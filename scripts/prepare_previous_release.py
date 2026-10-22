"""Reproduce the corrected documentary batch and prepare its gated release."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from extract_struck_html import ROOT, FILES, batch, read, spaces
from present_struck_html import prepare

RUN=ROOT/'experiments/previous-wordings-simple/20261021-associations-corrected'
OUT=ROOT/'experiments/previous-wordings-release/20261021-associations'
DEST=ROOT/'data/previous-wordings'

def write(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def validate():
    extraction=batch(ROOT/'HTML')
    assert extraction==read(RUN/'extraction.json'),'Source reproduction differs'
    presentation=prepare(extraction,read(RUN/'reader.json'))
    assert presentation==read(RUN/'presentation.json'),'Association reproduction differs'
    selected=presentation['records']
    assert read(ROOT/'tests/fixtures/previous-wordings-simple.json')['records']==selected
    entries={e['id']:e for s in extraction['sources'] for e in s['entries']}
    decisions={d['id']:d for d in presentation['decisions']}
    checks=[]
    for row in selected:
        source_id=row['id'].split('-fragment-')[0]
        occurrence=entries[source_id];decision=decisions[source_id]
        assert occurrence['extracted'] and decision['associated'] and decision['documentaryAssociated']
        assert row['articleId']==occurrence['context']['articleId']
        assert occurrence['context']['articleBlock'] is not None
        assert all(row[k]==occurrence[k] for k in ['notes','source','part'])
        if row['evidence'].get('fragmentTextRange'):
            a,z=row['evidence']['fragmentTextRange']
            assert row['text']==spaces(occurrence['evidence']['rawText'][a:z])
        else:assert row['text']==occurrence['text']
        assert row['review']=={'status':'pending'} and row['wording']['status']=='previous'
        if occurrence['context']['region'] in {'original_general_part','restructured_jury'}:
            assert row.get('documentaryContext') and 'não estabelecida' in row['documentaryContext']
        checks.append(dict(id=row['id'],sourceOccurrenceId=source_id,textAndNotesExact=True,sourceBytesVerified=True,documentContextCompatible=True,associationEvidence=decision,excludedReason=None))
    excluded=[dict(id=d['id'],codeId=d['codeId'],articleId=d['articleId'],reasons=d['reasons'],source=entries[d['id']]['source'],evidenceBlock=entries[d['id']]['evidence']['block']) for d in presentation['decisions'] if not d['associated']]
    assert len(selected)==3036 and len(decisions)==3188 and len(excluded)==154
    assert sum(d['associated'] for d in decisions.values())==3034
    assert len({r['id'] for r in selected})==len(selected)
    return selected,dict(inputCount=3188,associatedOccurrenceCount=3034,selectedCount=len(selected),excluded=excluded,checks=checks,
        byLegislation={c:sum(r['codeId']==c for r in selected) for c in FILES},deviceCount=len({(r['codeId'],r['articleId']) for r in selected}),
        sourceHashes={s['file']:s['sha256'] for s in extraction['sources']},sourceExtractionSha256=digest(RUN/'extraction.json'),
        individualLegalHomologation=False,humanSampleReviewReference='docs/REDACOES-ANTERIORES-LANCAMENTO.md#avaliacao-do-responsavel',
        readerFile='data/official/legislation.js',readerSha256=hashlib.sha256((ROOT/'data/official/legislation.js').read_text(encoding='utf8').encode('utf8')).hexdigest())

def public_records(selected):
    public=[]
    for row in selected:
        record={k:v for k,v in row.items() if k!='evidence'}
        record['evidence']={k:row['evidence'][k] for k in ['charRange','block','line','editorialNotes','fragmentTextRange'] if k in row['evidence']}
        record['evidence']['auditId']=row['id'].split('-fragment-')[0]
        public.append(record)
    return public

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    selected,report=validate()
    if args.verify:
        assert report==read(OUT/'validation.json')
        manifest=read(DEST/'release.json')
        assert [r['id'] for r in selected]==manifest['recordIds']
        assert read(DEST/'candidate.json')==dict(records=public_records(selected))
        assert digest(DEST/'candidate.json')==manifest['dataSha256']
        assert digest(OUT/'validation.json')==manifest['validationSha256']
        print('3034 associated occurrences / 3036 pending records reproduced; 154 exclusions preserved.');return
    if OUT.exists():raise ValueError('Preserve existing release validation; use --verify')
    write(OUT/'validation.json',report)
    public=public_records(selected);write(DEST/'candidate.json',dict(records=public))
    write(DEST/'release.json',dict(schemaVersion=1,releaseId='previous-wordings-associations-20261021',recordIds=[r['id'] for r in public],recordCount=len(public),byLegislation=report['byLegislation'],dataSha256=digest(DEST/'candidate.json'),readerSha256=report['readerSha256'],readerHashMode='utf8-lf',validationReport=OUT.relative_to(ROOT).as_posix()+'/validation.json',validationSha256=digest(OUT/'validation.json'),sourceRun=RUN.relative_to(ROOT).as_posix(),publicationAuthorized=False,governanceDecision=None,riskReviewDecision=None,publicationDecision=None))
    print('Prepared 3036 records with publication blocked; authorization is a separate product decision.')

if __name__=='__main__':main()
