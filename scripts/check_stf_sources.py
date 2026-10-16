"""Collect the STF index and every listed binding precedent, then propose a reader.

Public HTML is data, never executable instructions. A partial capture, ambiguous
structure, missing number or suspect truncation blocks every candidate write.
The supplied PDF stays immutable. No automatic merge or deployment.
"""
from datetime import datetime, timezone
from hashlib import sha256
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit, parse_qs, urlencode
import argparse
import copy
import json
import re
import sys
import time

from check_official_sources import parse_html, tidy
from import_official import load_js, version_signature
from official_http import fetch, check_url

ROOT = Path(__file__).resolve().parent.parent
HOSTS = frozenset({'portal.stf.jus.br', 'www.stf.jus.br'})
INDEX = 'https://portal.stf.jus.br/jurisprudencia/sumariosumulas.asp?base=26'
CONVERTER = 1
MAX_ENTRIES = 300
SECTION = re.compile(r'^(?:Precedentes?\s+Representativos?|Jurisprudência\s+selecionada|Teses?\s+de\s+Repercussão\s+Geral|Observaç(?:ão|ões)|Data de publicação do enunciado\s*:)', re.I)
END = re.compile(r'^Para (?:informações adicionais|pesquisar menções a esta súmula)', re.I)


def digest(value):
    return sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def individual_url(value):
    url = urljoin(INDEX, value)
    check_url(url, HOSTS)
    parts = urlsplit(url)
    query = parse_qs(parts.query)
    if (parts.hostname != 'portal.stf.jus.br' or parts.path.lower() != '/jurisprudencia/sumariosumulas.asp'
            or query.get('base') != ['26'] or len(query.get('sumula', [])) != 1
            or not query['sumula'][0].isdigit()):
        raise ValueError('Link diferente da coleção de súmulas vinculantes do STF')
    return INDEX + '&' + urlencode({'sumula': query['sumula'][0]})


def decode(raw, encoding=None):
    if encoding:
        return raw.decode(encoding, errors='strict')
    match = re.search(br'charset\s*=\s*["\']?\s*([\w-]+)', raw[:8192], re.I)
    if match:
        codec = match[1].decode('ascii')
        return raw.decode('cp1252' if codec.lower() == 'iso-8859-1' else codec, errors='strict')
    try:
        return raw.decode('utf-8', errors='strict')
    except UnicodeDecodeError:
        return raw.decode('cp1252', errors='strict')


