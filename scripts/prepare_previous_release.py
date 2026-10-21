"""Validate the complete associated batch and prepare a gated release candidate."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from extract_struck_html import ROOT, FILES, batch, read, write, StruckHTML, decode, spaces, unit
from present_struck_html import prepare

RUN=ROOT/'experiments/previous-wordings-simple/20261021-complete'
OUT=ROOT/'experiments/previous-wordings-release/20261021'
DEST=ROOT/'data/previous-wordings'


def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def validate():
    extraction=batch(RUN/'sources')
    assert extraction==read(RUN/'extraction.json'), 'Source reproduction differs'
    presentation=prepare(extraction,read(RUN/'reader.json'))
    assert presentation==read(RUN/'presentation.json'), 'Association reproduction differs'
    assert read(ROOT/'tests/fixtures/previous-wordings-simple.json')['records']==presentation['records']
    for source in extraction['sources']:
        assert digest(ROOT/'HTML'/source['file'])==source['sha256'],source['file']
    raw=(RUN/'sources'/FILES['cpp']).read_bytes()
    parser=StruckHTML(decode(raw)[0]);parser.feed(decode(raw)[0]);parser.close();parser.flush()
    starts=[i for i,b in enumerate(parser.blocks) if (m:=unit(spaces(''.join(r['text'] for r in b['runs'])))) and m[:2]==('caput','406')]
    assert starts==[1559,1812], 'CPP region changed; review the exclusion rule'
    selected=[]; excluded=[]; checks=[]
    entries={e['id']:e for s in extraction['sources'] for e in s['entries']}
    for row in presentation['records']:
        occurrence=entries[row['id']]
        assert occurrence['extracted']
        assert occurrence['context']['region'] not in {'original_general_part','quoted','approval_decree'}
        assert all(row[k]==occurrence[k] for k in ['text','notes','source','evidence','part','unitLabel'])
        assert row['review']=={'status':'pending'} and row['wording']['status']=='previous'
        decision=next(d for d in presentation['decisions'] if d['id']==row['id'])
        assert decision['associated'] and (decision['readerParagraphMatches'] or decision['currentCaputWitnesses'])
        reason='restructured_cpp_jury_scope_not_proven' if row['codeId']=='cpp' and starts[0]<=row['evidence']['block']<starts[1] else None
        checks.append(dict(id=row['id'],textAndNotesExact=True,sourceBytesVerified=True,documentContextCompatible=not bool(reason),
                           associationEvidence=decision,excludedReason=reason))
        if reason:
            excluded.append(dict(id=row['id'],codeId=row['codeId'],articleId=row['articleId'],reason=reason,
                                 source=row['source'],evidenceBlock=row['evidence']['block']))
        else: selected.append(row)
    assert len(selected)+len(excluded)==1903
    assert len({r['id'] for r in selected})==len(selected)
    return selected,dict(inputCount=1903,selectedCount=len(selected),excluded=excluded,checks=checks,
        byLegislation={c:sum(r['codeId']==c for r in selected) for c in FILES},
        deviceCount=len({(r['codeId'],r['articleId']) for r in selected}),
        humanReviewPerformed=False,publicationAuthorized=False,
        readerFile='data/official/legislation.js',readerSha256=hashlib.sha256((ROOT/'data/official/legislation.js').read_text(encoding='utf-8').encode('utf-8')).hexdigest())


def public_records(selected):
    public=[]
    for row in selected:
        record={k:v for k,v in row.items() if k!='evidence'}
        record['evidence']={k:row['evidence'][k] for k in ['charRange','block','line','editorialNotes']}
        record['evidence']['auditId']=row['id']
        public.append(record)
    return public


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    selected,report=validate()
    if args.verify:
        assert report==read(OUT/'validation.json')
        assert [r['id'] for r in selected]==read(DEST/'release.json')['recordIds']
        assert read(DEST/'candidate.json')==dict(records=public_records(selected)), 'Candidate text or metadata differs'
        assert digest(DEST/'candidate.json')==read(DEST/'release.json')['dataSha256']
        print('All 1903 source occurrences validated; candidate exclusions reproduced.'); return
    if OUT.exists() or DEST.exists(): raise ValueError('Preserve existing release artifacts')
    write(OUT/'validation.json',report)
    # Full raw evidence stays immutable in the source run; the site ships pointers, not duplicate HTML.
    public=public_records(selected)
    write(DEST/'candidate.json',dict(records=public))
    write(DEST/'release.json',dict(schemaVersion=1,releaseId='previous-wordings-20261021',
        recordIds=[r['id'] for r in public],recordCount=len(public),byLegislation=report['byLegislation'],
        dataSha256=digest(DEST/'candidate.json'),readerSha256=report['readerSha256'],
        validationReport=OUT.relative_to(ROOT).as_posix()+'/validation.json',validationSha256=digest(OUT/'validation.json'),
        sourceRun=RUN.relative_to(ROOT).as_posix(),publicationAuthorized=False,
        governanceDecision=None,riskReviewDecision=None,publicationDecision=None))
    print(json.dumps({k:report[k] for k in ['selectedCount','byLegislation','deviceCount']}))


if __name__=='__main__': main()
