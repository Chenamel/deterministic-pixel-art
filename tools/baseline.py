"""Verify curated, repository-local fixtures without accessing a source project."""
import hashlib
import json
from pathlib import Path


def verify_fixtures(baseline):
    baseline = Path(baseline)
    manifest = json.loads((baseline / 'manifest.json').read_text(encoding='utf-8'))
    actual = {p.relative_to(baseline).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
              for folder in ('snapshot', 'rendered')
              for p in sorted((baseline / folder).rglob('*')) if p.is_file()}
    return bool(actual) and actual == manifest['fixture_files']
