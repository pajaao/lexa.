"""Prepare reader candidates from the six monitored official snapshots.

No network, no automatic merge and no replacement of archived PDFs. Fail closed
on corrupt snapshots, incomplete coverage, unsupported deletion CSS or orphaned
normative paragraphs. Stable output: unchanged snapshots yield identical files.
"""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import argparse
import copy
import hashlib
import json
import re

from check_official_sources import fingerprint, validate, ADCT
from official_http import check_url

ROOT = Path(__file__).resolve().parent.parent
ARTICLE = re.compile(r'^Art\.?\s*(\d+(?:\.\d{3})*)(?:\s*[º°o])?((?:[-–][A-Z]{1,2}(?=[.\s:\-–]))*)\s*[.:-]?\s*')
RANGE = re.compile(r'^Arts?\.\s*(\d+(?:\.\d{3})*)\.?\s+a\s+(\d+(?:\.\d{3})*)\.?\s*')
HEADING = re.compile(r'^(PARTE\s+(?:GERAL|ESPECIAL|[IVX]+)\b|LIVRO\s+(?:[IVXLCDM]+|PRIMEIRO|SEGUNDO|TERCEIRO|COMPLEMENTAR)\b|(?:TÍTULO|SUBTÍTULO|CAPÍTULO|SEÇÃO|SUBSEÇÃO)\s+(?:[IVXLCDM]+|ÚNIC[OA])\b|DISPOSIÇÃO PRELIMINAR\b|DISPOSIÇÕES (?:FINAIS|GERAIS|TRANSITÓRIAS|COMUNS)\b)', re.I)
UNIT = re.compile(r'^(?:§|Parágrafo\s+único|[IVXLCDM]+\s*[-–—]|[a-z]\))')


def text_of(runs):
    return ''.join(run['text'] for run in runs).strip()


