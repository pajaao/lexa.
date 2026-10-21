"""Directed, offline quarantine of the reviewed numbering run; no legal equivalence inference."""
import argparse
import hashlib
import json
from pathlib import Path
from extract_previous_html import ROOT, FILES
from prepare_previous_only import previous_blocks

BASE = ROOT/'experiments/html-history/source-refresh/20261021T175224964205Z'
RUN = ROOT/'experiments/html-history/association-review/20261021'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def evaluate():
    old = read(BASE/'results.json')['additions']
    reader = read(BASE/'reader-ids.json')
    recovered = {}
    source_reports = {}
    for code in ['penal', 'cpp', 'clt', 'licitacoes']:
        result = previous_blocks(code, FILES[code], (BASE/'incoming'/FILES[code]).read_bytes(), set(reader[code]))
        recovered.update({r['id']: r for r in result['records']})
        source_reports[code] = result['source']
    decisions, kept, quarantine = [], [], []
    for row in old:
        match = recovered.get(row['id'])
        # An equal number or equal text in another occurrence is never a match.
        exact = bool(match and all(match[k] == row[k] for k in ['codeId', 'articleId', 'text', 'notes', 'source', 'evidence']))
        decision = dict(id=row['id'], codeId=row['codeId'], articleId=row['articleId'],
                        outcome='retained' if exact else 'quarantined',
                        reason='same_documentary_occurrence' if exact else 'original_general_part_identity_not_established')
        decisions.append(decision)
        (kept if exact else quarantine).append(row)
    existing = read(BASE/'existing.json')
    notes = []
    for comparison in read(BASE/'results.json')['comparisons']:
        if not comparison['notesDiffer']:
            continue
        row = next(r for r in existing if r['id'] == comparison['id'])
        # Compare body for diagnosis only; preserve the original record and notes.
        from extract_previous_html import canonical
        matches = [r for r in recovered.values() if r['codeId']==row['codeId'] and r['articleId']==row['articleId'] and canonical(r['text'])==canonical(row['text'])]
        notes.append(dict(id=row['id'], originalNotes=row['notes'], originalSource=row['source'],
                          candidateOccurrences=[dict(id=r['id'],notes=r['notes'],source=r['source']) for r in matches],
                          differenceRemains=bool(matches and all(r['notes']!=row['notes'] for r in matches)),
                          originalRecordChanged=False))
    return dict(decisions=decisions, retained=kept, quarantined=quarantine,
                notes=notes, sourceReports=source_reports, publicationAllowed=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true')
    args=parser.parse_args()
    result=evaluate()
    fixture=ROOT/'tests/fixtures/previous-wordings-html.json'
    previous=read(BASE/'previous-fixture-before.json')
    expected=dict(previous, records=previous['records']+result['retained'])
    if args.verify:
        assert result==read(RUN/'results.json'), 'Directed replay differs'
        assert read(fixture)==expected, 'Preview fixture differs'
        for name, digest in read(RUN/'manifest.json')['files'].items():
            assert hashlib.sha256((RUN/name).read_bytes()).hexdigest()==digest, name
        print('Association replay, fixture and evidence hashes verified.')
        return
    if RUN.exists():
        raise ValueError('Existing review evidence must not be overwritten')
    before=read(fixture)
    prior=dict(previous, records=previous['records']+read(BASE/'results.json')['additions'])
    assert before==prior, 'Unexpected local fixture; no write permitted'
    write(RUN/'fixture-before.json', before)
    write(RUN/'results.json', result)
    write(fixture, expected)
    write(RUN/'manifest.json', dict(baseRun=BASE.relative_to(ROOT).as_posix(),
          publicationAllowed=False, retained=len(result['retained']), quarantined=len(result['quarantined']),
          files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in RUN.glob('*.json')}))
    print(json.dumps(dict(retained=len(result['retained']), quarantined=len(result['quarantined']),
                          remainingNoteDifferences=sum(n['differenceRemains'] for n in result['notes']))))


if __name__=='__main__':
    main()
