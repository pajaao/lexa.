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


def documentary_notes(raw):
    """Keep a recoverable prefix even when an editorial note has no closing )."""
    from extract_previous_html import NOTE, BARE_NOTE
    ranges=[]; notes=[]; warnings=[]; cursor=0
    while match:=NOTE.search(raw,cursor):
        depth=0; end=len(raw)
        for i in range(match.start(),len(raw)):
            depth+=(raw[i]=='(')-(raw[i]==')')
            if depth==0: end=i+1; break
        else: warnings.append('incomplete_editorial_note_preserved')
        ranges.append((match.start(),end));notes.append(spaces(raw[match.start():end]));cursor=end
    for match in BARE_NOTE.finditer(raw):
        if not any(a<=match.start()<z for a,z in ranges):
            ranges.append(match.span());notes.append(spaces(match[0]))
    for bare in re.finditer(r'\bVigência(?:\s+encerrada)?\b',raw):
        if any(a<=bare.start()<z for a,z in ranges):continue
        adjacent=any(z<=bare.start() and not re.search(r'[^\s.;:]',raw[z:bare.start()]) for a,z in ranges)
        if adjacent or raw.strip()==bare[0]:ranges.append(bare.span());notes.append(spaces(bare[0]))
    ordered=sorted(zip(ranges,notes));ranges=[r for r,n in ordered];notes=[n for r,n in ordered]
    return spaces(''.join(c for i,c in enumerate(raw) if not any(a<=i<z for a,z in ranges))),notes,ranges,warnings


def documentary_unit(text):
    marker=unit(text)
    if marker:return marker
    if m:=re.match(r'^A\s*rt\.?\s*(\d+(?:\.\d{3})*)(?:\s*[-–]\s*([A-Z]))?[º°o]?\s*[.:-]?\s*',text):
        return 'caput',m[1].replace('.','')+('-'+m[2] if m[2] else ''),'caput',m.end()
    if m:=re.match(r'^([a-z])\s*\)',text):return 'letter',None,'alínea '+m[1],m.end()
    if m:=re.match(r'^([IVXLCDM]+(?:-?[A-Z])?)\s+(?=[a-záéíóúâêôãõç])',text):
        return 'item',None,'inciso '+m[1],m.end()
    return None


def native_article_anchor(block,article):
    compact=lambda value:re.sub(r'[-–.\s]','',value).lower()
    expected=compact(article)
    return any(compact(anchor) in {'art'+expected,'c'+expected} for anchor in block['anchors'])


