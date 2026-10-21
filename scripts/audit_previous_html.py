"""Read-only coverage ledger for every struck block detected in saved HTML.

Does not create legal history records or infer that a saved source is complete.
Unassociated blocks remain evidence awaiting triage, never approved content.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from extract_previous_html import ROOT, FILES, EvidenceHTML, decode, prepare_document


def coverage(code, filename, raw, result):
    source, encoding = decode(raw)
    parser = EvidenceHTML(source)
    parser.feed(source)
    parser.close()
    parser.flush()
    decisions = {}

    def mark(block, disposition, identity=None, reasons=()):
        decisions.setdefault(block, []).append(dict(disposition=disposition,
            recordId=identity, reasons=list(reasons)))

    for row in result['records']:
        # charRange is more reliable than parsing a human-readable location.
        for index, block in enumerate(parser.blocks):
            if [block['start'], block['end']] == row['evidence']['charRange']:
                mark(index, 'prepared', row['id'])
    for row in result['duplicateEvidence']:
        mark(row['block'], 'duplicate_evidence')
    for row in result['excluded']:
        for block in row.get('blocks', []):
            mark(block, 'excluded', reasons=row.get('reasons', []))

    digest = hashlib.sha256(raw).hexdigest()
    entries = []
    for index, block in enumerate(parser.blocks):
        # Include ordinal-only, partial and unrecognized blocks too.
        if not any(r['deleted'] and r['text'].strip() for r in block['runs']):
            continue
        outcomes = decisions.get(index, [dict(disposition='unassociated',
            recordId=None, reasons=['no_prepared_or_excluded_unit_for_this_block'])])
        entries.append(dict(id=f'{code}-{digest[:12]}-block-{index}',
            codeId=code, sourceFile=filename, sourceSha256=digest,
            encoding=encoding, block=index, line=block['line'],
            charRange=[block['start'], block['end']], rawHtml=block['rawHtml'],
            rawText=''.join(r['text'] for r in block['runs']), runs=block['runs'],
            anchors=block['anchors'], decisions=outcomes))
    return dict(codeId=code, file=filename, sha256=digest,
        detectedStruckBlocks=len(entries),
        blocksByDisposition=dict(Counter(d for e in entries for d in
            {x['disposition'] for x in e['decisions']})), entries=entries)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path,
        default=ROOT/'experiments/html-history/safeguards/coverage.json')
    args = parser.parse_args()
    if not args.output.resolve().is_relative_to(ROOT/'experiments/html-history'):
        raise ValueError('Coverage output must stay experimental')
    existing = json.loads((ROOT/'experiments/html-history/existing-records.json').read_text(encoding='utf-8'))
    reader = json.loads((ROOT/'experiments/html-history/reader-ids.json').read_text(encoding='utf-8'))
    sources = []
    for code, filename in FILES.items():
        path = ROOT/'HTML'/filename
        raw = path.read_bytes()
        result = prepare_document(code, filename, raw, existing, set(reader[code]))
        sources.append(coverage(code, filename, raw, result))
        if path.read_bytes() != raw:
            raise ValueError('Source changed during coverage audit')
    output = dict(schemaVersion=1, publicationAllowed=False,
        scope='All struck blocks detected by the existing HTML parser; not all legislative history',
        limitations=['No recovery of absent source text',
            'External CSS and unsupported markup are not a completeness guarantee',
            'A tracked block may contain other units; no claim of complete normative-unit coverage',
            'Unassociated blocks may be editorial, ordinal-only, mixed or outside reader scope'],
        sources=sources)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps([dict(codeId=s['codeId'], blocks=s['detectedStruckBlocks'],
        dispositions=s['blocksByDisposition']) for s in sources], ensure_ascii=False))


if __name__ == '__main__':
    main()
