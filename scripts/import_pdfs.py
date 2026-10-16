"""Import the six supplied PDFs without treating document text as instructions.

Keep deleted text marked, retain amendment notes, and namespace ADCT articles.
The PDFs and manifest remain the evidence; extraction does not certify currency.
Requires PyMuPDF. Run from any directory: python3 scripts/import_pdfs.py.
"""
from pathlib import Path
from collections import Counter
import hashlib
import json
import re
import fitz

ROOT = Path(__file__).resolve().parent.parent
FILES = {
    'civil': ('L10406compilada.pdf', 2046),
    'penal': ('DEL2848compilado.pdf', 361),
    'cpc': ('L13105.pdf', 1072),
    'cdc': ('L8078compilado.pdf', 119),
    'ctn': ('L5172COMPILADO.pdf', 218),
    'cf': ('cf88_69ed.pdf', 250),
}
ARTICLE = re.compile(r'^Art\.?\s*(\d+(?:\.\d{3})*)(?:\s*[º°o])?((?:[-–][A-Z]{1,2}(?=[.\s:\-–]))*)\s*[.:-]?\s*')
RANGE = re.compile(r'^Arts?\.\s*(\d+(?:\.\d{3})*)\.?\s+a\s+(\d+(?:\.\d{3})*)\.?\s*')
HEADING = re.compile(r'^(?:(?:PARTE)\s+(?:GERAL|ESPECIAL|[IVX]+)\b|LIVRO\s+(?:[IVXLCDM]+|PRIMEIRO|SEGUNDO|TERCEIRO|COMPLEMENTAR)\b|(?:TÍTULO|CAPÍTULO|SEÇÃO|SUBSEÇÃO)\s+(?:[IVXLCDM]+|ÚNIC[OA])\b|DISPOSIÇÃO PRELIMINAR\b|DISPOSIÇÕES (?:FINAIS|GERAIS|TRANSITÓRIAS)\b)', re.I)
UNIT = re.compile(r'^(?:§|Parágrafo\s+único|[IVXLCDM]+\s*[-–—]|[a-z]\))')

def clean(text):
    return re.sub(r'\s+', ' ', text.replace('\xad', '').replace('\ufeff', '').replace('\x03', '').replace('\uf0e3', '').replace('\uf0a3', '')).strip()

def page_lines(page, constitution=False):
    """Use original PDF lines; horizontal rules through glyph middles are deletions.

    Hyperlink underlines lie near the baseline and are explicitly excluded.
    Run geometry uses each character so mixed deleted/live lines stay distinct.
    """
    rules = [d['rect'] for d in page.get_drawings()
             if d['rect'].height <= 1.7 and d['rect'].width > 1]
    out = []
    for block in page.get_text('rawdict')['blocks']:
        for line in block.get('lines', []):
            x0, y0, x1, y1 = line['bbox']
            if y0 < (47 if constitution else 26) or y1 > page.rect.height - (24 if constitution else 28):
                continue
            runs = []
            sizes = []
            for span in line['spans']:
                sizes.append(span['size'])
                sb = fitz.Rect(span['bbox'])
                span_rules = [r for r in rules if .32 < (r.y0 - sb.y0) / max(sb.height, 1) < .68]
                for char in span['chars']:
                    c = char['c']
                    if c in '\uf0e3\uf0a3\ufeff\x03':
                        continue
                    box = fitz.Rect(char['bbox'])
                    middle = (box.x0 + box.x1) / 2
                    # An underline below ordinary text may cross a superscript.
                    # Do not misclassify ordinal markers as deleted provisions.
                    struck = not (span['flags'] & 1) and c not in 'º°' and any(r.x0 - .5 <= middle <= r.x1 + .5 for r in span_rules)
                    if runs and runs[-1]['deleted'] == struck:
                        runs[-1]['text'] += c
                    else:
                        runs.append({'text': c, 'deleted': struck})
            text = clean(''.join(r['text'] for r in runs))
            if not text or text.startswith('https://') or re.fullmatch(r'\d+/\d+', text):
                continue
            out.append({'text': text, 'runs': runs, 'page': page.number + 1,
                        'x0': x0, 'x1': x1, 'y0': y0, 'y1': y1,
                        'size': max(sizes, default=10), 'width': page.rect.width,
                        'block': block.get('number'),
                        'startsBold': next((bool(s['flags'] & 16) for s in line['spans'] if clean(''.join(c['c'] for c in s['chars']))), False)})
    return sorted(out, key=lambda l: (round(l['y0'], 1), l['x0']))