def convert(spec, snapshot):
    if snapshot.get('schema_version') != 1 or snapshot.get('id') != spec['id'] or snapshot.get('source_url') != spec['url']:
        raise ValueError('Identidade ou versão da referência inválida: '+spec['id'])
    check_url(snapshot['source_url'])
    document = snapshot['document']
    if fingerprint(document) != snapshot['semantic_sha256']:
        raise ValueError('Hash da referência não corresponde ao conteúdo: '+spec['id'])
    validate(document, spec)
    if document.get('deletion_styles'):
        raise ValueError('Estilos CSS de exclusão exigem revisão do importador: '+spec['id'])
    date = datetime.fromisoformat(snapshot['captured_at'])
    if date.tzinfo is None:
        raise ValueError('Data de coleta sem fuso horário')
    label_date = date.astimezone(ZoneInfo('America/Sao_Paulo')).strftime('%d/%m/%Y')
    blocks = document['blocks']
    articles, sections, introductions = [], [], []
    scope, high_water = 'main', 0
    hierarchy = {}
    current = None
    stopped = False
    heading_pending = False
    rubric = None
    intro = []
    in_preamble = False
    orphaned = []

    def section_id():
        title = ' › '.join(hierarchy.values()) or ('ADCT' if scope == 'adct' else 'Texto da legislação')
        if not sections or sections[-1]['title'] != title or sections[-1]['scope'] != scope:
            sections.append({'id': str(len(sections)), 'scope': scope, 'title': title})
        return sections[-1]['id']

    for index, runs in enumerate(blocks):
        text = text_of(runs)
        compact = re.sub(r'\s+', '', text).upper()
        heading_text = 'PARTE GERAL' if compact == 'PARTEGERAL' else ('PARTE ESPECIAL' if compact == 'PARTEESPECIAL' else text)
        # Ignore the ADCT link in the top index; only the actual boundary after
        # the constitutional articles can change article namespace.
        if spec['id'] == 'cf' and text.upper() == ADCT and high_water >= spec['last_article'] and scope == 'main':
            scope, high_water, hierarchy, current = 'adct', 0, {0:'ADCT'}, None
            stopped, heading_pending, rubric = False, False, None
            continue
        if stopped:
            continue
        if current and text.startswith(('Brasília,', 'Rio de Janeiro,', 'Este texto não substitui')):
            stopped = True
            continue
        group = RANGE.match(text)
        match = group or ARTICLE.match(text)
        if match:
            base = int(match[1].replace('.', ''))
            number = str(base) + ('' if group else match[2].replace('–','-'))
            key = ('adct-' if scope == 'adct' else '') + number
            if base >= high_water:
                if current is None or current['id'] != key:
                    if any(a['id'] == key for a in articles):
                        raise ValueError('Artigo repetido fora da sequência: '+key)
                    current = {'id': key, 'number': number, 'scope': scope, 'sectionId': section_id(),
                               'sourceBlock': index+1, 'paragraphs': []}
                    if group:
                        current['rangeEnd'] = int(group[2].replace('.', ''))
                    if rubric:
                        current['title'] = rubric
                        rubric = None
                    articles.append(current)
                high_water = max(high_water, current.get('rangeEnd',base))
                current['paragraphs'].append({'runs': copy.deepcopy(runs), 'sourceBlock': index+1})
                in_preamble, heading_pending = False, False
                continue
            # Quoted amendments to another law remain inside their parent article.
        if HEADING.match(heading_text):
            token = heading_text.split()[0].upper()
            level = {'PARTE':0,'LIVRO':1,'TÍTULO':2,'SUBTÍTULO':3,'CAPÍTULO':4,'SEÇÃO':5,'SUBSEÇÃO':6}.get(token,4)
            hierarchy = {k:v for k,v in hierarchy.items() if k<level}
            hierarchy[level] = heading_text
            current, heading_pending = None, True
            continue
        if heading_pending and not UNIT.match(text):
            level = max(hierarchy)
            hierarchy[level] += ' — '+text
            if not text.startswith('('):
                heading_pending = False
            continue
        if spec['id']=='penal' and index+1<len(blocks) and not UNIT.match(text) and len(text)<220 and not text.endswith(('.', ';', ':')) and not text.startswith('(') and ARTICLE.match(text_of(blocks[index+1])):
            rubric = text
            continue
        if current:
            current['paragraphs'].append({'runs':copy.deepcopy(runs),'sourceBlock':index+1})
        elif spec['id']=='cf' and scope=='main' and not articles:
            if text.upper()=='PREÂMBULO':
                in_preamble=True
            elif in_preamble:
                intro.append(text)
        elif hierarchy and not UNIT.match(text) and not match:
            # Wrapped headings and amendment notes can occupy several separate
            # HTML paragraphs before the first article of a chapter.
            hierarchy[max(hierarchy)] += ' — '+text
        elif articles:
            orphaned.append((index+1,text[:160]))

    if orphaned:
        raise ValueError(f'Parágrafos sem artigo em {spec["id"]}: {orphaned[:5]}')
    covered = {scope:set() for scope in ['main','adct']}
    for a in articles:
        if '-' not in a['number']:
            covered[a['scope']].update(range(int(a['number']),a.get('rangeEnd',int(a['number']))+1))
    for sc,last in [('main',spec['last_article']),('adct',spec.get('last_adct_article',0))]:
        missing=set(range(1,last+1))-covered[sc]
        if missing:
            raise ValueError(f'Artigos ausentes após conversão ({spec["id"]}/{sc}): {sorted(missing)}')
    if intro:
        introductions.append({'title':'Preâmbulo','text':' '.join(intro)})
    source = {'kind':'official_html','edition':'Planalto · texto consultado em '+label_date,
              'url':snapshot['source_url'],'capturedAt':snapshot['captured_at'],
              'sha256':snapshot['semantic_sha256'],'rawSha256':snapshot['raw_sha256'],
              'snapshot':'monitor/official/'+spec['id']+'.json','converterVersion':1,
              'coverage':'Texto extraído da fonte oficial, com notas e redações riscadas preservadas.',
              'reviewStatus':'Extração automatizada. A data da coleta não certifica o início de vigência de cada alteração.'}
    return {'articles':articles,'sections':sections,'introductions':introductions,'source':source}


def load_js(path, export_name):
    source=Path(path).read_text()
    marker='export const '+export_name+' = '
    return json.loads(source[source.index(marker)+len(marker):].strip().removesuffix(';'))


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False).encode()).hexdigest()


def changes(previous, candidate):
    def entries(code):
        return {a['id']:{'title':a.get('title'),'paragraphs':[[{'text':r['text'],'deleted':r['deleted']} for r in p['runs']] for p in a['paragraphs']]} for a in code['articles']}
    before,after=entries(previous),entries(candidate)
    return {'added':[key for key in after if key not in before],
            'removed':[key for key in before if key not in after],
            'changed':[key for key in after if key in before and digest(after[key])!=digest(before[key])]}


def article_version(article):
    if article is None:
        return None
    return {'title':article.get('title'), 'paragraphs':[
        {'runs':[{'text':r['text'],'deleted':bool(r['deleted'])} for r in p['runs']]}
        for p in article['paragraphs']]}


def version_signature(version):
    # Ignore PDF/HTML line wrapping, paragraph boundaries and incidental spaces;
    # preserve actual words, punctuation and the source's deletion markings.
    if version is None:
        return None
    tokens=[(False,t) for t in (version.get('title') or '').split()]
    for p in version['paragraphs']:
        for r in p['runs']:
            tokens.extend((r['deleted'],t) for t in r['text'].split())
    return tokens


