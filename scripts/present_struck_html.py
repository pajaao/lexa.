"""Map extracted occurrences to the experimental reader; never reconstruct history."""
import argparse
from collections import Counter
import hashlib
import json
import re
from pathlib import Path
import subprocess
from extract_struck_html import ROOT, read, write, split_notes, spaces


def prepare(extraction, reader):
    records=[]; decisions=[]; seen=set()
    for source in extraction['sources']:
        code=reader.get(source['codeId'],{})
        for entry in source['entries']:
            reasons=list(entry['reasons'])
            context=entry['context']; article=context['articleId']
            if context['region'] in {'original_general_part','approval_decree','quoted'}:
                reasons.append('incompatible_or_quoted_document_context')
            target=code.get('articles',{}).get(article)
            if not target: reasons.append('no_reader_device')
            matching=[]; witnesses=[]
            if target:
                for i,paragraph in enumerate(target['paragraphs']):
                    raw=''.join(r['text'] for r in paragraph['runs'])
                    try: body=split_notes(raw)[0]
                    except ValueError: continue
                    if spaces(body)==spaces(entry['text']): matching.append(i)
                    witnesses.extend(dict(sourceBlock=w['block'],readerParagraph=i) for w in context.get('unstruckCaputs',[]) if spaces(w['text'])==spaces(body))
                if not matching and not witnesses: reasons.append('no_documentary_text_or_current_caput_witness')
            identity=(source['codeId'],article,entry['part'],entry['unitLabel'],spaces(entry['text']))
            if not reasons and identity in seen: reasons.append('duplicate_documentary_text')
            if not reasons:
                seen.add(identity)
                records.append(dict(id=entry['id'],codeId=entry['codeId'],articleId=article,
                    part=entry['part'],unitLabel=entry['unitLabel'],text=entry['text'],notes=entry['notes'],
                    reference='\n'.join(note for note in entry['notes'] if re.search(r'\b(?:Lei|Emenda|Decreto|Medida Provisória)\b',note)) or None,sequence=dict(order=entry['evidence']['block'],
                        basis='Ordem na fonte HTML local; não demonstra sucessão legislativa ou vigência.'),
                    review=dict(status='pending'),wording=dict(status='previous',basis='Unidade integralmente riscada na fonte local.'),
                    source=entry['source'],evidence=entry['evidence']))
            decisions.append(dict(id=entry['id'],codeId=entry['codeId'],articleId=article,
                associated=not reasons,reasons=sorted(set(reasons)),readerParagraphMatches=matching,currentCaputWitnesses=witnesses))
    return dict(records=records,decisions=decisions,summary=[dict(codeId=s['codeId'],
        found=len(s['entries']),extracted=sum(e['extracted'] for e in s['entries']),
        associated=sum(d['associated'] for d in decisions if d['codeId']==s['codeId']),
        reasons=dict(Counter(r for d in decisions if d['codeId']==s['codeId'] for r in d['reasons'])))
        for s in extraction['sources']])


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--verify',action='store_true')
    args=parser.parse_args(); run=args.input.resolve()
    if not run.is_relative_to(ROOT/'experiments/previous-wordings-simple'):
        raise ValueError('Input must remain experimental')
    fixture=ROOT/'tests/fixtures/previous-wordings-simple.json'
    if args.verify:
        result=prepare(read(run/'extraction.json'),read(run/'reader.json'))
        assert result==read(run/'presentation.json')
        assert read(run/'preview.json')==dict(preview=True,records=result['records'])
        for name,digest in read(run/'manifest.json')['files'].items():
            assert hashlib.sha256((run/name).read_bytes()).hexdigest()==digest,name
        manifest=read(run/'manifest.json')
        for name,digest in manifest['scripts'].items():
            script=ROOT/'scripts'/name
            contents=script.read_text(encoding='utf-8').encode('utf-8') if manifest.get('scriptHashMode')=='utf8-lf' else script.read_bytes()
            assert hashlib.sha256(contents).hexdigest()==digest,name
        print('Presentation, pending fixture and hashes reproduced.'); return
    if not (run/'extraction.json').exists(): raise ValueError('Extraction must complete before presentation')
    if (run/'presentation.json').exists():
        raise ValueError('Preserve existing output; select a fresh experiment before replacing a fixture')
    script="import {officialImported} from './data/official/legislation.js'; console.log(JSON.stringify(Object.fromEntries(Object.entries(officialImported).map(([c,v])=>[c,{source:v.source,articles:Object.fromEntries(v.articles.map(a=>[a.id,a]))}]))));"
    reader=json.loads(subprocess.check_output(['node','--input-type=module','-e',script],cwd=ROOT).decode('utf-8'))
    write(run/'reader.json',reader)
    result=prepare(read(run/'extraction.json'),reader)
    write(run/'presentation.json',result)
    if fixture.exists(): write(run/'fixture-before.json',read(fixture))
    write(run/'preview.json',dict(preview=True,records=result['records']))
    write(fixture,dict(preview=True,records=result['records']))
    write(run/'manifest.json',dict(publicationAllowed=False,homologation='pending',
        fixtureSha256=hashlib.sha256(fixture.read_bytes()).hexdigest(),
        scriptHashMode='utf8-lf',scripts={n:hashlib.sha256((ROOT/'scripts'/n).read_text(encoding='utf-8').encode('utf-8')).hexdigest() for n in ['extract_struck_html.py','present_struck_html.py']},
        files={p.relative_to(run).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in run.rglob('*') if p.is_file()}))
    print(json.dumps(result['summary']))


if __name__=='__main__': main()
