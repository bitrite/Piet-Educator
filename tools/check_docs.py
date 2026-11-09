"""Check local Markdown file/image destinations without reading private data folders."""
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit


def check(root):
    root = Path(root).resolve()
    documents = sorted(root.glob('*.md')) + sorted((root / 'docs').rglob('*.md'))
    failures = []
    count = 0
    for document in documents:
        for target in re.findall(r'!?\[[^\]\n]*\]\(([^)\n]+)\)', document.read_text(encoding='utf-8')):
            target = target.strip().strip('<>')
            parsed = urlsplit(target)
            if parsed.scheme in ('http', 'https', 'mailto') or not parsed.path:
                continue
            count += 1
            path = (document.parent / unquote(parsed.path)).resolve()
            try:
                path.relative_to(root)
            except ValueError:
                failures.append(str(document.relative_to(root)) + ': destination leaves repository: ' + target)
                continue
            if parsed.scheme or not path.exists():
                failures.append(str(document.relative_to(root)) + ': missing/invalid destination: ' + target)
    return documents, count, failures


if __name__ == '__main__':
    documents, count, failures = check(Path(__file__).resolve().parents[1])
    for failure in failures:
        print(failure)
    print(str(len(documents)) + ' Markdown documents; ' + str(count) + ' local links checked; ' + str(len(failures)) + ' failures.')
    raise SystemExit(1 if failures else 0)