def history_event(code_id, previous, candidate, existing):
    source=candidate['source']
    prior=previous['source'] if previous else None
    recorded=any(event['codeId']==code_id for event in existing)
    if prior and prior['sha256']==source['sha256'] and prior.get('converterVersion')==source['converterVersion'] and recorded:
        return None
    first=previous is None or not recorded
    event_id=digest({'code':code_id,'from':None if first else prior['sha256'],
                     'to':source['sha256'],'converter':source['converterVersion']})
    if any(event['id']==event_id for event in existing):
        return None
    revisions=[]
    if not first:
        old={a['id']:a for a in previous['articles']}
        new={a['id']:a for a in candidate['articles']}
        for key in dict.fromkeys([*new,*old]):
            before,after=article_version(old.get(key)),article_version(new.get(key))
            if version_signature(before)==version_signature(after):
                continue
            article=new.get(key) or old[key]
            revisions.append({'articleId':key,'number':article['number'],'scope':article['scope'],
                              'rangeEnd':article.get('rangeEnd'),
                              'type':'added' if before is None else ('removed' if after is None else 'changed'),
                              'before':before,'after':after})
    kind='baseline' if first else ('processing' if prior['sha256']==source['sha256'] else ('text' if revisions else 'source'))
    return {'id':event_id,'codeId':code_id,'kind':kind,'capturedAt':source['capturedAt'],
            'sourceUrl':source['url'],'fromVersion':None if first else prior['sha256'],
            'toVersion':source['sha256'],'changes':revisions}


def prepare(root=ROOT):
    root=Path(root)
    specs=json.loads((root/'monitor/sources.json').read_text())
    archived=load_js(root/'data/archive/legislation.js','imported')
    current=load_js(root/'data/official/legislation.js','officialImported')
    history_path=root/'data/history/legislation.js'
    history=load_js(history_path,'updateHistory') if history_path.exists() else []
    if not isinstance(history,list):
        raise ValueError('Histórico de versões inválido')
    candidates={}
    report={}
    for spec in specs:
        snapshot=json.loads((root/'monitor/official'/(spec['id']+'.json')).read_text())
        candidate=convert(spec,snapshot)
        candidates[spec['id']]=candidate
        previous=current.get(spec['id'])
        if previous and not any(event['codeId']==spec['id'] for event in history):
            history.append(history_event(spec['id'],None,previous,history))
        event=history_event(spec['id'],previous,candidate,history)
        if event:
            history.append(event)
        report[spec['id']]={**changes(current.get(spec['id'],archived[spec['id']]),candidate),
                            'articles':len(candidate['articles']),'source':candidate['source']}
    # Validate every document first; no generated output is written on failure.
    payload='export const officialImported = '+json.dumps(candidates,ensure_ascii=False,separators=(',',':'))+';\n'
    (root/'sources').mkdir(exist_ok=True)
    for folder in ['data/official','data/history']:(root/folder).mkdir(parents=True,exist_ok=True)
    (root/'data/official/legislation.js').write_text(payload)
    history_path.write_text('export const updateHistory = '+json.dumps(history,ensure_ascii=False,separators=(',',':'))+';\n')
    (root/'sources/official-manifest.json').write_text(json.dumps({id:d['source'] for id,d in candidates.items()},ensure_ascii=False,indent=2)+'\n')
    run_dir=root/'monitor/run';run_dir.mkdir(parents=True,exist_ok=True)
    (run_dir/'reader-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    rows='\n'.join(f'| {id} | {d["articles"]} | {len(d["added"])} | {len(d["changed"])} | {len(d["removed"])} |' for id,d in report.items())
    body=f'''## Atualização proposta para o leitor

Esta proposta prepara os textos do site a partir das seis fontes oficiais monitoradas. **Não há aprovação, merge ou implantação automática.**

| Legislação | Entradas | Adicionadas | Alteradas | Removidas |
| --- | ---: | ---: | ---: | ---: |
{rows}

A primeira conversão troca a edição baseada nos PDFs pela extração das páginas oficiais. Diferenças de formatação também podem aparecer no relatório; as contagens não são uma classificação jurídica das alterações.

Confira `monitor/official/`, `data/official/legislation.js`, `data/history/legislation.js`, `sources/official-manifest.json` e o artefato `reader-report.json`. A prévia `index.html` inclui a página “Atualizações” com comparações antes/depois. O primeiro registro estabelece a base do histórico, sem apresentar diferenças de migração como mudanças legislativas. Os testes são executados antes desta proposta. Os PDFs originais permanecem arquivados. A data da coleta não certifica vigência: revise notas, revogações e início de efeitos antes de mesclar.

Mesclar incorpora os arquivos gerados ao repositório. A publicação do site depende da hospedagem utilizada; este workflow não faz implantação.
'''
    (run_dir/'pr-body.md').write_text(body)
    for id,d in report.items():
        print(f'{id}: {d["articles"]} entradas; +{len(d["added"])} / ~{len(d["changed"])} / -{len(d["removed"])}')
    return candidates,report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT)
    args=parser.parse_args()
    prepare(args.root)
