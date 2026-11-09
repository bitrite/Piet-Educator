"""Single-profile loopback prototype with a separate owner-controlled material library."""
import argparse
import json
import os
import re
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from educator import AGE_BANDS, Educator, Ollama
from library import Library

ROOT = Path(__file__).resolve().parent


def make_server(band="6-9", port=8767, model="qwen3:8b", judge_model=None, service=None, data_dir=None, owner_key=None):
    catalog = json.loads((ROOT / "lessons.json").read_text())
    service = service or Educator(catalog, band, Ollama(model), Ollama(judge_model or model))
    library = Library(data_dir or ROOT / "data")
    service.library = library
    if owner_key is None:
        keyfile = library.root / "owner-key"
        if not keyfile.exists():
            with keyfile.open("x") as output:
                os.chmod(keyfile, 0o600)
                output.write(secrets.token_urlsafe(24))
        os.chmod(keyfile, 0o600)
        owner_key = keyfile.read_text().strip()
        if len(owner_key) < 20:
            raise ValueError("The library owner key is invalid.")
    token = secrets.token_urlsafe(32)
    busy = threading.BoundedSemaphore(1)
    importing = threading.BoundedSemaphore(1)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def trusted(self):
            host = self.headers.get("Host", "")
            expected = {"127.0.0.1:" + str(self.server.server_port), "localhost:" + str(self.server.server_port)}
            origin = self.headers.get("Origin")
            return host in expected and (origin is None or origin == "http://" + host)

        def owner(self):
            return secrets.compare_digest(self.headers.get("X-Piet-Owner", ""), owner_key)

        def send(self, code, body, mime="application/json; charset=utf-8"):
            raw = json.dumps(body).encode() if isinstance(body, dict) else body
            self.send_response(code)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self):
            if not self.trusted():
                return self.send(403, {"error": "Open Piet from its local address."})
            if self.path == "/api/session":
                return self.send(200, {"token": token, "age_band": service.band,
                    "age_label": AGE_BANDS[service.band][0], "lessons": service.available_lessons(),
                    "model": model, "prototype": True})
            if self.path.startswith("/api/library"):
                if not self.owner():
                    return self.send(403, {"error": "Unlock the library with the owner's access code."})
                try:
                    if self.path == "/api/library":
                        return self.send(200, {"materials": library.list()})
                    match = re.fullmatch(r"/api/library/([a-f0-9]{32})(/original)?", self.path)
                    if match:
                        if match[2]:
                            return self.send(200, library.original(match[1]), "application/octet-stream")
                        return self.send(200, library.detail(match[1]))
                except ValueError as exc:
                    return self.send(404, {"error": str(exc)})
                return self.send(404, {"error": "Material not found."})
            files = {"/": ("index.html", "text/html; charset=utf-8"),
                     "/app.js": ("app.js", "text/javascript; charset=utf-8"),
                     "/style.css": ("style.css", "text/css; charset=utf-8"),
                     "/library": ("library.html", "text/html; charset=utf-8"),
                     "/library.js": ("library.js", "text/javascript; charset=utf-8")}
            if self.path not in files:
                return self.send(404, {"error": "Page not found"})
            name, mime = files[self.path]
            self.send(200, (ROOT / "web" / name).read_bytes(), mime)

        def do_POST(self):
            is_library = self.path.startswith("/api/library")
            authorized = self.owner() if is_library else secrets.compare_digest(self.headers.get("X-Piet-Token", ""), token)
            if not self.trusted() or not authorized:
                return self.send(403, {"error": "Unlock the owner library or refresh the local learning page."})
            if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                return self.send(415, {"error": "A JSON request is required."})
            if self.headers.get("Transfer-Encoding"):
                return self.send(400, {"error": "This upload method is not supported."})
            try:
                size = int(self.headers.get("Content-Length", "0"))
                limit = 29 * 1024 * 1024 if self.path == "/api/library/import" else 40000 if is_library else 16000
                if size < 1 or size > limit:
                    return self.send(413, {"error": "That request is too large or empty."})
                self.connection.settimeout(20)
                data = json.loads(self.rfile.read(size))
                if self.path == "/api/library/import":
                    if not importing.acquire(blocking=False):
                        return self.send(429, {"error": "Another import is in progress. Please try again shortly."})
                    try:
                        return self.send(201, library.import_file(data))
                    finally:
                        importing.release()
                match = re.fullmatch(r"/api/library/([a-f0-9]{32})/passages", self.path)
                if match:
                    return self.send(201, library.add_passage(match[1], data))
                match = re.fullmatch(r"/api/library/passages/([a-f0-9]{32})/review", self.path)
                if match:
                    return self.send(200, library.review(match[1], data))
                if self.path != "/api/explain":
                    return self.send(404, {"error": "Action not found"})
                if not busy.acquire(blocking=False):
                    return self.send(429, {"error": "Piet is finishing another explanation. Try again shortly."})
                try:
                    result = service.explain(data)
                finally:
                    busy.release()
                self.send(200, result)
            except (ValueError, TypeError, TimeoutError) as exc:
                self.send(400, {"error": str(exc)[:400] if is_library else "Check the lesson, explanation method and question length."})
            except Exception:
                self.send(503, {"error": "The local service could not finish. Please try again."})

    server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    server.daemon_threads = True
    server.owner_key = owner_key
    server.library = library
    return server


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Piet Educator local prototype")
    parser.add_argument("--age-band", choices=AGE_BANDS, default="6-9")
    parser.add_argument("--port", type=int, default=8767)
    parser.add_argument("--model", default="qwen3:8b")
    parser.add_argument("--judge-model", default=None)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    args = parser.parse_args()
    server = make_server(args.age_band, args.port, args.model, args.judge_model, data_dir=args.data_dir)
    print("Piet Educator prototype: http://127.0.0.1:" + str(server.server_port), flush=True)
    print("Age setting: " + args.age_band + ". Change this only through the owner-controlled launch.", flush=True)
    print("Owner library: http://127.0.0.1:" + str(server.server_port) + "/library", flush=True)
    print("Library access code (keep with the device owner): " + server.owner_key, flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
