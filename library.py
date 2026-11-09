"""Persistent local material library; imported passages are drafts until owner review."""
import base64
import binascii
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from educator import AGE_BANDS, validate_catalog

MAX_FILE = 20 * 1024 * 1024
SUFFIXES = {".pdf", ".epub", ".docx", ".txt", ".md"}


def required(value, label, limit=200):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError(label + " is required (up to " + str(limit) + " characters).")
    return value.strip()


def split_text(text, limit=2400):
    text = text.replace("\x00", "").replace("\r\n", "\n").replace("\r", "\n").strip()
    while text:
        end = min(limit, len(text))
        if end < len(text):
            end = max(text.rfind("\n", 0, end), text.rfind(" ", 0, end), end // 2)
        yield text[:end].strip()
        text = text[end:].strip()


class Library:
    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.blobs = self.root / "originals"
        self.blobs.mkdir(exist_ok=True, mode=0o700)
        self.database = self.root / "library.sqlite3"
        with self.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS materials (
                    id TEXT PRIMARY KEY, metadata TEXT NOT NULL, filename TEXT NOT NULL,
                    digest TEXT NOT NULL UNIQUE, suffix TEXT NOT NULL, warnings TEXT NOT NULL,
                    created TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS passages (
                    id TEXT PRIMARY KEY, material_id TEXT NOT NULL REFERENCES materials(id),
                    location TEXT NOT NULL, original_text TEXT NOT NULL, text TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'draft', age_bands TEXT NOT NULL DEFAULT '[]',
                    reviewed_by TEXT NOT NULL DEFAULT '', reviewed_on TEXT NOT NULL DEFAULT '',
                    revision INTEGER NOT NULL DEFAULT 1);
                CREATE TABLE IF NOT EXISTS reviews (
                    id INTEGER PRIMARY KEY, passage_id TEXT NOT NULL, event TEXT NOT NULL,
                    reviewer TEXT NOT NULL, created TEXT NOT NULL, snapshot TEXT NOT NULL);
            """)
        os.chmod(self.database, 0o600)

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(str(self.database), timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def import_file(self, request):
        if not isinstance(request, dict) or set(request) != {"filename", "content", "metadata"}:
            raise ValueError("Choose a file and complete its learning details.")
        filename = required(request["filename"], "File name", 240)
        suffix = Path(filename).suffix.lower()
        if suffix not in SUFFIXES:
            raise ValueError("Use PDF, EPUB, DOCX, TXT or Markdown files.")
        metadata = request["metadata"]
        fields = {"title", "provider", "framework", "grade", "subject", "language", "edition", "permission"}
        if not isinstance(metadata, dict) or set(metadata) != fields or metadata.get("permission") is not True:
            raise ValueError("Complete the book details and confirm permission to use it.")
        metadata = {key: required(metadata[key], key.capitalize()) for key in fields - {"permission"}}
        metadata["permission"] = True
        if not isinstance(request["content"], str) or len(request["content"]) > (MAX_FILE + 2) // 3 * 4:
            raise ValueError("Choose a file of up to 20 MB.")
        try:
            raw = base64.b64decode(request["content"], validate=True)
        except (binascii.Error, ValueError):
            raise ValueError("The file upload was incomplete. Please try again.")
        if not raw or len(raw) > MAX_FILE:
            raise ValueError("Choose a nonempty file of up to 20 MB.")
        digest = hashlib.sha256(raw).hexdigest()
        with self.connect() as db:
            existing = db.execute("SELECT id FROM materials WHERE digest=?", (digest,)).fetchone()
        if existing:
            raise ValueError("This exact file is already in the library.")
        try:
            process = subprocess.run([sys.executable, str(Path(__file__).with_name("extract_material.py")), suffix],
                input=raw, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, timeout=30)
            extraction = json.loads(process.stdout)
        except (subprocess.TimeoutExpired, ValueError):
            raise ValueError("Extraction could not finish within the import limits. Try a smaller section.")
        if process.returncode or "error" in extraction:
            raise ValueError(extraction.get("error", "This document could not be read."))
        material_id = uuid.uuid4().hex
        original = self.blobs / (material_id + suffix)
        # Generated storage name; a supplied file name never becomes a filesystem path.
        with original.open("xb") as stream:
            os.chmod(original, 0o600)
            stream.write(raw)
        now = datetime.now(timezone.utc).isoformat()
        try:
            with self.connect() as db:
                db.execute("INSERT INTO materials VALUES (?,?,?,?,?,?,?)", (material_id, json.dumps(metadata),
                    Path(filename.replace("\\", "/")).name, digest, suffix, json.dumps(extraction["warnings"]), now))
                for section in extraction["sections"]:
                    for index, text in enumerate(split_text(section["text"]), 1):
                        if not text:
                            continue
                        location = section["location"] + " · passage " + str(index)
                        db.execute("INSERT INTO passages (id,material_id,location,original_text,text) VALUES (?,?,?,?,?)",
                            (uuid.uuid4().hex, material_id, location, text, text))
        except Exception:
            original.unlink(missing_ok=True)  # Roll back only this failed import's generated copy.
            raise
        return self.detail(material_id)

    def list(self):
        with self.connect() as db:
            rows = db.execute("""SELECT m.*, COUNT(p.id) AS total,
                SUM(CASE WHEN p.status='approved' THEN 1 ELSE 0 END) AS approved
                FROM materials m LEFT JOIN passages p ON p.material_id=m.id
                GROUP BY m.id ORDER BY m.created DESC""").fetchall()
        return [{"id": x["id"], "metadata": json.loads(x["metadata"]), "filename": x["filename"],
                 "total": x["total"], "approved": x["approved"] or 0,
                 "warnings": json.loads(x["warnings"])} for x in rows]

    def detail(self, material_id):
        with self.connect() as db:
            row = db.execute("SELECT * FROM materials WHERE id=?", (material_id,)).fetchone()
            if not row:
                raise ValueError("Material not found.")
            passages = db.execute("SELECT * FROM passages WHERE material_id=? ORDER BY rowid", (material_id,)).fetchall()
        return {"id": row["id"], "metadata": json.loads(row["metadata"]), "filename": row["filename"],
                "warnings": json.loads(row["warnings"]), "passages": [dict(x, age_bands=json.loads(x["age_bands"])) for x in passages]}

    def add_passage(self, material_id, request):
        if not isinstance(request, dict) or set(request) != {"text", "location"}:
            raise ValueError("Enter passage text and its source location.")
        text = required(request["text"], "Passage", 6000)
        location = required(request["location"], "Source location")
        with self.connect() as db:
            if not db.execute("SELECT id FROM materials WHERE id=?", (material_id,)).fetchone():
                raise ValueError("Material not found.")
            db.execute("INSERT INTO passages (id,material_id,location,original_text,text) VALUES (?,?,?,?,?)",
                       (uuid.uuid4().hex, material_id, location, "", text))
        return self.detail(material_id)

    def original(self, material_id):
        with self.connect() as db:
            row = db.execute("SELECT suffix FROM materials WHERE id=?", (material_id,)).fetchone()
        if not row or not all(x in "0123456789abcdef" for x in material_id) or len(material_id) != 32:
            raise ValueError("Material not found.")
        return (self.blobs / (material_id + row["suffix"])).read_bytes()

    def review(self, passage_id, request):
        fields = {"text", "age_bands", "reviewed_by", "status", "revision", "confirmed"}
        if not isinstance(request, dict) or set(request) != fields:
            raise ValueError("Complete the passage review.")
        text = required(request["text"], "Passage", 6000)
        reviewer = required(request["reviewed_by"], "Reviewer name", 100)
        bands = request["age_bands"]
        status = request["status"]
        if not isinstance(bands, list) or any(not isinstance(x, str) or x not in AGE_BANDS for x in bands):
            raise ValueError("Choose valid age groups.")
        if status not in ("approved", "draft") or (status == "approved" and not bands):
            raise ValueError("Approved passages need at least one suitable age group.")
        if status == "approved" and request["confirmed"] is not True:
            raise ValueError("Confirm that you checked the original and age suitability before approval.")
        now = datetime.now(timezone.utc).isoformat()
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM passages WHERE id=?", (passage_id,)).fetchone()
            if not row:
                raise ValueError("Passage not found.")
            if type(request["revision"]) is not int or request["revision"] != row["revision"]:
                raise ValueError("This passage changed in another window. Reopen it before reviewing.")
            # One transaction publishes exactly the version, ages and text the owner reviewed.
            db.execute("UPDATE passages SET text=?,status=?,age_bands=?,reviewed_by=?,reviewed_on=?,revision=revision+1 WHERE id=?",
                (text, status, json.dumps(sorted(set(bands))), reviewer, now, passage_id))
            db.execute("INSERT INTO reviews (passage_id,event,reviewer,created,snapshot) VALUES (?,?,?,?,?)",
                       (passage_id, status, reviewer, now, json.dumps(request)))
            material_id = row["material_id"]
        return self.detail(material_id)

    def lessons(self, band):
        with self.connect() as db:
            rows = db.execute("""SELECT p.*,m.metadata FROM passages p JOIN materials m ON m.id=p.material_id
                WHERE p.status='approved' ORDER BY m.created,p.rowid""").fetchall()
        lessons = []
        for row in rows:
            bands = json.loads(row["age_bands"])
            if band not in bands:
                continue
            meta = json.loads(row["metadata"])
            lessons.append({"id": "library-" + row["id"], "material_id": row["material_id"],
                "title": meta["title"] + " · " + row["location"], "text": row["text"],
                "source": meta["title"] + " · " + meta["edition"] + " · " + row["location"],
                "metadata": meta, "status": "approved", "age_bands": bands,
                "reviewed_by": row["reviewed_by"], "reviewed_on": row["reviewed_on"]})
        return validate_catalog(lessons) if lessons else []
