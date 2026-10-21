"""Offline, conservative preparation of documented previous wording from Planalto HTML.

Reuses the monitor's tag/deletion reader, never its network or capture workflow.
No production writes, inferred validity dates, or automatic legal approval.
"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import re
import unicodedata
from urllib.parse import urlparse

from check_official_sources import OfficialHTML
from import_official import ARTICLE

ROOT = Path(__file__).resolve().parents[1]
FILES = {'cf':'Constituição.html', 'penal':'DEL2848.html', 'cpp':'Del3689.html',
         'clt':'Del5452compilado.html', 'civil':'L10406compilada.html',
         'cpc':'L13105compilada.html', 'licitacoes':'L14133.html',
         'ctn':'L5172COMPILADO.html', 'lep':'L7210.html', 'eca':'L8069.html',
         'cdc':'L8078compilado.html', 'improbidade':'L8429.html',
         'maria-penha':'Lei nº 11.340.html'}
NOTE = re.compile(r'\((?:Redação|Incluíd[oa]|Acrescid[oa]|Alterad[oa]|Revogad[oa]|Vide\b|Vigência\b|Produção de efeitos?\b|Suspens[ao])', re.I)
SENSITIVE = re.compile(r'\b(?:VETAD[OA]|Revogad[oa]|Suspens[ao]|ADIN?|ADPF)\b', re.I)
PARA = re.compile(r'^(?:§\s*(\d+)\s*(?-i:[º°o])?(-[A-Z])?|Parágrafo\s+único)', re.I)
ITEM = re.compile(r'^([IVXLCDM]+)\s*[-–—]')
ITEM_NO_DASH = re.compile(r'^([IVXLCDM]+)\s+(?=[a-záéíóúâêôãõç])')
BARE_NOTE = re.compile(r'\bVide art\.\s*\d+\s*[-–—]\s*ADCT\b', re.I)
LETTER = re.compile(r'^([a-z])\)')
PENALTY = re.compile(r'\bPenas?\s*[-–—:]')


def spaces(value):
    return re.sub(r'\s+', ' ', value).strip()


def decode(raw):
    if raw.startswith((b'\xff\xfe', b'\xfe\xff')):
        encoding = 'utf-16'
    elif raw.startswith(b'\xef\xbb\xbf'):
        encoding = 'utf-8-sig'
    elif match := re.search(br'charset\s*=\s*["\']?\s*([\w-]+)', raw[:8192], re.I):
        encoding = match[1].decode('ascii')
    else:
        try:
            raw.decode('utf-8', errors='strict')
            encoding = 'utf-8'
        except UnicodeDecodeError:
            encoding = 'cp1252'
    return raw.decode(encoding, errors='strict'), encoding


class EvidenceHTML(OfficialHTML):
    """Keep exact decoded text and link offsets on the existing deletion stack.

    No Unicode rewriting: whitespace is normalized only in the final body.
    BR is a whitespace separator, not a complete legal-unit boundary.
    """
    boundaries = OfficialHTML.boundaries - {'br'}

    def __init__(self, source):
        super().__init__()
        self.source = source
        self.offsets = [0]+[m.end() for m in re.finditer('\n', source)]
        self.start = None
        self.anchors = []
        self.link_stack = []
        self.start_location = None
        self.context_tags = []

    def pos(self):
        line, column = self.getpos()
        return self.offsets[line-1]+column

    def handle_starttag(self, tag, attrs):
        super().handle_starttag(tag, attrs)
        attrs = dict(attrs)
        self.link_stack = [item for item in self.link_stack if item[0] <= len(self.stack)]
        if tag in self.boundaries:
            self.start = self.pos()
            self.start_location = self.getpos()
            self.context_tags = [entry[0] for entry in self.stack]
        if attrs.get('id') or attrs.get('name'):
            self.anchors.append(attrs.get('id') or attrs['name'])
        if tag == 'a' and attrs.get('href'):
            self.link_stack.append((len(self.stack), attrs['href']))
        if tag == 'br':
            self.handle_data(' ')

    def handle_endtag(self, tag):
        super().handle_endtag(tag)
        self.link_stack = [item for item in self.link_stack if item[0] <= len(self.stack)]

    def handle_data(self, text):
        if self.stack and self.stack[-1][1]:
            if self.stack[-1][0] == 'style' and 'line-through' in text.lower():
                self.deletion_styles.add(text)
            return
        if self.start is None:
            self.start, self.start_location = self.pos(), self.getpos()
            self.context_tags = [entry[0] for entry in self.stack]
        self.runs.append({'text':text, 'deleted':self.stack[-1][2] if self.stack else False,
                          'href':self.link_stack[-1][1] if self.link_stack else None})

    def flush(self):
        if any(run['text'].strip() for run in self.runs):
            end = self.pos()
            # Include the closing boundary tag when flush was called by its end.
            closing = re.match(r'</(?:p|div|li|tr|h[1-6])\s*>', self.source[end:], re.I)
            if closing:
                end += closing.end()
            self.blocks.append(dict(runs=self.runs, anchors=self.anchors,
                start=self.start, end=end, line=(self.start_location or (1,0))[0],
                contextTags=self.context_tags,
                rawHtml=self.source[self.start:end]))
        self.runs, self.anchors = [], []
        self.start, self.start_location = None, None


def split_notes(raw):
    ranges, notes, cursor = [], [], 0
    while match := NOTE.search(raw, cursor):
        depth = 0
        for i in range(match.start(), len(raw)):
            depth += (raw[i]=='(')-(raw[i]==')')
            if depth == 0:
                ranges.append((match.start(), i+1))
                notes.append(spaces(raw[match.start():i+1]))
                cursor = i+1
                break
        else:
            raise ValueError('incomplete_editorial_note')
    for match in BARE_NOTE.finditer(raw):
        if any(a <= match.start() < b for a,b in ranges):
            continue
        # Explicit editorial cross-reference, never a free-form tail.
        ranges.append((match.start(), match.end()))
        notes.append(spaces(match[0]))
    ordered = sorted(zip(ranges, notes))
    ranges, notes = [r for r,n in ordered], [n for r,n in ordered]
    chars = [c for i,c in enumerate(raw) if not any(a <= i < b for a,b in ranges)]
    return spaces(''.join(chars)), notes, ranges


def unit(text):
    if m := ARTICLE.match(text):
        return 'caput', m[1].replace('.', '')+(m[2] or '').replace('–','-'), 'caput', m.end()
    if m := PARA.match(text):
        return 'paragraph', None, '§ '+m[1]+(m[2] or '') if m[1] else 'Parágrafo único', m.end()
    if m := ITEM.match(text):
        return 'item', None, 'inciso '+m[1], m.end()
    if m := LETTER.match(text):
        return 'letter', None, 'alínea '+m[1], m.end()
    return None


def canonical(value):
    # For duplicate identity only; never changes the exported norm text.
    return unicodedata.normalize('NFC', spaces(value))


def row_key(row):
    part = row['part']
    marker = unit(row['text'])
    label = row.get('unitLabel', '')
    if part == 'caput':
        label = 'caput'
    elif part == 'paragraph' and marker:
        label = marker[2]
    return row['codeId'], row['articleId'], part, label


def inspect_source(code, filename, raw, reader_ids=None):
    source, encoding = decode(raw)
    origin_match = re.search(r'saved from url=\(\d+\)([^\s]+)', source)
    origin = origin_match[1] if origin_match else None
    if not origin or urlparse(origin).hostname not in {'www.planalto.gov.br', 'planalto.gov.br'}:
        raise ValueError('Unexpected source origin')
    parser = EvidenceHTML(source)
    parser.feed(source)
    parser.close()
    parser.flush()
    blocks = parser.blocks
    candidates, excluded = [], []
    start = 0
    if code == 'penal':
        ones = [i for i,b in enumerate(blocks) if (u:=unit(spaces(''.join(r['text'] for r in b['runs'])))) and u[0]=='caput' and u[1]=='1']
        if len(ones)>1:
            start = ones[-1]
            excluded.append(dict(reason='original_general_part_not_mapped', blocksSkipped=start))
    article, parent, inciso, scope, high = None, 'caput', None, '', 0
    stopped = False
    parents = {}
    for index,b in enumerate(blocks[start:], start):
        raw_text = ''.join(r['text'] for r in b['runs'])
        text = spaces(raw_text)
        u = unit(text)
        dashless = ITEM_NO_DASH.match(text) if not u else None
        if dashless and candidates and candidates[-1]['articleId']==article and candidates[-1]['part']=='item' and candidates[-1]['state']=='struck' and candidates[-1]['unitLabel'].endswith('inciso '+dashless[1]):
            u = ('item', None, 'inciso '+dashless[1], dashless.end())
        if code == 'cf' and high >= 250 and text.upper().startswith('ATO DAS DISPOSIÇÕES CONSTITUCIONAIS TRANSITÓRIAS'):
            scope, high, stopped = 'adct-', 0, False
        if u and u[0] == 'caput':
            n = int(re.match(r'\d+', u[1])[0])
            if n < high:
                stopped = True
            high = max(high, n)
            article, parent, inciso = scope+u[1], 'caput', None
            parents = {}
        if not u or not article:
            if article and PENALTY.match(text) and parents.get('paragraph'):
                parents['paragraph']['flags'].append('paragraph_with_separate_penalty')
            continue
        part, _, marker, _ = u
        if part == 'paragraph':
            parent, inciso = marker, None
            parents.pop('item', None)
        elif part == 'item':
            if parents.get('paragraph'):
                parents['paragraph']['flags'].append('unit_has_unrepresented_children')
            inciso = marker
        elif part == 'letter':
            if parents.get('item'):
                parents['item']['flags'].append('unit_has_unrepresented_children')
        label = marker if part in {'caput','paragraph'} else parent+' · '+marker if part=='item' else parent+' · '+str(inciso)+' · '+marker
        flags = []
        if 'blockquote' in b['contextTags']:
            flags.append('quoted_or_indented_container_requires_review')
        if stopped:
            flags.append('numbering_regression_or_later_document_region')
        if reader_ids is not None and article not in reader_ids:
            flags.append('article_not_in_reader')
        if part == 'letter' and inciso is None:
            flags.append('letter_without_explicit_parent_item')
        # A single explicit caput/penalty pair may share a P. Keep offsets;
        # never borrow a penalty's amendment note for the caput.
        leading = len(raw_text)-len(raw_text.lstrip())
        cut = len(raw_text)
        if part == 'caput' and (penalty:=PENALTY.search(raw_text)):
            cut = penalty.start()
            if len(list(PENALTY.finditer(raw_text))) != 1:
                flags.append('multiple_penalties_inside_caput_block')
        raw_unit = raw_text[:cut]
        try:
            body, notes, ranges = split_notes(raw_unit)
        except ValueError as error:
            body, notes, ranges = '', [], []
            flags.append(str(error))
        body_after_marker = body[u[3]:]
        if not body or body_after_marker.count('(')!=body_after_marker.count(')') or not re.search(r'[.;:]$', body):
            flags.append('incomplete_or_undelimited_unit')
        if SENSITIVE.search(raw_text) or re.search(r'\(\s*promulga\w*', raw_text, re.I) or any(re.search(r'\bpromulga\w*', n, re.I) for n in notes):
            flags.append('veto_repeal_suspension_or_judicial_note')
        if re.search(r'[;:]\s*\.$', body):
            flags.append('ambiguous_punctuation_after_note')
        if re.search(r'(?:\n|\r)\s*(?:Art\.?\s*\d|§\s*\d|Parágrafo único|[IVXLCDM]+\s*[-–—]|[a-z]\))', raw_unit[leading+u[3]:]):
            flags.append('multiple_units_in_same_block')
        if re.search(r'[.;:]\s*(?:§\s*\d|Parágrafo único|Art\.\s*\d|[IVXLCDM]+\s*[-–—]|[a-z]\))', body[u[3]:]):
            flags.append('multiple_inline_units')
        if part != 'caput' and PENALTY.search(body):
            flags.append('mixed_unit_and_penalty')
        body_marker = unit(body)
        prefix_end = body_marker[3] if body_marker else 0
        # Prefix offsets are computed against raw_unit, not its whitespace-normalized body.
        raw_marker = unit(raw_unit.lstrip())
        normative_start = leading+(raw_marker[3] if raw_marker else prefix_end)
        letters, notes_details, cursor = [], [], 0
        links_by_note = [set() for _ in ranges]
        for run in b['runs']:
            for j,c in enumerate(run['text'], cursor):
                if normative_start <= j < cut and c.isalpha() and c not in 'º°' and not any(a<=j<z for a,z in ranges):
                    letters.append(run['deleted'])
            if run['href']:
                for k,(a,z) in enumerate(ranges):
                    if cursor < z and cursor+len(run['text']) > a:
                        links_by_note[k].add(run['href'])
            cursor += len(run['text'])
        state = 'struck' if letters and all(letters) else 'unstruck' if letters and not any(letters) else 'mixed'
        if state == 'mixed':
            flags.append('partial_or_non_substantive_strike')
        for note,links in zip(notes, links_by_note):
            notes_details.append(dict(text=note, links=sorted(links)))
        c = dict(codeId=code, articleId=article, part=part, unitLabel=label,
                 text=body, notes=notes, state=state, flags=flags, block=index,
                 evidence=dict(rawHtml=b['rawHtml'], rawText=raw_text, rawUnitText=raw_unit,
                     rawUnitRange=[0,cut], charRange=[b['start'],b['end']], line=b['line'],
                     anchors=b['anchors'], contextTags=b['contextTags'], runs=b['runs'], editorialNotes=notes_details),
                 source=dict(file=filename, sha256=hashlib.sha256(raw).hexdigest(),
                             encoding=encoding, originUrl=origin))
        candidates.append(c)
        if part in {'paragraph','item'}:
            parents[part]=c
    return candidates, excluded, dict(codeId=code, file=filename, sha256=hashlib.sha256(raw).hexdigest(),
        encoding=encoding, origin=origin, blocks=len(blocks), articleIds=sorted({c['articleId'] for c in candidates}),
        candidates=len(candidates), stylesheetStrikeRules=len(parser.deletion_styles))


def prepare_document(code, filename, raw, existing=(), reader_ids=None):
    candidates, excluded, inventory = inspect_source(code, filename, raw, reader_ids)
    if inventory['stylesheetStrikeRules']:
        for c in candidates:
            c['flags'].append('unsupported_stylesheet_deletion_rules')
    groups = defaultdict(list)
    caputs = Counter(c['articleId'] for c in candidates if c['part']=='caput')
    existing_keys = defaultdict(set)
    orders = Counter()
    for row in existing:
        existing_keys[row_key(row)].add(canonical(row['text']))
        if row['codeId']==code:
            orders[row['articleId']] = max(orders[row['articleId']], row['sequence']['order'])
    for c in candidates:
        groups[row_key(c)].append(c)
    records, duplicate_evidence = [], []
    for key, versions in groups.items():
        reasons = sorted({f for c in versions for f in c['flags']})
        if key[2]!='caput' and caputs[key[1]]!=1:
            reasons.append('internal_unit_under_multiple_caputs')
        states = [c['state'] for c in versions]
        substantive_old = 'struck' in states
        if not substantive_old:
            continue
        if len(versions)<2 or states != ['struck']*(len(versions)-1)+['unstruck']:
            reasons.append('no_clear_prior_and_replacement_sequence')
        if any(not any(re.match(r'\(Redação dada',note,re.I) for note in c['notes']) for c in versions[1:]):
            reasons.append('replacement_without_explicit_amendment_note')
        texts = [canonical(c['text']) for c in versions]
        if len(set(texts))!=len(texts):
            reasons.append('same_normative_body_different_documentary_entries')
        new_texts = set(texts)-existing_keys[key]
        if existing_keys[key] and new_texts:
            reasons.append('existing_unit_with_new_text_requires_review')
        if reasons:
            excluded.append(dict(articleId=key[1], part=key[2], unitLabel=key[3],
                reasons=sorted(set(reasons)), blocks=[c['block'] for c in versions],
                evidence=[c['evidence'] for c in versions]))
            continue
        for c in versions:
            if canonical(c['text']) in existing_keys[key]:
                duplicate_evidence.append(dict(existingUnit=list(key), block=c['block'], source=c['source'], evidence=c['evidence']))
                continue
            orders[c['articleId']] += 1
            amendment = next((n for n in c['evidence']['editorialNotes'] if re.match(r'\(Redação dada',n['text'],re.I)), None)
            url = c['source']['originUrl']
            basis = 'Mesma unidade explicitamente identificada no HTML, com corpo anterior riscado e substituta acompanhada de nota própria de redação; sequência documental, sem inferência de vigência.'
            records.append(dict(id=f"{code}-{c['articleId']}-html-{c['source']['sha256'][:12]}-b{c['block']}",
                codeId=code, articleId=c['articleId'], part=c['part'],
                unitLabel='Caput' if c['part']=='caput' else c['unitLabel'], text=c['text'],
                sequence=dict(order=orders[c['articleId']], basis=basis),
                reference=amendment['text'] if amendment else None, notes=c['notes'],
                source=dict(label='Planalto — HTML oficial salvo localmente',document=filename,
                    sha256=c['source']['sha256'], encoding=c['source']['encoding'], originUrl=url,
                    url=url, location=f"Linha {c['evidence']['line']}, bloco {c['block']}; âncoras {c['evidence']['anchors']}"),
                review=dict(status='pending'), wording=dict(status='previous' if c['state']=='struck' else 'current_candidate', basis=basis),
                evidence=c['evidence']))
    validations=[]
    for row in existing:
        if row['codeId']!=code:
            continue
        hits=[c for c in candidates if row_key(c)==row_key(row) and c['text']==row['text']]
        text_hits=[c for c in candidates if c['text']==row['text']]
        validations.append(dict(id=row['id'], articleId=row['articleId'], part=row['part'],
            result='exact_text_and_unit' if hits else 'text_only_wrong_or_unresolved_unit' if text_hits else 'not_exact',
            expectedNature=row['wording']['status'],
            observedStates=[c['state'] for c in hits], blocks=[c['block'] for c in hits],
            natureMatches=bool(hits) and all(c['state']==('struck' if row['wording']['status']=='previous' else 'unstruck') for c in hits),
            candidateFlags=[c['flags'] for c in hits]))
    inventory.update(records=len(records), recordArticles=len({r['articleId'] for r in records}),
                     duplicateEvidence=len(duplicate_evidence), excludedGroups=len(excluded))
    inventory['readerArticlesNotIdentified'] = sorted(set(reader_ids or ())-set(inventory['articleIds']))
    inventory['readerArticleIdsIdentified'] = sorted(set(reader_ids or ())&set(inventory['articleIds']))
    inventory['foreignOrUnknownArticleIds'] = sorted(set(inventory['articleIds'])-set(reader_ids or ()))
    inventory['warnings'] = []
    if inventory['stylesheetStrikeRules']:
        inventory['warnings'].append('unsupported_stylesheet_deletion_rules')
    if code in {'cf','cpp','cpc'} and reader_ids:
        observed_max=max((int(re.match(r'\d+',a)[0]) for a in inventory['articleIds'] if not a.startswith('adct-')), default=0)
        expected_max=max(int(re.match(r'\d+',a)[0]) for a in reader_ids if not a.startswith('adct-'))
        if observed_max < expected_max:
            inventory['warnings'].append(f'saved_document_stops_at_article_{observed_max}_reader_reaches_{expected_max}')
    return dict(records=records, excluded=excluded, duplicateEvidence=duplicate_evidence,
                validation=validations, inventory=inventory)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sources',type=Path,default=ROOT/'HTML')
    parser.add_argument('--existing',type=Path,default=ROOT/'experiments/html-history/existing-records.json')
    parser.add_argument('--reader-ids',type=Path,default=ROOT/'experiments/html-history/reader-ids.json')
    parser.add_argument('--output',type=Path,default=ROOT/'experiments/html-history/results')
    parser.add_argument('--preview-fixture',action='store_true',help='Update only the isolated HTML preview fixture after reference validation.')
    args=parser.parse_args()
    if not any(args.output.resolve().is_relative_to(ROOT/f) for f in ('experiments/html-history','test-results')):
        raise ValueError('Output must remain experimental, outside public data.')
    existing=json.loads(args.existing.read_text(encoding='utf-8'))
    reader=json.loads(args.reader_ids.read_text(encoding='utf-8'))
    results=[]
    for code,name in FILES.items():
        path=args.sources/name
        raw=path.read_bytes()
        result=prepare_document(code,name,raw,existing,set(reader[code]))
        assert hashlib.sha256(path.read_bytes()).hexdigest()==result['inventory']['sha256']
        results.append(result)
    args.output.mkdir(parents=True,exist_ok=True)
    for key in ('records','excluded','duplicateEvidence','validation'):
        (args.output/(key+'.json')).write_text(json.dumps([r for result in results for r in result[key]],ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (args.output/'inventory.json').write_text(json.dumps([r['inventory'] for r in results],ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if args.preview_fixture:
        validation=[r for result in results for r in result['validation']]
        if len(validation)!=len(existing) or any(v['result']!='exact_text_and_unit' or not v['natureMatches'] for v in validation):
            raise ValueError('Reference validation failed: preview fixture was not changed; inspect validation.json.')
        records=[r for result in results for r in result['records']]
        identities=[(*row_key(r),canonical(r['text'])) for r in [*existing,*records]]
        if len(identities)!=len(set(identities)):
            raise ValueError('Duplicate unit identity: preview fixture was not changed.')
        (ROOT/'tests/fixtures/legislative-history-html.json').write_text(json.dumps({'records':records},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    file_hashes = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in args.output.glob('*.json') if p.name!='manifest.json'}
    manifest=dict(schemaVersion=1,publicationAllowed=False,
        extractorSha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        existingRecordsSha256=hashlib.sha256(args.existing.read_bytes()).hexdigest(),
        readerIdsSha256=hashlib.sha256(args.reader_ids.read_bytes()).hexdigest(),
        files=file_hashes,sources={r['inventory']['file']:r['inventory']['sha256'] for r in results})
    (args.output/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps([dict(codeId=r['inventory']['codeId'],articlesIdentified=len(r['inventory']['articleIds']),
                          recordArticles=r['inventory']['recordArticles'],records=r['inventory']['records'],
                          warnings=r['inventory']['warnings']) for r in results],ensure_ascii=False))


if __name__=='__main__':
    main()