def merge_runs(target, runs, space=True):
    if target and space:
        target[-1]['text'] += ' '
    for run in runs:
        text = re.sub(r'\s+', ' ', run['text'].replace('\xad', ''))
        if not text:
            continue
        if target and target[-1]['deleted'] == run['deleted']:
            target[-1]['text'] += text
        else:
            target.append({'text': text, 'deleted': run['deleted']})

def paragraph_text(p):
    return clean(''.join(r['text'] for r in p['runs']))

def extract(id, filename, final):
    path = ROOT / 'sources' / (id + '.pdf')
    doc = fitz.open(path)
    is_cf = id == 'cf'
    lines = []
    for page in doc:
        # The edition bookmarks identify the Constitution, ADCT, then amendments.
        if is_cf and not 7 <= page.number < 193:
            continue
        lines.extend(page_lines(page, is_cf))
    articles, introductions, sections = [], [], []
    hierarchy = {}
    current = None
    paragraph = None
    previous = None
    scope = 'main'
    stopped = False
    heading = False
    high_water = 0
    stats = Counter()
    preamble = []
    unassigned = []
    rubric = []

    def new_section():
        title = ' › '.join(hierarchy.values()) or ('ADCT' if scope == 'adct' else 'Texto da legislação')
        if not sections or sections[-1]['title'] != title or sections[-1]['scope'] != scope:
            sections.append({'id': str(len(sections)), 'title': title, 'scope': scope})
        return sections[-1]['id']

    for line_index, line in enumerate(lines):
        text = line['text']
        if is_cf and line['page'] >= 143 and scope != 'adct':
            scope, current, paragraph, hierarchy = 'adct', None, None, {}
            stopped, high_water, heading = False, 0, False
        if stopped:
            continue
        # Signatures and the Civil Code's appended table of contents are not articles.
        if current and (text.startswith('Brasília,') or text.startswith('Rio de Janeiro,') or
                        text.startswith('Este texto não substitui')):
            stopped = True
            continue
        range_match = RANGE.match(text)
        match = range_match or ARTICLE.match(text)
        if match:
            base = int(match[1].replace('.', ''))
            number = str(base) + ('' if range_match else re.sub(r'\s+', '', match[2]).replace('–', '-'))
            key = ('adct-' if scope == 'adct' else '') + number
            # Lower article numbers inside an amendment/quotation belong to that
            # containing article, never to a new article of this code.
            if (base >= high_water or (current and key == current['id'])) and base <= (999 if scope == 'adct' else final):
                high_water = base
                heading = False
                if current and key == current['id']:
                    stats['repeatedCaput'] += 1
                else:
                    current = {'id': key, 'number': number, 'scope': scope,
                               'sectionId': new_section(), 'page': line['page'], 'paragraphs': []}
                    if rubric:
                        current['title'] = clean(' '.join(rubric))
                        rubric = []
                    if range_match:
                        current['rangeEnd'] = int(range_match[2].replace('.', ''))
                        high_water = current['rangeEnd']
                    articles.append(current)
                paragraph = None
            else:
                match = None
        centered = abs((line['x0'] + line['x1']) / 2 - line['width'] / 2) < 32
        if not match and HEADING.match(text) and (centered or text.split()[0].upper() in ['SEÇÃO', 'SUBSEÇÃO']):
            # Structural headings are always standalone, outside article paragraphs.
            token = text.split()[0].upper()
            levels = {'PARTE': 0, 'LIVRO': 1, 'TÍTULO': 2, 'CAPÍTULO': 3, 'SEÇÃO': 4, 'SUBSEÇÃO': 5}
            level = levels.get(token, 3)
            hierarchy = {k: v for k, v in hierarchy.items() if k < level}
            hierarchy[level] = text
            heading = level
            current, paragraph = None, None
            rubric = []
            previous = line
            continue
        if heading is not False and not match and not UNIT.match(text):
            if centered or text.startswith(('(Redação', '(Incluído', '(Vide', '(Vigência')):
                hierarchy[heading] += ' — ' + text
                previous = line
                continue
            heading = False
        is_rubric = id == 'penal' and not match and line['startsBold'] and len(text) < 250 and not UNIT.match(text) and not text.startswith('(')
        if is_rubric:
            next_article = False
            for later in lines[line_index + 1:line_index + 9]:
                if ARTICLE.match(later['text']):
                    next_article = True
                    break
                if later['startsBold'] or later['text'].startswith('('):
                    continue
                break
            if next_article or current is None:
                rubric.append(text)
                current, paragraph = None, None
                previous = line
                continue
        if not current:
            if id == 'penal' and articles and not UNIT.match(text):
                rubric.append(text)
            elif is_cf and scope == 'main' and not articles and (text == 'PREÂMBULO' or preamble):
                if text != 'PREÂMBULO':
                    raw = ''.join(r['text'] for r in line['runs']).strip()
                    if preamble and preamble[-1].endswith('\xad'):
                        preamble[-1] = preamble[-1][:-1] + raw
                    else:
                        preamble.append(raw)
                elif not preamble:
                    preamble.append('')
            elif articles and text != 'ATO DAS DISPOSIÇÕES CONSTITUCIONAIS TRANSITÓRIAS':
                unassigned.append({'page': line['page'], 'text': text})
            continue
        starts_unit = bool(UNIT.match(text))
        same_page = previous and previous['page'] == line['page']
        gap = line['y0'] - previous['y1'] if same_page else 0
        # PDF print paragraphs have a vertical gap; the Câmara edition uses
        # indents and explicit provision labels at ordinary line spacing.
        separate = paragraph is None or match or starts_unit or is_rubric or (same_page and gap > 3.2)
        if separate:
            paragraph = {'runs': [], 'page': line['page']}
            if is_rubric:
                paragraph['kind'] = 'rubric'
            current['paragraphs'].append(paragraph)
        # Soft hyphens inserted by the edition disappear without a word break.
        soft_join = previous and ''.join(r['text'] for r in previous['runs']).rstrip().endswith('\xad')
        merge_runs(paragraph['runs'], line['runs'], space=bool(paragraph['runs']) and not soft_join)
        previous = line

    for article in articles:
        article['text'] = '\n'.join(paragraph_text(p) for p in article['paragraphs'])
    if preamble:
        introductions.append({'title': 'Preâmbulo', 'text': clean(' '.join(preamble)), 'page': 8})
    source = {'filename': filename, 'pdf': 'sources/' + id + '.pdf', 'pages': len(doc),
              'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
              'importedAt': '2026-10-15',
              'edition': 'Câmara dos Deputados · 69ª edição, 2026 · até a EC 138/2025' if is_cf else 'PDF do Planalto · impressão de 15/10/2026',
              'coverage': 'Texto constitucional e ADCT. Emendas e tratados anexos disponíveis no PDF original.' if is_cf else 'Articulado extraído do PDF fornecido; notas e redações riscadas preservadas.',
              'reviewStatus': 'Extração automatizada; vigência e alterações posteriores não conferidas.'}
    ids = [a['id'] for a in articles]
    if len(set(ids)) != len(ids):
        raise ValueError(f'Duplicate article IDs: {id}')
    for n in range(1, final + 1):
        covered = any(a['scope'] == 'main' and int(a['number'].split('-')[0]) <= n <= a.get('rangeEnd', int(a['number'].split('-')[0])) and '-' not in a['number'] for a in articles)
        if str(n) not in ids and not covered:
            stats['missingBaseArticles'] += 1
    summary = {'articles': len(articles), 'sections': len(sections),
               'deletedRuns': sum(r['deleted'] for a in articles for p in a['paragraphs'] for r in p['runs']),
               'scopeCounts': dict(Counter(a['scope'] for a in articles)),
               'lastArticle': articles[-1]['id'], **stats}
    summary['unassignedLines'] = unassigned
    if stats['missingBaseArticles'] or unassigned:
        raise ValueError(f'Incomplete extraction for {id}: {summary}')
    print(id, summary)
    return {'articles': articles, 'sections': sections, 'introductions': introductions, 'source': source}, summary

def main():
    imported, report = {}, {}
    for id, (filename, final) in FILES.items():
        imported[id], report[id] = extract(id, filename, final)
    # Store each text once; the browser reconstructs searchable plain text from runs.
    payload = {id: {**data, 'articles': [{k: v for k, v in a.items() if k != 'text'} for a in data['articles']]}
               for id, data in imported.items()}
    (ROOT / 'data/archive').mkdir(parents=True,exist_ok=True)
    (ROOT / 'data/archive/legislation.js').write_text('export const imported = ' + json.dumps(payload, ensure_ascii=False, separators=(',', ':')) + ';\n')
    (ROOT / 'sources' / 'manifest.json').write_text(json.dumps({id: data['source'] for id, data in imported.items()}, ensure_ascii=False, indent=2) + '\n')
    (ROOT / 'sources' / 'import-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')

if __name__ == '__main__':
    main()
