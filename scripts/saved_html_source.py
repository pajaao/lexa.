"""Resolve an exact saved source edition, never substitute newer bytes silently."""
import hashlib
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]


def source_path(document, sha256, root=ROOT):
    if Path(document).name!=document or not re.fullmatch(r'[0-9a-f]{64}',sha256):
        raise ValueError('Invalid source identity')
    for path in [root/'HTML'/document,
                 root/'experiments/html-history/source-archives'/sha256/document]:
        if path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest()==sha256:
            return path
    raise ValueError(f'Saved source edition missing or changed: {document} ({sha256})')