def extract(code, filename, raw):
    source, encoding=decode(raw);parser=StruckHTML(source)
    parser.feed(source);parser.close();parser.flush();blocks=parser.blocks
    origin=re.search(r'saved from url=\(\d+\)([^\s]+)',source)
    digest=hashlib.sha256(raw).hexdigest()
    from urllib.parse import urlparse
    if not origin or urlparse(origin[1]).hostname not in {'www.planalto.gov.br','planalto.gov.br'}:
        raise ValueError('Source is missing its official saved-page origin: '+filename)
    texts=[spaces(''.join(r['text'] for r in b['runs'])) for b in blocks]
    markers=[documentary_unit(t) for t in texts]
    structural=re.compile(r'^(?:C[ÓO]DIGO PENAL\b|PARTE\b|T[ÍI]TULO\b|CAP[ÍI]TULO\b|SE(?:CÇ|Ç|C)[ÃA]O(?:\b|(?=[IVXLCDM]))|SUBSE(?:CÇ|Ç|C)[ÃA]O\b|LIVRO\b)',re.I)
    structures=[not m and (bool(structural.match(t)) or bool(re.match(r'^D[AO]S?\s',t) and t.isupper()) or (i>0 and bool(structural.match(texts[i-1])))) for i,(t,m) in enumerate(zip(texts,markers))]
    ones=[i for i,m in enumerate(markers) if m and m[:2]==('caput','1')]
    cp_boundary=ones[-1] if code=='penal' and len(ones)>1 else -1
    jury=[i for i,m in enumerate(markers) if m and m[:2]==('caput','406')] if code=='cpp' else []
    clt_boundary=next((i for i,t in enumerate(texts) if t.upper()=='CONSOLIDAÇÃO DAS LEIS DO TRABALHO'),-1)
    article=None;article_block=None;paragraph=None;item=None;adct=False;cf_end_seen=False;quote_native=False
    entries=[];groups={};group=0;previous_article=None
    for index,b in enumerate(blocks):
        raw_text=''.join(r['text'] for r in b['runs']);text=texts[index];marker=markers[index]
        if code=='cf' and cf_end_seen and text.upper().startswith('ATO DAS DISPOSIÇÕES CONSTITUCIONAIS TRANSITÓRIAS'):
            adct=True;article=None;article_block=None;paragraph=None;item=None
        quoted='blockquote' in b['contextTags']; foreign_quote=False
        if structures[index]:article=None;article_block=None;paragraph=None;item=None;quote_native=False
        elif marker and marker[0]=='caput':
            if quoted and not native_article_anchor(b,marker[1]):
                article=None;article_block=None;quote_native=False;foreign_quote=True
            else:
                article=('adct-' if adct else '')+marker[1];article_block=index;paragraph=None;item=None
                quote_native=quoted
                if code=='cf' and marker[1]=='250':cf_end_seen=True
        elif quoted and not quote_native:
            article=None;article_block=None;foreign_quote=True
        elif marker and marker[0]=='paragraph':paragraph=marker[2];item=None
        elif marker and marker[0]=='item':item=marker[2]
        if article!=previous_article:group+=1;previous_article=article
        if marker and marker[0]=='caput' and article and not any(r['deleted'] and any(c.isalpha() for c in r['text']) for r in b['runs']):
            witness=documentary_notes(raw_text)[0]
            if witness:groups.setdefault(group,[]).append(dict(text=witness,block=index,line=b['line']))
        if not any(r['deleted'] and r['text'].strip() for r in b['runs']):continue
        body,notes,ranges,warnings=documentary_notes(raw_text);m=documentary_unit(body)
        evidence=dict(rawHtml=b['rawHtml'],rawText=raw_text,rawUnitText=raw_text,runs=b['runs'],anchors=b['anchors'],contextTags=b['contextTags'],charRange=[b['start'],b['end']],line=b['line'],block=index)
        editorial=[]
        for note,(a,z) in zip(notes,ranges):
            links=[];offset=0
            for run in b['runs']:
                if run.get('href') and offset<z and offset+len(run['text'])>a and run['href'] not in links:links.append(run['href'])
                offset+=len(run['text'])
            editorial.append(dict(text=note,links=links))
        evidence['editorialNotes']=editorial
        reasons=[];part=m[0] if m else 'penalty' if PENALTY.match(body) else None
        label={'caput':'Caput','penalty':'Pena'}.get(part,m[2] if m else '')
        if part=='item' and paragraph:label=paragraph+' · '+label
        if part=='letter':label=' · '.join(x for x in [paragraph,item,label] if x)
        letter_markers=[match.span() for match in re.finditer(r'(?m)^\s*[a-z]\s*\)',raw_text)]
        if part=='letter' and len(letter_markers)>1:
            label=' · '.join(x for x in [paragraph,item,'Alíneas '+', '.join(raw_text[a:z].strip() for a,z in letter_markers)+' — trecho conjunto da fonte'] if x)
        association_article=article;association_block=article_block;basis='Caput e continuidade estrutural na própria fonte HTML.'
        # A caption immediately preceding a caput belongs to that following article,
        # not to the previous article. Never jump over another normative unit/title.
        short_caption=not m and not PENALTY.match(body) and not re.search(r'[.;:]\s*$',body) and len(body)<250 and (bool(re.search(r'<(?:b|strong)\b|font-weight\s*:\s*(?:bold|[7-9]00)',b['rawHtml'],re.I)) or index>0 and structures[index-1] and bool(re.search(r'<p\b',b['rawHtml'],re.I)))
        if short_caption and not structures[index]:
            next_index=index+1
            while next_index<len(blocks):
                next_body=documentary_notes(''.join(r['text'] for r in blocks[next_index]['runs']))[0]
                if not next_body:next_index+=1;continue
                caption_sibling=not markers[next_index] and not structures[next_index] and len(next_body)<250 and bool(re.search(r'<(?:b|strong)\b|font-weight\s*:\s*(?:bold|[7-9]00)',blocks[next_index]['rawHtml'],re.I))
                if caption_sibling:next_index+=1;continue
                break
            following=markers[next_index] if next_index<len(blocks) else None
            if following and following[0]=='caput' and not structures[next_index] and ('blockquote' not in blocks[next_index]['contextTags'] or native_article_anchor(blocks[next_index],following[1])):
                association_article=('adct-' if adct else '')+following[1];association_block=next_index
                part='rubric';label='Rubrica';basis='Rubrica imediatamente anterior ao caput na fonte, sem unidade normativa intermediária.'
            elif article and following and following[0] in {'paragraph','item','letter'}:
                part='rubric';label='Subtítulo interno do artigo';basis='Subtítulo entre o caput e sua subdivisão na mesma fonte.'
            elif part is None:reasons.append('caption_or_fragment_association_uncertain')
        if structures[index]:reasons.append('supra_article_structure')
        if foreign_quote:reasons.append('quoted_context_without_native_article_evidence')
        if not association_article and not structures[index]:reasons.append('no_documentary_article')
        # Ignore structural labels and editorial notes when inspecting body strike.
        start=len(raw_text)-len(raw_text.lstrip());original_marker=documentary_unit(raw_text.lstrip())
        start+=original_marker[3] if original_marker else 0
        states=[];deleted=[];cursor=0;fragments=[];fragment=[];fragment_start=None
        for run in b['runs']:
            for pos,c in enumerate(run['text'],cursor):
                in_note=any(a<=pos<z for a,z in ranges)
                structural_marker=pos<start or any(a<=pos<z for a,z in letter_markers)
                if not in_note and not structural_marker and (c.isalpha() and c not in 'º°' or c.isdigit()):
                    states.append(run['deleted'])
                    if run['deleted']:deleted.append(c)
                if run['deleted'] and not in_note:
                    if fragment_start is None:fragment_start=pos
                    fragment.append(c)
                elif fragment and (in_note or c.strip()):
                    fragments.append(dict(text=spaces(''.join(fragment)),textRange=[fragment_start,pos]));fragment=[];fragment_start=None
                elif fragment:fragment.append(c)
            cursor+=len(run['text'])
        if fragment:fragments.append(dict(text=spaces(''.join(fragment)),textRange=[fragment_start,len(raw_text)]))
        content=body[m[3]:] if m else PENALTY.sub('',body,count=1)
        if re.fullmatch(r'[\s.:(-]*(?:VETAD[OA]|Revogad[oa])[\s.):;-]*',content,re.I):reasons.append('veto_or_revocation_placeholder')
        if not deleted:reasons.append('no_struck_normative_content')
        if parser.unsupported:reasons.append('unsupported_embedded_css')
        if part is None:part='article';label='Trecho normativo do artigo — subdivisão não identificada'
        if part=='caput' and PENALTY.search(body):part='article';label='Trecho da fonte: caput e pena'
        elif re.search(r'<br\s*/?>\s*(?:<(?:s|strike|span)[^>]*>\s*)*(?:§|[IVXLCDM]+\s*[-–—])',b['rawHtml'],re.I):
            part='article';label='Trecho conjunto da fonte — múltiplas subdivisões'
        complete=bool(states) and all(states)
        if not complete:
            # Preserve only actual struck fragments; never fill intervening current text.
            fragments=[f for f in fragments if re.search(r'[\w]',f['text'].replace('º','').replace('°','')) and not re.fullmatch(r'(?:Art\.?\s*\d+[º°]?|§\s*\d+[º°o]?|[IVXLCDM]+\s*[-–—]?|[a-z]\s*\))\s*[.:;-]?',f['text'])]
            if not fragments:reasons.append('no_struck_normative_content')
            warnings.append('partial_strike_only_documented_fragments')
        else:fragments=[]
        region='original_general_part' if index<cp_boundary else 'approval_decree' if code=='clt' and clt_boundary>=0 and index<clt_boundary else 'adct' if adct else 'main'
        if len(jury)==2 and jury[0]<=index<jury[1]:region='restructured_jury'
        if region=='approval_decree':reasons.append('approval_decree_outside_consolidated_legislation')
        context=dict(articleId=association_article,region=region,group=group,articleBlock=association_block,basis=basis,equivalenceToCurrent='not_established')
        entries.append(dict(id=f'{code}-simple-{digest[:12]}-b{index}',codeId=code,context=context,part=part,unitLabel=label,text=body,notes=notes,extracted=not reasons,reasons=sorted(set(reasons)),warnings=sorted(set(warnings)),fragments=fragments,source=dict(label='Planalto — HTML oficial salvo localmente',document=filename,sha256=digest,url=origin[1],location=f'Linha {b["line"]}, bloco {index}'),evidence=evidence))
    for entry in entries:entry['context']['unstruckCaputs']=groups.get(entry['context']['group'],[])
    return dict(codeId=code,file=filename,sha256=digest,encoding=encoding,unsupportedCss=parser.unsupported,entries=entries)


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