class IndexLinks(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.current = None
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in {'script', 'style', 'noscript'}:
            self.skip += 1
        if tag == 'a' and not self.skip:
            self.current = [attrs.get('href', ''), []]

    def handle_data(self, data):
        if self.current is not None and not self.skip:
            self.current[1].append(data)

    def handle_endtag(self, tag):
        if tag == 'a' and self.current is not None:
            self.links.append((self.current[0], tidy(''.join(self.current[1])).strip()))
            self.current = None
        if tag in {'script', 'style', 'noscript'}:
            self.skip = max(0, self.skip - 1)


def parse_index(raw, required, encoding=None):
    parser = IndexLinks()
    parser.feed(decode(raw, encoding))
    result, reverse = {}, {}
    known_urls = {individual_url(a['url']): int(a['number']) for a in required}
    for href, label in parser.links:
        try:
            url = individual_url(href)
        except ValueError:
            continue
        match = re.fullmatch(r'(?:Súmula\s+Vinculante\s*(?:n[º°o.]?\s*)?)?(\d+)(?:\s*\([^)]*\))?', label, re.I)
        number = int(match[1]) if match else known_urls.get(url)
        if number is None:
            raise ValueError('Link do STF sem número reconhecível; revisar o índice')
        if not 1 <= number <= MAX_ENTRIES or (number in result and result[number] != url) or (url in reverse and reverse[url] != number):
            raise ValueError('Numeração ou links ambíguos no índice')
        result[number], reverse[url] = url, number
    if not result or set(result) != set(range(1, max(result) + 1)):
        raise ValueError('Índice vazio ou incompleto; nenhuma proposta preparada')
    if not {int(a['number']) for a in required} <= set(result):
        raise ValueError('Súmulas já conhecidas ausentes do índice; revisar manualmente')
    return dict(sorted(result.items()))


def block_text(runs):
    return ''.join(run['text'] for run in runs).strip()


def parse_item(raw, number, url, previous=None, encoding=None):
    document = parse_html(raw, encoding)
    if document.get('deletion_styles'):
        raise ValueError('Estilos de texto riscado exigem revisão do extrator')
    blocks = document['blocks']
    title = re.compile(rf'^Súmula\s+Vinculante\s*(?:n[º°o.]?\s*)?{number}(?:\s*\((?:cancelada|suspensa)\))?$', re.I)
    candidates = []
    for start, runs in enumerate(blocks):
        heading = block_text(runs)
        if not title.fullmatch(heading):
            continue
        paragraphs, notes = [], []
        in_notes, ended = False, False
        for block in blocks[start + 1:]:
            text = block_text(block)
            if END.match(text):
                ended = True
                break
            if re.match(r'^Súmula Vinculante\s+\d+', text, re.I) and not in_notes:
                # Navigation titles are not article content.
                break
            if text.casefold() in {'aplicação das súmulas no stf', 'enunciado', 'texto do enunciado'}:
                continue
            is_heading = bool(SECTION.match(text))
            in_notes = in_notes or is_heading
            paragraph = {'runs': copy.deepcopy(block)}
            (notes if in_notes else paragraphs).append({**paragraph, 'heading': is_heading} if in_notes else paragraph)
        statement = ' '.join(block_text(p['runs']) for p in paragraphs)
        pending = bool(re.fullmatch(r'A Súmula Vinculante 30 está pendente de publicação\.', statement, re.I)) and number == 30
        if len(statement) < 25 or len(statement) > 8000 or (not pending and (not ended or not notes)):
            continue
        if previous:
            old_length = sum(len(block_text(p['runs'])) for p in previous.get('notes', []))
            new_length = sum(len(block_text(p['runs'])) for p in notes)
            if old_length > 500 and new_length < old_length * .6:
                continue
        status = 'pending' if pending else ('cancelled' if '(cancelada)' in heading.casefold() else ('suspended' if '(suspensa)' in heading.casefold() else 'as_provided'))
        if previous and previous.get('status') == 'cancelled' and status != 'cancelled':
            continue
        candidates.append({'id': str(number), 'number': str(number), 'scope': 'main', 'kind': 'vinculante',
                           'sectionId': f'grupo-{(number - 1) // 10}', 'status': status, 'url': url,
                           'paragraphs': paragraphs, 'notes': notes})
    unique = {digest(candidate): candidate for candidate in candidates}
    if len(unique) != 1:
        raise ValueError(f'SV {number}: conteúdo ausente, truncado ou ambíguo; revisar a estrutura da fonte')
    return next(iter(unique.values()))


def version(article):
    if article is None:
        return None
    statuses = {'cancelled': 'Cancelada', 'pending': 'Pendente de publicação', 'suspended': 'Suspensa', 'as_provided': 'Sem indicação especial no título da fonte'}
    notes = article.get('notes', [])
    return {'title': 'Situação registrada: ' + statuses[article['status']],
            'paragraphs': copy.deepcopy(article['paragraphs']) +
                          ([{'runs': [{'text': 'Precedentes, jurisprudência e observações', 'deleted': False}]}] +
                           [{'runs': copy.deepcopy(p['runs'])} for p in notes] if notes else [])}


def make_event(previous, candidate, existing):
    source = candidate['source']
    old_source = previous['source'] if previous else None
    if old_source and old_source['sha256'] == source['sha256'] and old_source.get('converterVersion') == CONVERTER:
        return None
    first = previous is None
    event_id = digest({'code': 'sv', 'from': old_source['sha256'] if old_source else None,
                       'to': source['sha256'], 'converter': CONVERTER, 'capturedAt': source['capturedAt']})
    if any(e['id'] == event_id for e in existing):
        return None
    changes = []
    if previous:
        before = {a['id']: a for a in previous['articles']}
        for article in candidate['articles']:
            old = before.get(article['id'])
            if version_signature(version(old)) != version_signature(version(article)):
                changes.append({'articleId': article['id'], 'number': article['number'], 'scope': 'main',
                                'kind': 'vinculante', 'type': 'added' if old is None else 'changed',
                                'before': version(old), 'after': version(article)})
    return {'id': event_id, 'codeId': 'sv', 'kind': 'baseline' if first else ('processing' if old_source['sha256'] == source['sha256'] else ('text' if changes else 'source')),
            'capturedAt': source['capturedAt'], 'sourceUrl': INDEX,
            'fromVersion': old_source['sha256'] if old_source else None, 'toVersion': source['sha256'], 'changes': changes}


def save_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def run(root=ROOT, fetcher=None, sleeper=time.sleep, now=None):
    root = Path(root)
    run_dir = root / 'monitor/run/stf'
    run_dir.mkdir(parents=True, exist_ok=True)
    stamp = now or datetime.now(timezone.utc).isoformat()
    pdf = load_js(root / 'data/archive/sumulas.js', 'sumulas')[0]
    current_list = load_js(root / 'data/official/sumulas.js', 'officialSumulas')
    previous = current_list[0] if current_list else None
    history = load_js(root / 'data/history/sumulas.js', 'sumulaUpdates')
    if not isinstance(history, list) or any(e['codeId'] != 'sv' for e in history):
        raise ValueError('Histórico de súmulas inválido')
    current = previous or pdf
    fetcher = fetcher or (lambda url: fetch({'url': url}, allowed_hosts=HOSTS))
    stage, active_url = 'index', INDEX
    try:
        raw, encoding = fetcher(INDEX)
        (run_dir / 'index.html').write_bytes(raw)
        index = parse_index(raw, current['articles'], encoding)
        old_articles = {int(a['number']): a for a in current['articles']}
        snapshots, articles = {}, []
        for number, url in index.items():
            sleeper(.2)
            stage, active_url = f'sv-{number}', url
            raw, encoding = fetcher(url)
            # Preserve raw evidence only as a workflow artifact, never as executable site HTML.
            (run_dir / f'sv-{number}.html').write_bytes(raw)
            article = parse_item(raw, number, url, old_articles.get(number), encoding)
            snapshot = {'schema_version': 1, 'number': number, 'source_url': url,
                        'captured_at': stamp, 'raw_sha256': sha256(raw).hexdigest(),
                        'semantic_sha256': digest(article), 'article': article}
            old_path = root / f'monitor/stf/items/{number}.json'
            if old_path.exists():
                old = json.loads(old_path.read_text())
                if digest(old['article']) != old['semantic_sha256']:
                    raise ValueError(f'Referência local corrompida: SV {number}')
                if old['semantic_sha256'] == snapshot['semantic_sha256'] and old['source_url'] == url:
                    snapshot = old
            snapshots[number] = snapshot
            articles.append(article)
        semantic_hash = digest({str(n): s['semantic_sha256'] for n, s in snapshots.items()})
        source = {'kind': 'official_stf', 'url': INDEX, 'sha256': semantic_hash,
                  'converterVersion': CONVERTER, 'capturedAt': stamp, 'snapshot': 'monitor/stf/index.json',
                  'edition': 'STF · fonte oficial consultada',
                  'coverage': f'{len(articles)} entradas de súmulas vinculantes, com enunciados e material de aplicação.',
                  'reviewStatus': 'Coleta automática das páginas do STF proposta para revisão. Situações e notas reproduzem a fonte consultada; a coleta não certifica vigência.'}
        if previous and previous['source']['sha256'] == semantic_hash and previous['source'].get('converterVersion') == CONVERTER:
            source = previous['source']
        candidate = {**copy.deepcopy(pdf), 'articles': articles, 'source': source,
                     'law': f'{len(articles)} entradas · Supremo Tribunal Federal',
                     'sections': [{'id': f'grupo-{i}', 'scope': 'main', 'title': f'Súmulas {i * 10 + 1} a {min((i + 1) * 10, max(index))}'} for i in range((max(index) + 9) // 10)]}
        event = make_event(previous, candidate, history)
        if event:
            history.append(event)
        old_by_id = {a['id']: a for a in current['articles']}
        diffs = [{'number': a['number'], 'before': version(old_by_id.get(a['id'])), 'after': version(a)}
                 for a in articles if version_signature(version(old_by_id.get(a['id']))) != version_signature(version(a))]
        report = {'status': 'validated', 'captured_at': stamp, 'entries': len(articles),
                  'first_official_capture': previous is None, 'differences': diffs,
                  'event_created': event is not None, 'semantic_sha256': semantic_hash}
        save_json(run_dir / 'report.json', report)
        summary = f'''## Atualização proposta das súmulas vinculantes do STF

Consulta das páginas oficiais do STF, com {len(articles)} entradas validadas.
Diferenças em relação à edição do leitor: **{len(diffs)}** entradas (enunciado, situação ou material de aplicação).

{'**Primeira coleta oficial:** a comparação do relatório usa o PDF fornecido como referência. O histórico começa com uma referência inicial; diferenças de migração não são apresentadas como novas mudanças jurídicas.' if previous is None else 'O histórico inclui comparações antes/depois dos enunciados, situações registradas e precedentes alterados.'}

Revise `monitor/stf/`, `data/official/sumulas.js`, `data/history/sumulas.js` e o relatório `report.json` no artefato da execução. A prévia inclui o leitor e a página Atualizações. O PDF fornecido permanece arquivado. Ausências ou falhas de validação bloqueiam esta proposta, sem excluir entradas do leitor.

**Sem aprovação, merge ou implantação automática.** As datas indicam a coleta; situações e início de efeitos precisam ser conferidos na fonte. Mesclar incorpora a versão ao repositório; a publicação depende da hospedagem.
'''
        (run_dir / 'pr-body.md').write_text(summary)
        # Prepare everything in memory and validate the entire collection before
        # touching any tracked candidate. A failed later CI step also blocks PRs.
        for number, snapshot in snapshots.items():
            save_json(root / f'monitor/stf/items/{number}.json', snapshot)
        index_path = root / 'monitor/stf/index.json'
        index_snapshot = {'schema_version': 1, 'source_url': INDEX, 'captured_at': source['capturedAt'],
                          'semantic_sha256': semantic_hash, 'links': {str(n): url for n, url in index.items()}}
        save_json(index_path, index_snapshot)
        for folder in ['data/official','data/history']:(root / folder).mkdir(parents=True,exist_ok=True)
        (root / 'data/official/sumulas.js').write_text('export const officialSumulas = ' + json.dumps([candidate], ensure_ascii=False, separators=(',', ':')) + ';\n')
        (root / 'data/history/sumulas.js').write_text('export const sumulaUpdates = ' + json.dumps(history, ensure_ascii=False, separators=(',', ':')) + ';\n')
        print(f'STF: {len(articles)} entradas validadas; {len(diffs)} diferenças para revisão.')
        return candidate, report
    except Exception as error:
        save_json(run_dir / 'report.json', {'status': 'failed', 'stage': stage, 'url': active_url, 'error': f'{type(error).__name__}: {error}', 'captured_at': stamp})
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--transport', choices=['http', 'browser'], default='http')
    args = parser.parse_args()
    try:
        if args.transport == 'browser':
            from stf_browser import STFBrowser
            with STFBrowser(args.root / 'monitor/run/stf') as browser:
                run(args.root, fetcher=browser.fetch)
        else:
            run(args.root)
    except Exception as error:
        print(f'STF: coleta bloqueada — {error}', file=sys.stderr)
        sys.exit(1)
