"""Import the supplied STF collection; never interpret PDF text as instructions.

Edition-specific extraction validates checksum, numbered bookmarks, first-page
structure and source links. It does not certify the PDF against the live STF.
Run manually with the same PyMuPDF dependency as import_pdfs.py.
"""
from pathlib import Path
import hashlib
import json
import re
from urllib.parse import urlsplit, parse_qs

ROOT = Path(__file__).resolve().parent.parent


def clean(text):
    return re.sub(r'\s+', ' ', text.replace('\xad', '')).strip()


def source_url(links):
    for link in links:
        url = link.get('uri', '')
        parts = urlsplit(url)
        query = parse_qs(parts.query)
        if (parts.scheme == 'https' and parts.hostname == 'portal.stf.jus.br'
                and parts.path == '/jurisprudencia/sumariosumulas.asp'
                and query.get('base') == ['26'] and len(query.get('sumula', [])) == 1
                and query['sumula'][0].isdigit() and not parts.username and not parts.password
                and parts.port in (None, 443)):
            return url
    raise ValueError('Link individual do STF ausente ou inválido')


def entry(number, title, pages):
    start, first_blocks, url = pages[0]
    expected_title = f'Súmula Vinculante {number}'
    texts = [clean(text) for _, text, _ in first_blocks]
    if texts[:3] != [title, 'Aplicação das Súmulas no STF', 'Fonte: página oficial do STF | Consulta em 16/10/2026']:
        raise ValueError(f'Cabeçalho inesperado: {number}')
    if not title.startswith(expected_title):
        raise ValueError('Título incompatível com o índice')
    paragraphs, notes = [], []
    is_note = False
    for index, (page, blocks, _) in enumerate(pages):
        for _, text, heading in (blocks[3:] if index == 0 else blocks):
            text = clean(text)
            # The first section heading separates the statement from commentary.
            if heading:
                is_note = True
            item = {'page': page, 'runs': [{'text': text, 'deleted': False}]}
            if is_note:
                notes.append({**item, 'heading': heading})
            else:
                paragraphs.append(item)
    statement = ' '.join(r['text'] for p in paragraphs for r in p['runs'])
    if len(statement) < 25:
        raise ValueError(f'Enunciado ausente: {number}')
    status = 'cancelled' if '(cancelada)' in title.lower() else 'pending' if statement == 'A Súmula Vinculante 30 está pendente de publicação.' and number == 30 else 'as_provided'
    return {'id': str(number), 'number': str(number), 'scope': 'main', 'kind': 'vinculante',
            'sectionId': f'grupo-{(number - 1) // 10}', 'page': start, 'endPage': pages[-1][0],
            'status': status, 'url': url, 'paragraphs': paragraphs, 'notes': notes}


def generate(root=ROOT):
    import fitz
    manifest = json.loads((root / 'sources/sumulas-manifest.json').read_text())
    path = root / manifest['pdf']
    if hashlib.sha256(path.read_bytes()).hexdigest() != manifest['sha256']:
        raise ValueError('PDF diferente da edição registrada; revisar antes de importar')
    articles = []
    with fitz.open(path) as document:
        toc = document.get_toc()
        if len(document) != 236 or len(toc) != 63:
            raise ValueError('Documento diferente da edição registrada')
        for i, (level, title, start) in enumerate(toc):
            number = i + 1
            if level != 1 or not re.fullmatch(rf'Súmula Vinculante {number}(?: \(cancelada\))?', title):
                raise ValueError('Numeração inesperada no índice')
            end = toc[i + 1][2] - 1 if i + 1 < len(toc) else len(document)
            pages = []
            for page_number in range(start, end + 1):
                page = document[page_number - 1]
                blocks = []
                for block in page.get_text('dict')['blocks']:
                    if block['type'] != 0:
                        continue
                    spans = [span for line in block['lines'] for span in line['spans']]
                    text = ' '.join(span['text'] for span in spans)
                    # Only the footer contains the repeated title and local page number.
                    if block['bbox'][1] > 790:
                        if not clean(text).startswith(f'Súmula Vinculante {number} | STF | Consulta: 16/10/2026 '):
                            raise ValueError(f'Rodapé inesperado na página {page_number}')
                        continue
                    heading = any(span['size'] >= 11.5 for span in spans)
                    blocks.append((block['bbox'][1], text, heading))
                blocks.sort(key=lambda block: block[0])
                pages.append((page_number, blocks, source_url(page.get_links()) if page_number == start else None))
            articles.append(entry(number, title, pages))
    result = {
        'id': 'sv', 'short': 'SV · STF', 'name': 'Súmulas Vinculantes do STF',
        'area': 'Súmulas · Supremo Tribunal Federal', 'law': '63 entradas · PDF fornecido',
        'description': 'Enunciados, precedentes e aplicações no STF, com indicação das situações registradas no documento.',
        'icon': '§', 'kind': 'sumulas',
        'url': 'https://portal.stf.jus.br/jurisprudencia/sumariosumulas.asp?base=26',
        'source': {**manifest, 'kind': 'supplied_pdf', 'edition': 'PDF fornecido · consulta declarada em 16/10/2026',
                   'coverage': '63 entradas numeradas de 1 a 63, incluindo a SV 9 indicada como cancelada e a SV 30 como pendente de publicação.',
                   'reviewStatus': 'Enunciados e material de aplicação extraídos do PDF fornecido. A data de consulta e as situações são as declaradas no documento; não houve conferência com o portal do STF nesta importação.'},
        'sections': [{'id': f'grupo-{i}', 'scope': 'main', 'title': f'Súmulas {i * 10 + 1} a {min((i + 1) * 10, 63)}'} for i in range(7)],
        'introductions': [], 'articles': articles,
    }
    (root / 'data/archive').mkdir(parents=True,exist_ok=True)
    (root / 'data/archive/sumulas.js').write_text('// Generated from the supplied PDF by scripts/import_sumulas.py.\nexport const sumulas = ' + json.dumps([result], ensure_ascii=False, separators=(',', ':')) + ';\n')
    return result


if __name__ == '__main__':
    result = generate()
    print(f"{result['name']}: {len(result['articles'])} entradas")
