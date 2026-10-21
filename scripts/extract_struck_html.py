"""Extract struck documentary units only. No reader mapping or legislative reconstruction."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

# Reuse byte decoding, evidence capture and marker parsing, not the old preparers.
from extract_previous_html import ROOT, FILES, EvidenceHTML, decode, split_notes, spaces, unit, PENALTY


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


class StruckHTML(EvidenceHTML):
    """Support simple embedded CSS selectors as well as tags and inline CSS.

    Complex selectors are reported, never approximated. Original HTML is untouched.
    """
    def __init__(self, source):
        super().__init__(source)
        self.selectors=[]
        self.unsupported=[]
        for sheet in re.findall(r'<style\b[^>]*>(.*?)</style>',source,re.S|re.I):
            sheet=re.sub(r'/\*.*?\*/','',sheet,flags=re.S)
            if 'line-through' in sheet.lower() and ('@' in sheet or re.search(r'text-decoration(?:-line)?\s*:[^;{}]*(?:none|underline|overline)',sheet,re.I)):
                self.unsupported.append('conditional_or_conflicting_css_requires_review')
            for selector, declarations in re.findall(r'([^{}]+)\{([^{}]*)\}',sheet):
                if not re.search(r'text-decoration(?:-line)?\s*:[^;]*line-through',declarations,re.I):
                    continue
                for item in selector.split(','):
                    item=item.strip()
                    if re.fullmatch(r'(?:[a-zA-Z][\w-]*)?(?:[.#][\w-]+)*',item) and item:
                        self.selectors.append(item)
                    else:
                        self.unsupported.append(item)

    def handle_starttag(self, tag, attrs):
        attrs=list(attrs)
        values=dict(attrs)
        for selector in self.selectors:
            match=re.match(r'^[\w-]+',selector)
            if match and match[0].lower()!=tag:
                continue
            if all((kind=='.' and name in values.get('class','').split()) or
                   (kind=='#' and name==values.get('id'))
                   for kind,name in re.findall(r'([.#])([\w-]+)',selector)):
                attrs=[(k,v) for k,v in attrs if k!='style']+[
                    ('style',values.get('style','')+';text-decoration:line-through')]
                break
        super().handle_starttag(tag,attrs)


def extract(code, filename, raw):
    source, encoding=decode(raw)
    parser=StruckHTML(source)
    parser.feed(source); parser.close(); parser.flush()
    blocks=parser.blocks
    origin=re.search(r'saved from url=\(\d+\)([^\s]+)',source)
    digest=hashlib.sha256(raw).hexdigest()
    from urllib.parse import urlparse
    if not origin or urlparse(origin[1]).hostname not in {'www.planalto.gov.br','planalto.gov.br'}:
        raise ValueError('Source is missing its official saved-page origin: '+filename)
    ones=[i for i,b in enumerate(blocks) if (u:=unit(spaces(''.join(r['text'] for r in b['runs'])))) and u[:2]==('caput','1')]
    # This is a document boundary, explicitly NOT an identity relationship.
    cp_boundary=ones[-1] if code=='penal' and len(ones)>1 else -1
    clt_boundary=next((i for i,b in enumerate(blocks) if spaces(''.join(r['text'] for r in b['runs'])).upper()=='CONSOLIDAÇÃO DAS LEIS DO TRABALHO'),-1)
    article=None; paragraph=None; item=None; adct=False; cf_end_seen=False
    entries=[]; groups={}; group=0; previous_article=None
    for index,b in enumerate(blocks):
        raw_text=''.join(r['text'] for r in b['runs'])
        text=spaces(raw_text)
        if code=='cf' and cf_end_seen and text.upper().startswith('ATO DAS DISPOSIÇÕES CONSTITUCIONAIS TRANSITÓRIAS'):
            adct=True; article=None; paragraph=None; item=None
        quoted='blockquote' in b['contextTags']
        marker=unit(text)
        if code=='cf' and not quoted and marker and marker[:2]==('caput','250'): cf_end_seen=True
        if quoted:
            article=None; paragraph=None; item=None
        elif marker and marker[0]=='caput':
            article=('adct-' if adct else '')+marker[1]; paragraph=None; item=None
        elif marker and marker[0]=='paragraph':
            paragraph=marker[2]; item=None
        elif marker and marker[0]=='item':
            item=marker[2]
        if article!=previous_article:
            group+=1; previous_article=article
        if marker and marker[0]=='caput' and not quoted and not any(r['deleted'] and any(c.isalpha() for c in r['text']) for r in b['runs']):
            try:
                witness=split_notes(raw_text)[0]
            except ValueError:
                witness=None
            if witness: groups.setdefault(group,[]).append(dict(text=witness,block=index,line=b['line']))
        if not any(r['deleted'] and r['text'].strip() for r in b['runs']):
            continue
        evidence=dict(rawHtml=b['rawHtml'],rawText=raw_text,rawUnitText=raw_text,
                      runs=b['runs'],anchors=b['anchors'],contextTags=b['contextTags'],
                      charRange=[b['start'],b['end']],line=b['line'],block=index)
        reasons=[]
        try:
            body,notes,ranges=split_notes(raw_text)
        except ValueError:
            body,notes,ranges='',[],[]; reasons.append('incomplete_editorial_note')
        editorial=[]
        for note,(a,z) in zip(notes,ranges):
            links=[]; offset=0
            for run in b['runs']:
                if run.get('href') and offset<z and offset+len(run['text'])>a and run['href'] not in links: links.append(run['href'])
                offset+=len(run['text'])
            editorial.append(dict(text=note,links=links))
        evidence['editorialNotes']=editorial
        m=unit(body)
        part=m[0] if m else 'penalty' if PENALTY.match(body) else None
        label={'caput':'Caput','penalty':'Pena'}.get(part,m[2] if m else '')
        if part=='item' and paragraph: label=paragraph+' · '+label
        if part=='letter':
            if not item: reasons.append('letter_without_parent_item')
            label=' · '.join(x for x in [paragraph,item,label] if x)
        if not part: reasons.append('unidentified_unit')
        # Markers and editorial notes may be unstruck; the normative body must be fully struck.
        start=len(raw_text)-len(raw_text.lstrip())
        original_marker=unit(raw_text.lstrip())
        start+=original_marker[3] if original_marker else 0
        states=[]; cursor=0
        for run in b['runs']:
            states.extend(run['deleted'] for i,c in enumerate(run['text'],cursor)
                          if i>=start and c.isalpha() and c not in 'º°' and not any(a<=i<z for a,z in ranges))
            cursor+=len(run['text'])
        if not states or not all(states): reasons.append('partial_or_non_normative_strike')
        content=body[m[3]:] if m else PENALTY.sub('',body,count=1)
        if re.match(r'^[\s.:(-]*(?:VETAD[OA]|Revogad[oa])\b',content,re.I):
            reasons.append('veto_or_revocation_placeholder')
        if not any(c.isalpha() for c in content): reasons.append('empty_normative_body')
        if not re.search(r'[.;:]["”]?$|[.;:]\s*\.$',body): reasons.append('incomplete_unit')
        if len(re.findall(r'\bArt\.?\s+\d+',body,re.I))>1: reasons.append('multiple_articles_in_block')
        if re.search(r'<br\s*/?>\s*(?:<(?:s|strike|span)[^>]*>\s*)*(?:§|[IVXLCDM]+\s*[-–—]|[a-z]\))',b['rawHtml'],re.I):
            reasons.append('multiple_units_with_explicit_break')
        if parser.unsupported: reasons.append('unsupported_embedded_css')
        if part=='caput' and PENALTY.search(body): part='article'; label='Trecho da fonte: caput e pena'
        region='quoted' if quoted else 'original_general_part' if index<cp_boundary else 'approval_decree' if code=='clt' and clt_boundary>=0 and index<clt_boundary else 'adct' if adct else 'main'
        entries.append(dict(id=f'{code}-simple-{digest[:12]}-b{index}',codeId=code,
            context=dict(articleId=article,region=region,group=group),part=part,unitLabel=label,text=body,notes=notes,
            extracted=not reasons,reasons=sorted(set(reasons)),
            source=dict(label='Planalto — HTML oficial salvo localmente',document=filename,sha256=digest,
                        url=origin[1],location=f'Linha {b["line"]}, bloco {index}'),evidence=evidence))
    for entry in entries:
        entry['context']['unstruckCaputs']=groups.get(entry['context']['group'],[])
    return dict(codeId=code,file=filename,sha256=digest,encoding=encoding,
                unsupportedCss=parser.unsupported,entries=entries)


def batch(directory):
    results=[extract(code,name,(directory/name).read_bytes()) for code,name in FILES.items()]
    return dict(sources=results,found=sum(len(r['entries']) for r in results),
                extracted=sum(e['extracted'] for r in results for e in r['entries']))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--verify',action='store_true')
    args=parser.parse_args(); run=args.output.resolve()
    if not run.is_relative_to(ROOT/'experiments/previous-wordings-simple'):
        raise ValueError('Output must remain inside the simple experiment directory')
    if args.verify:
        assert batch(run/'sources')==read(run/'extraction.json')
        print('All 13 saved sources reproduced exactly.'); return
    if run.exists(): raise ValueError('Existing evidence must not be overwritten')
    result=batch(ROOT/'HTML')
    import shutil
    for name in FILES.values():
        dest=run/'sources'/name; dest.parent.mkdir(parents=True,exist_ok=True); shutil.copyfile(ROOT/'HTML'/name,dest)
    write(run/'extraction.json',result)
    print(json.dumps(dict(found=result['found'],extracted=result['extracted'])))


if __name__=='__main__': main()
