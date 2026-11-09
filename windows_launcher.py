"""Windows desktop entry point. Reuses the same server and age enforcement."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import urllib.request
import webbrowser
from educator import AGE_BANDS, Ollama
from server import make_server

PORT = 8767


def load_settings(home):
    try:
        config = json.loads((Path(home) / "settings.json").read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        raise ValueError("Run Install-Windows.cmd first to set up this learning space.")
    if not isinstance(config, dict) or config.get("schema_version") != 1 or config.get("age_band") not in AGE_BANDS:
        raise ValueError("The age setting is invalid. Run the installer again; no adult fallback was selected.")
    return config


def read_local_json(url, timeout=2):
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            raise OSError("Unexpected local service redirect")
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    with opener.open(url, timeout=timeout) as response:
        raw = response.read(3000000)
    return json.loads(raw)


def ensure_ollama():
    try:
        if isinstance(read_local_json("http://127.0.0.1:11434/api/tags").get("models"), list):
            return
    except (OSError, ValueError, AttributeError):
        pass
    candidate = shutil.which("ollama")
    if not candidate and os.environ.get("LOCALAPPDATA"):
        known = Path(os.environ["LOCALAPPDATA"]) / "Programs" / "Ollama" / "ollama.exe"
        if known.is_file():
            candidate = str(known)
    if not candidate:
        raise ValueError("Ollama was not found. Run Install-Windows.cmd again.")
    environment = dict(os.environ, OLLAMA_HOST="127.0.0.1:11434", OLLAMA_NO_CLOUD="1")
    subprocess.Popen([candidate, "serve"], env=environment, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    for _ in range(60):
        try:
            if isinstance(read_local_json("http://127.0.0.1:11434/api/tags").get("models"), list):
                return
        except (OSError, ValueError, AttributeError):
            pass
        time.sleep(0.5)
    raise ValueError("Ollama did not start. Open Ollama from the Start menu, then try again.")


def matches_learning_space(session, band, data_dir):
    return (isinstance(session, dict) and session.get("application") == "piet-educator"
            and session.get("age_band") == band
            and session.get("instance_id") == hashlib.sha256(str(Path(data_dir).resolve()).casefold().encode()).hexdigest()[:16])


def main(argv=None):
    parser = argparse.ArgumentParser(description="Start the installed Piet Educator")
    parser.add_argument("--home", type=Path,
                        default=Path(os.environ.get("LOCALAPPDATA", Path.home())) / "PietEducator")
    parser.add_argument("--page", choices=("reader", "library"), default="reader")
    parser.add_argument("--diagnostics", action="store_true")
    args = parser.parse_args(argv)
    config = load_settings(args.home)
    data_dir = args.home / "data"
    if importlib.util.find_spec("pypdf") is None:
        raise ValueError("PDF support is missing. Run Install-Windows.cmd again.")
    ensure_ollama()
    for name in ("qwen3:8b", "piet-educator"):
        Ollama(name).verify_local()
    if args.diagnostics:
        print("Local models, PDF import and age settings are ready.")
        return 0
    url = "http://127.0.0.1:" + str(PORT) + ("/library" if args.page == "library" else "/")
    try:
        server = make_server(config["age_band"], PORT, "piet-educator", "qwen3:8b", data_dir=data_dir)
    except OSError:
        try:
            session = read_local_json("http://127.0.0.1:" + str(PORT) + "/api/session")
        except (OSError, ValueError):
            raise ValueError("Another application is using Piet's local address. Close it and try again.")
        if not matches_learning_space(session, config["age_band"], data_dir):
            raise ValueError("Another learning space is running. Close its Piet window before changing age settings or data folders.")
        webbrowser.open(url)
        print("Opened your existing Piet Educator window.")
        return 0
    print("Piet Educator - " + AGE_BANDS[config["age_band"]][0])
    print("Keep this window open while using Piet. Close it to stop the learning server.")
    print("The owner library code is in your private PietEducator data folder (owner-key).")
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print("Piet could not start: " + str(exc))
        raise SystemExit(1)
