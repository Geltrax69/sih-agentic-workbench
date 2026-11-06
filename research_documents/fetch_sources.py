"""Verify retained originals and download missing PDFs without changing recorded provenance."""
from pathlib import Path
import hashlib
import io
import json
import urllib.request
from pypdf import PdfReader

root = Path(__file__).resolve().parent
failures = []
for source in json.loads((root / 'source_register.json').read_text()):
    target = root / source['file']
    try:
        data = target.read_bytes() if target.exists() else urllib.request.urlopen(
            urllib.request.Request(source['pdf_url'], headers={'User-Agent': 'Mozilla/5.0'}), timeout=60
        ).read()
        if not data.startswith(b'%PDF'):
            raise ValueError('The response is not a PDF')
        if hashlib.sha256(data).hexdigest() != source['sha256']:
            raise ValueError('Content differs from the recorded version; inspect before updating provenance')
        if len(PdfReader(io.BytesIO(data)).pages) != source['pages']:
            raise ValueError('Page count differs from the register')
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        print(source['id'], 'verified', source['file'])
    except Exception as exc:
        failures.append(source['id'])
        print(source['id'], 'FAILED:', exc)
if failures:
    raise SystemExit('Unverified sources: ' + ', '.join(failures))
