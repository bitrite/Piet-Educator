"""Bounded, isolated text extraction. Never execute documents or fetch their links."""
import io
import json
import posixpath
import re
import sys
import zipfile
from html.parser import HTMLParser
from xml.etree import ElementTree as ET

MAX_BYTES = 20 * 1024 * 1024
MAX_TEXT = 1000000


def xml(data):
    if re.search(br"<!\s*(DOCTYPE|ENTITY)", data, re.I):
        raise ValueError("XML document declarations and entities are not supported.")
    return ET.fromstring(data)


def archive(raw):
    book = zipfile.ZipFile(io.BytesIO(raw))
    infos = book.infolist()
    if len(infos) > 2000 or sum(x.file_size for x in infos) > 60 * 1024 * 1024:
        raise ValueError("This document expands beyond the import limit.")
    if any(x.flag_bits & 1 or x.file_size > 10 * 1024 * 1024 for x in infos):
        raise ValueError("Encrypted or oversized document sections are not supported.")
    return book


class TextHTML(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "svg"):
            self.skip += 1
        if not self.skip and tag in ("p", "div", "br", "li", "h1", "h2", "h3", "section"):
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style", "svg"):
            self.skip = max(0, self.skip - 1)
        if not self.skip and tag in ("p", "div", "li", "h1", "h2", "h3", "section"):
            self.parts.append("\n")

    def handle_data(self, text):
        if not self.skip:
            self.parts.append(text)


def extract(raw, suffix):
    if not raw or len(raw) > MAX_BYTES:
        raise ValueError("Choose a nonempty file of up to 20 MB.")
    sections, warnings = [], []
    if suffix in (".txt", ".md"):
        sections = [{"location": "Text section 1", "text": raw.decode("utf-8-sig")}]
    elif suffix == ".pdf":
        if not raw.startswith(b"%PDF-"):
            raise ValueError("This file is not a PDF.")
        try:
            from pypdf import PdfReader
        except ImportError:
            raise ValueError("PDF import needs pypdf. Install the library requirements first.")
        reader = PdfReader(io.BytesIO(raw))
        if reader.is_encrypted:
            raise ValueError("Password-protected PDFs are not supported. Use a permitted unlocked copy.")
        if len(reader.pages) > 500:
            raise ValueError("Import books of up to 500 pages, or split a longer book first.")
        for number, page in enumerate(reader.pages, 1):
            sections.append({"location": "PDF page " + str(number), "text": page.extract_text() or ""})
        warnings.append("PDF page numbers are file positions, which may differ from printed page numbers. Check diagrams, equations, columns and text order against the original.")
    elif suffix == ".docx":
        with archive(raw) as book:
            tree = xml(book.read("word/document.xml"))
            ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
            paragraphs = []
            for p in tree.findall(".//w:p", ns):
                paragraphs.append("".join(t.text or "" for t in p.findall(".//w:t", ns)))
            sections = [{"location": "Word document text", "text": "\n\n".join(paragraphs)}]
        warnings.append("Word pagination is not preserved. Check tables, equations and images against the original.")
    elif suffix == ".epub":
        with archive(raw) as book:
            if any(name.lower().endswith("encryption.xml") for name in book.namelist()):
                raise ValueError("This EPUB declares encrypted resources. Use a permitted unprotected copy.")
            root = xml(book.read("META-INF/container.xml"))
            rootfile = next((x.attrib.get("full-path") for x in root.iter() if x.tag.endswith("}rootfile")), None)
            if not rootfile:
                raise ValueError("This EPUB has no readable book structure.")
            package = xml(book.read(rootfile))
            manifest = {x.attrib.get("id"): x.attrib for x in package.iter() if x.tag.endswith("}item")}
            for entry in package.iter():
                if not entry.tag.endswith("}itemref"):
                    continue
                item = manifest.get(entry.attrib.get("idref"), {})
                if item.get("media-type") not in ("application/xhtml+xml", "text/html"):
                    continue
                from urllib.parse import unquote
                path = posixpath.normpath(posixpath.join(posixpath.dirname(rootfile), unquote(item.get("href", "").split("#")[0])))
                if path.startswith(("/", "../")) or ":" in path:
                    raise ValueError("This EPUB contains an unsupported resource path.")
                parser = TextHTML()
                parser.feed(book.read(path).decode("utf-8-sig"))
                sections.append({"location": "EPUB section " + str(len(sections) + 1) + " (" + posixpath.basename(path) + ")", "text": "".join(parser.parts)})
        warnings.append("EPUB references use reading-order sections, not printed pages. Images and diagrams need review.")
    else:
        raise ValueError("Use PDF, EPUB, DOCX, TXT or Markdown files.")
    if sum(len(x["text"]) for x in sections) > MAX_TEXT:
        raise ValueError("There is too much text for one import. Split the book into smaller parts.")
    empty = [x["location"] for x in sections if not x["text"].strip()]
    if empty:
        warnings.append("No text was found in " + ", ".join(empty[:12]) + (" and more" if len(empty) > 12 else "") + ". Scans need transcription or OCR; they have not been read automatically.")
    return {"sections": sections, "warnings": warnings}


if __name__ == "__main__":
    try:
        # Bound CPU even if a malformed document makes a parser work excessively.
        try:
            import resource
            resource.setrlimit(resource.RLIMIT_CPU, (20, 20))
            if sys.platform.startswith("linux"):
                resource.setrlimit(resource.RLIMIT_AS, (768 * 1024 * 1024,) * 2)
        except (ImportError, ValueError, OSError):
            pass
        result = extract(sys.stdin.buffer.read(MAX_BYTES + 1), sys.argv[1])
        print(json.dumps(result))
    except Exception as exc:
        message = str(exc) if isinstance(exc, (ValueError, UnicodeError)) else "The document could not be read. Check its format and try again."
        print(json.dumps({"error": message[:400]}))
        sys.exit(1)
