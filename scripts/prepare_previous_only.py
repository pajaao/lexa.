"""Prepare only previous wordings from local saved HTML, without replacement research.

Keeps the older experimental datasets untouched. Every addition is pending.
"""

import hashlib

import json

import re

from pathlib import Path

from extract_previous_html import (ROOT, FILES, EvidenceHTML, decode,

    inspect_source, split_notes, spaces, canonical, PENALTY, unit)

def previous_blocks(code, filename, raw, reader_ids, existing=(), documented_restarts=True, allow_unmapped_general_part=False):

    candidates, _, inventory = inspect_source(code, filename, raw, reader_ids, documented_restarts=documented_restarts, allow_unmapped_general_part=allow_unmapped_general_part)

    source, _ = decode(raw)

    parser = EvidenceHTML(source)

    parser.feed(source)

    parser.close()

    parser.flush()

    by_block = {c['block']: c for c in candidates}

    seen = {(r['codeId'],r['articleId'],canonical(r['text'])) for r in existing

            if r.get('wording',{}).get('status')=='previous'}

    records, excluded, article = [], [], None

    unsafe = {'quoted_or_indented_container_requires_review',

        'numbering_regression_or_later_document_region', 'article_not_in_reader',

        'letter_without_explicit_parent_item', 'multiple_units_in_same_block',

        'multiple_inline_units', 'incomplete_editorial_note'}

    for index, block in enumerate(parser.blocks):

        candidate = by_block.get(index)
        quoted = documented_restarts and 'blockquote' in block['contextTags']
        if quoted:
            article = None

        if candidate:

            article = candidate['articleId']

            if unsafe.intersection(candidate['flags']):

                article = None

        raw_text = ''.join(r['text'] for r in block['runs'])

        if not any(r['deleted'] and r['text'].strip() for r in block['runs']):

            continue

        reasons = []
        if quoted:
            reasons.append('quoted_or_indented_container_requires_review')

        if parser.deletion_styles:

            reasons.append('unsupported_stylesheet_deletion_rules')

        if not article or article not in reader_ids:

            reasons.append('article_not_safely_identified')

        if candidate:

            reasons.extend(sorted(unsafe.intersection(candidate['flags'])))

            part, label = candidate['part'], candidate['unitLabel']

        elif PENALTY.match(spaces(raw_text)):

            part, label = 'penalty', 'Pena'

        else:

            reasons.append('not_identified_as_normative_unit')

            part, label = None, None

        try:

            body, notes, ranges = split_notes(raw_text)

        except ValueError:

            body, notes, ranges = '', [], []

            reasons.append('incomplete_editorial_note')

        raw_marker=unit(raw_text.lstrip())

        normative_start=len(raw_text)-len(raw_text.lstrip())+(raw_marker[3] if raw_marker else 0)

        states, cursor = [], 0

        for run in block['runs']:

            for i, char in enumerate(run['text'], cursor):

                if i>=normative_start and char.isalpha() and char not in 'º°' and not any(a<=i<b for a,b in ranges):

                    states.append(run['deleted'])

            cursor += len(run['text'])

        if not states or not all(states):

            reasons.append('not_a_fully_struck_normative_block')

        marker=unit(body)

        content=body[marker[3]:] if marker else PENALTY.sub('',body,count=1)

        if re.match(r'^[\s.:\-–—(]*(?:VETAD[OA]|Revogad[oa])\b',content,re.I):

            reasons.append('editorial_placeholder_not_previous_wording')

        if not any(c.isalpha() for c in content):

            reasons.append('marker_without_normative_text')

        if not body or not re.search(r'[.;:]["”]?$|[.;:]\s*\.$',body):

            reasons.append('incomplete_or_undelimited_unit')

        if re.search(r'^(?:Art\.?\s*[\dA-Z.-]+\s*)?\(?\s*(?:VETAD[OA]|Revogad[oa])\b',body,re.I):

            reasons.append('editorial_placeholder_not_previous_wording')

        evidence = dict(rawHtml=block['rawHtml'],rawText=raw_text,rawUnitText=raw_text,

            charRange=[block['start'],block['end']],line=block['line'],block=index,

            anchors=block['anchors'],runs=block['runs'])
        if documented_restarts:
            evidence['contextTags']=block['contextTags']

        if reasons:

            excluded.append(dict(codeId=code,articleId=article,block=index,

                reasons=sorted(set(reasons)),evidence=evidence))

            continue

        identity = (code,article,canonical(body))

        if identity in seen:

            continue

        seen.add(identity)

        if candidate and part=='caput' and PENALTY.search(body):

            part, label = 'article', 'Trecho da fonte: caput e pena'

        basis='Posição do trecho riscado na fonte local; sem reconstrução legislativa ou inferência de vigência.'

        records.append(dict(id=f'{code}-{article}-previous-{inventory["sha256"][:12]}-b{index}',

            codeId=code,articleId=article,part=part,unitLabel='Caput' if part=='caput' else label,

            text=body,sequence=dict(order=index+10000,basis=basis),

            reference=None,notes=notes,review=dict(status='pending'),

            wording=dict(status='previous',basis='Texto normativo integralmente riscado na fonte local.'),

            source=dict(label='Planalto — HTML oficial salvo localmente',document=filename,

                sha256=inventory['sha256'],url=inventory['origin'],

                location=f'Linha {block["line"]}, bloco {index}'),evidence=evidence))

    return dict(records=records,excluded=excluded,source=inventory)

def ensure_source_baseline(root=ROOT):
    manifest=root/'experiments/html-history/previous-only/manifest.json'
    if manifest.exists():
        sources=json.loads(manifest.read_text(encoding='utf-8'))['sources']
        if any(hashlib.sha256((root/'HTML'/name).read_bytes()).hexdigest()!=expected for name,expected in sources.items()):
            raise ValueError('Sources changed: use refresh_previous_html_sources.py to preserve existing records and source editions.')

def main():
    ensure_source_baseline()

    existing=json.loads((ROOT/'experiments/html-history/existing-records.json').read_text(encoding='utf-8'))

    existing+=json.loads((ROOT/'tests/fixtures/legislative-history-html.json').read_text(encoding='utf-8'))['records']

    reader=json.loads((ROOT/'experiments/html-history/reader-ids.json').read_text(encoding='utf-8'))

    results=[]

    for code,name in FILES.items():

        path=ROOT/'HTML'/name

        raw=path.read_bytes()

        results.append(previous_blocks(code,name,raw,set(reader[code]),existing))

        assert hashlib.sha256(path.read_bytes()).hexdigest()==results[-1]['source']['sha256']

    output=ROOT/'experiments/html-history/previous-only'

    output.mkdir(parents=True,exist_ok=True)

    records=[r for result in results for r in result['records']]

    for key in ('records','excluded'):

        (output/(key+'.json')).write_text(json.dumps([r for result in results for r in result[key]],ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

    (ROOT/'tests/fixtures/previous-wordings-html.json').write_text(json.dumps(dict(records=records),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

    manifest=dict(publicationAllowed=False,sources={r['source']['file']:r['source']['sha256'] for r in results},

        scriptSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),

        files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in output.glob('*.json') if p.name!='manifest.json'})

    (output/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

    previous=[r for r in existing if r.get('wording',{}).get('status')=='previous']+records

    print(json.dumps(dict(additions=len(records),previousWordings=len(previous),

        articles=len({(r['codeId'],r['articleId']) for r in previous})),ensure_ascii=False))

if __name__=='__main__':

    main()
