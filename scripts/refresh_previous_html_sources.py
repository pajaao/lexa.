"""Refresh only CF/CPP/CPC local sources, preserving old editions and records."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

from extract_previous_html import ROOT, FILES, canonical, decode
from prepare_previous_only import previous_blocks

INPUTS={'cf':'Constituição.html','cpp':'Del3689.html','cpc':'L13105.html'}


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path, value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def archive(path, document):
    target=ROOT/'experiments/html-history/source-archives'/digest(path)/document
    target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists():
        if target.read_bytes()!=path.read_bytes():
            raise ValueError('Archive identity conflict')
    else:
        shutil.copy2(path,target)
    return target


def key(row):
    return row['codeId'],row['articleId'],canonical(row['text'])


def process(incoming, existing, reader, documented_restarts=True):
    additions, exclusions, comparisons, summary=[],[],[],[]
    seen={key(r) for r in existing if r.get('wording',{}).get('status')=='previous'}
    for code,name in INPUTS.items():
        raw=(incoming/name).read_bytes()
        text,encoding=decode(raw)
        result=previous_blocks(code,FILES[code],raw,set(reader[code]),documented_restarts=documented_restarts)
        required={'cf':{'250','adct-138'},'cpp':{'811'},'cpc':{'1072'}}[code]
        if not required.issubset(result['source']['articleIds']) or '</html>' not in text[-2000:].lower():
            raise ValueError(f'Missing end-of-document evidence: {code}')
        found={key(r):r for r in result['records']}
        old=[r for r in existing if r['codeId']==code and r.get('wording',{}).get('status')=='previous']
        for row in old:
            match=found.get(key(row))
            comparisons.append(dict(codeId=code,id=row['id'],articleId=row['articleId'],
                outcome='same_normative_text' if match else 'not_recovered_by_current_rules',
                notesDiffer=bool(match and row['notes']!=match['notes'])))
        added=[]
        for row in result['records']:
            if key(row) not in seen:
                seen.add(key(row))
                row['source']['receivedFilename']=name
                additions.append(row)
                added.append(row)
        exclusions.extend(result['excluded'])
        summary.append(dict(codeId=code,receivedFilename=name,activeFilename=FILES[code],
            sha256=hashlib.sha256(raw).hexdigest(),encoding=encoding,
            origin=result['source']['origin'],endMarkersVerified=sorted(required),
            existingPreviousRecords=len(old),sameNormativeText=sum(key(r) in found for r in old),
            newRecords=len(added),excludedBlocks=len(result['excluded']),
            excludedReasons=dict(Counter(reason for e in result['excluded'] for reason in e['reasons']))))
    return dict(additions=additions,excluded=exclusions,comparisons=comparisons,summary=summary)


def reprocess(sources, existing, reader, codes, allow_unmapped_general_part=False):
    """Compare legacy and corrected layout handling; append only new safe text."""
    additions, exclusions, comparisons, summary = [], [], [], []
    seen={key(r) for r in existing if r.get('wording',{}).get('status')=='previous'}
    for code in codes:
        name=FILES[code]
        raw=(sources/name).read_bytes()
        before=previous_blocks(code,name,raw,set(reader[code]),documented_restarts=False)
        after=previous_blocks(code,name,raw,set(reader[code]),documented_restarts=True, allow_unmapped_general_part=allow_unmapped_general_part)
        old_found={key(r):r for r in before['records']}
        found={key(r):r for r in after['records']}
        old=[r for r in existing if r['codeId']==code and r.get('wording',{}).get('status')=='previous']
        lost=[r['id'] for r in old if key(r) in old_found and key(r) not in found]
        if lost:
            raise ValueError(f'Unexpected loss of previously recognized records: {lost}')
        added=[]
        for row in after['records']:
            if key(row) not in seen:
                additions.append(row)
                added.append(row)
                seen.add(key(row))
        for row in old:
            comparisons.append(dict(codeId=code,id=row['id'],
                recognizedBefore=key(row) in old_found,recognizedAfter=key(row) in found,
                notesDiffer=bool(key(row) in found and row['notes']!=found[key(row)]['notes'])))
        exclusions.extend(after['excluded'])
        summary.append(dict(codeId=code,file=name,sourceSha256=after['source']['sha256'],
            existingPreviousRecords=len(old),recognizedBefore=sum(key(r) in old_found for r in old),
            recognizedAfter=sum(key(r) in found for r in old),
            preparedBefore=len(before['records']),preparedAfter=len(after['records']),
            newRecords=len(added),excludedBefore=len(before['excluded']),excludedAfter=len(after['excluded']),
            excludedReasons=dict(Counter(reason for e in after['excluded'] for reason in e['reasons'])),
            numberingTransitions=after['source']['numberingTransitions']))
    return dict(additions=additions,excluded=exclusions,comparisons=comparisons,summary=summary)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--input-dir',type=Path)
    mode.add_argument('--verify',type=Path,help='Reproduce a preserved run without changing sources or fixtures')
    mode.add_argument('--reprocess',action='store_true',help='Reprocess only selected active sources with corrected document-region handling')
    parser.add_argument('--codes',nargs='+',choices=list(FILES))
    args=parser.parse_args()
    if bool(args.codes)!=bool(args.reprocess):
        parser.error('--codes must be provided only with --reprocess')
    if args.verify:
        run=args.verify.resolve()
        manifest=read(run/'manifest.json')
        if manifest.get('runKind')=='numbering_reprocess':
            result=reprocess(run/'incoming',read(run/'existing.json'),read(run/'reader-ids.json'),manifest['codes'],allow_unmapped_general_part=manifest.get('allowUnmappedGeneralPart',True))
        else:
            result=process(run/'incoming',read(run/'existing.json'),read(run/'reader-ids.json'),documented_restarts=manifest.get('documentedRestarts',False))
        if result!=read(run/'results.json'):
            raise ValueError('Offline reproduction differs from preserved results')
        manifest=read(run/'manifest.json')
        for name,expected in manifest['files'].items():
            if digest(run/name)!=expected:
                raise ValueError(f'Run file changed: {name}')
        print('Offline reproduction and run hashes verified.')
        return
    fixture=ROOT/'tests/fixtures/previous-wordings-html.json'
    previous_fixture=read(fixture)
    existing=read(ROOT/'experiments/html-history/existing-records.json')
    existing+=read(ROOT/'tests/fixtures/legislative-history-html.json')['records']
    existing+=previous_fixture['records']
    reader=read(ROOT/'experiments/html-history/reader-ids.json')
    if args.reprocess:
        codes=list(dict.fromkeys(args.codes))
        before={name:digest(ROOT/'HTML'/name) for name in FILES.values()}
        result=reprocess(ROOT/'HTML',existing,reader,codes)
        if any(digest(ROOT/'HTML'/name)!=value for name,value in before.items()):
            raise ValueError('A source changed during reprocessing; fixture not changed')
        run=ROOT/'experiments/html-history/source-refresh'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        run.mkdir(parents=True,exist_ok=False)
        write(run/'existing.json',existing)
        write(run/'reader-ids.json',reader)
        write(run/'previous-fixture-before.json',previous_fixture)
        write(run/'results.json',result)
        for code in codes:
            dest=run/'incoming'/FILES[code]
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(ROOT/'HTML'/FILES[code],dest)
        records=previous_fixture['records']+result['additions']
        if len({r['id'] for r in [*existing,*result['additions']]})!=len(existing)+len(result['additions']):
            raise ValueError('Duplicate record ID; fixture not changed')
        if any(r['review']!={'status':'pending'} or r['wording']['status']!='previous' for r in result['additions']):
            raise ValueError('Invalid new-record state; fixture not changed')
        write(fixture,dict(previous_fixture,records=records))
        write(run/'manifest.json',dict(runKind='numbering_reprocess',codes=codes,
            documentedRestarts=True,allowUnmappedGeneralPart=False,publicationAllowed=False,sourcesBefore=before,sourcesAfter=before,
            existingRecordCount=len(existing),newRecordCount=len(result['additions']),
            fixtureAfterSha256=digest(fixture),
            scripts={n:digest(ROOT/'scripts'/n) for n in ['refresh_previous_html_sources.py','prepare_previous_only.py','extract_previous_html.py']},
            files={p.relative_to(run).as_posix():digest(p) for p in run.rglob('*') if p.is_file()}))
        print(json.dumps(dict(run=str(run),summary=result['summary']),ensure_ascii=True))
        return
    # Validate and compute everything before replacing any active source.
    result=process(args.input_dir,existing,reader)
    run=ROOT/'experiments/html-history/source-refresh'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    run.mkdir(parents=True,exist_ok=False)
    write(run/'existing.json',existing)
    write(run/'reader-ids.json',reader)
    write(run/'previous-fixture-before.json',previous_fixture)
    write(run/'results.json',result)
    before={name:digest(ROOT/'HTML'/name) for name in FILES.values()}
    for code,name in INPUTS.items():
        active=ROOT/'HTML'/FILES[code]
        archive(active,FILES[code])
        archive(args.input_dir/name,FILES[code])
        target=run/'incoming'/name
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(args.input_dir/name,target)
    expected=previous_fixture['records']+result['additions']
    if len({r['id'] for r in expected})!=len(expected):
        raise ValueError('Duplicate record ID; sources and fixture were not replaced')
    for code,name in INPUTS.items():
        shutil.copy2(run/'incoming'/name,ROOT/'HTML'/FILES[code])
    write(fixture,dict(previous_fixture,records=expected))
    after={name:digest(ROOT/'HTML'/name) for name in FILES.values()}
    untouched={FILES[c] for c in FILES if c not in INPUTS}
    if any(before[n]!=after[n] for n in untouched):
        raise ValueError('Unexpected change to another source')
    write(run/'manifest.json',dict(publicationAllowed=False,documentedRestarts=True,
        sourcesBefore=before,sourcesAfter=after,
        preservedExistingRecords=True,otherTenSourcesUnchanged=True,
        fixtureAfterSha256=digest(fixture),
        scripts={n:digest(ROOT/'scripts'/n) for n in
            ['refresh_previous_html_sources.py','prepare_previous_only.py','extract_previous_html.py']},
        files={p.relative_to(run).as_posix():digest(p) for p in run.rglob('*') if p.is_file()}))
    print(json.dumps(dict(run=str(run),summary=result['summary']),ensure_ascii=True))


if __name__=='__main__':
    main()
