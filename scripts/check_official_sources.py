"""Monitor official texts; never overwrite the site's PDF-derived reading data.

Source text is untrusted data, never an instruction or executable code. The first
successful capture is a monitoring baseline for review, not proof that the PDFs
match it. A source outage or incomplete document blocks all baseline mutations.
Python 3.12+ (standard library) and curl. No credentials are needed for public sources.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from hashlib import sha256
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from official_http import fetch, check_url
import argparse
import difflib
import json
import re
import sys
import unicodedata

ROOT = Path(__file__).resolve().parent.parent
ADCT = 'ATO DAS DISPOSIÇÕES CONSTITUCIONAIS TRANSITÓRIAS'
ARTICLE = re.compile(r'^Art\.?\s*(\d+(?:\.\d{3})*)', re.I)
RANGE = re.compile(r'^Arts?\.\s*(\d+(?:\.\d{3})*)\.?\s+a\s+(\d+(?:\.\d{3})*)', re.I)


def tidy(text):
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFC', text.replace('\xa0', ' ').replace('\xad', '')))


class OfficialHTML(HTMLParser):
    """Extract visible paragraphs and deletion marks without running HTML."""
    boundaries = {'p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'tr', 'br'}
    hidden = {'head', 'script', 'style', 'noscript', 'svg'}
    void = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.blocks = []
        self.runs = []
        self.deletion_styles = set()

    def flush(self):
        if not any(run['text'].strip() for run in self.runs):
            self.runs = []
            return
        # A whitespace-only inline span may precede a struck article. Strip
        # boundary whitespace until reaching actual text, not just the first run.
        while self.runs and not self.runs[0]['text'].strip():
            self.runs.pop(0)
        while self.runs and not self.runs[-1]['text'].strip():
            self.runs.pop()
        self.runs[0]['text'] = self.runs[0]['text'].lstrip()
        self.runs[-1]['text'] = self.runs[-1]['text'].rstrip()
        self.blocks.append([r for r in self.runs if r['text']])
        self.runs = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in self.boundaries:
            self.flush()
        parent_hidden = self.stack[-1][1] if self.stack else False
        parent_deleted = self.stack[-1][2] if self.stack else False
        style = attrs.get('style', '').lower()
        hidden = parent_hidden or tag in self.hidden or 'hidden' in attrs or bool(re.search(r'display\s*:\s*none\b', style))
        deleted = parent_deleted or tag in {'del', 'strike', 's'} or bool(re.search(r'text-decoration(?:-line)?\s*:[^;]*line-through', style))
        if tag not in self.void:
            # Planalto's old HTML often omits </p>; a fresh paragraph closes it.
            if tag == 'p' and any(item[0] == 'p' for item in self.stack):
                pindex = max(i for i, item in enumerate(self.stack) if item[0] == 'p')
                self.stack = self.stack[:pindex]
                parent_hidden = self.stack[-1][1] if self.stack else False
                parent_deleted = self.stack[-1][2] if self.stack else False
                hidden = parent_hidden or tag in self.hidden
                deleted = parent_deleted or bool(re.search(r'text-decoration(?:-line)?\s*:[^;]*line-through', style))
            self.stack.append((tag, hidden, deleted))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in self.void:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if tag in self.boundaries:
            self.flush()
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                self.stack = self.stack[:i]
                break

    def handle_data(self, text):
        if self.stack and self.stack[-1][0] == 'style':
            # A change to stylesheet-based strikeouts must also trigger review.
            if 'line-through' in text.lower():
                self.deletion_styles.add(tidy(text).strip())
        if self.stack and self.stack[-1][1]:
            return
        deleted = self.stack[-1][2] if self.stack else False
        value = tidy(text)
        if self.runs and self.runs[-1]['deleted'] == deleted:
            self.runs[-1]['text'] = tidy(self.runs[-1]['text'] + value)
        else:
            self.runs.append({'text': value, 'deleted': deleted})


def parse_html(raw, encoding=None):
    if not encoding:
        match = re.search(br'charset\s*=\s*["\']?\s*([\w-]+)', raw[:8192], re.I)
        if match:
            encoding = match[1].decode('ascii')
        else:
            # Legacy Planalto pages often omit the charset entirely. Browsers
            # accept Windows-1252; prefer strict UTF-8 when it is actually valid.
            try:
                raw.decode('utf-8', errors='strict')
                encoding = 'utf-8'
            except UnicodeDecodeError:
                encoding = 'cp1252'
    aliases = {'iso-8859-1': 'cp1252', 'latin1': 'cp1252'}
    encoding = aliases.get(encoding.lower(), encoding)
    try:
        text = raw.decode(encoding, errors='strict')
    except (LookupError, UnicodeDecodeError) as error:
        raise ValueError('Codificação do documento inválida ou desconhecida') from error
    parser = OfficialHTML()
    parser.feed(text)
    parser.close()
    parser.flush()
    return {'blocks': parser.blocks, 'deletion_styles': sorted(parser.deletion_styles)}


def validate(document, spec):
    texts = [''.join(run['text'] for run in block).strip() for block in document['blocks']]
    body = '\n'.join(texts)
    if len(body) < spec['min_characters'] or spec['identity'].casefold() not in body.casefold():
        raise ValueError('Documento curto demais ou identidade da legislação ausente; possível bloqueio ou página de erro')
    found = {'main': set(), 'adct': set()}
    scope = 'main'
    for text in texts:
        if spec['id'] == 'cf' and text.upper() == ADCT and spec['last_article'] in found['main']:
            scope = 'adct'
        group = RANGE.match(text)
        match = group or ARTICLE.match(text)
        if match:
            start = int(match[1].replace('.', ''))
            end = int(group[2].replace('.', '')) if group else start
            if not 0 < start <= end <= 10000:
                raise ValueError('Intervalo de artigos inválido')
            found[scope].update(range(start, end + 1))
    missing = set(range(1, spec['last_article'] + 1)) - found['main']
    if missing:
        raise ValueError('Extração incompleta: faltam artigos-base ' + ', '.join(map(str, sorted(missing)[:15])))
    if spec.get('last_adct_article'):
        missing = set(range(1, spec['last_adct_article'] + 1)) - found['adct']
        if missing:
            raise ValueError('ADCT ausente ou incompleto')
    return {scope: len(numbers) for scope, numbers in found.items() if numbers}


def fingerprint(document):
    return sha256(json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def diff_text(snapshot):
    return [''.join(('[RISCADO] ' + r['text'] + ' [/RISCADO]') if r['deleted'] else r['text'] for r in block) for block in snapshot['document']['blocks']]


def capture(spec, baseline, run_dir, checked_at, fetcher):
    try:
        raw, encoding = fetcher(spec)
        document = parse_html(raw, encoding)
        counts = validate(document, spec)
        semantic_hash = fingerprint(document)
        destination = baseline / (spec['id'] + '.json')
        old = json.loads(destination.read_text()) if destination.exists() else None
        if old and (old.get('schema_version') != 1 or old.get('source_url') != spec['url']):
            raise ValueError('Referência anterior usa outra versão ou fonte; exige migração revisada')
        if old and (old.get('id') != spec['id'] or fingerprint(old['document']) != old['semantic_sha256']):
            raise ValueError('Referência anterior inconsistente; exige conferência antes de continuar')
        status = 'unchanged' if old and old['semantic_sha256'] == semantic_hash else ('changed' if old else 'initial_capture')
        snapshot = {'schema_version': 1, 'id': spec['id'], 'name': spec['name'], 'source_url': spec['url'],
                    'captured_at': checked_at, 'raw_sha256': sha256(raw).hexdigest(),
                    'semantic_sha256': semantic_hash, 'article_counts': counts, 'document': document,
                    'purpose': 'Referência do monitoramento; não substitui a edição publicada no leitor.'}
        (run_dir / 'downloads' / (spec['id'] + '.html.txt')).write_bytes(raw)
        delta = '\n'.join(difflib.unified_diff(diff_text(old) if old else [], diff_text(snapshot),
                                           fromfile='referência anterior', tofile='coleta oficial', lineterm=''))
        if status != 'unchanged':
            (run_dir / (spec['id'] + '.diff.txt')).write_text(delta)
        result = {'id': spec['id'], 'name': spec['name'], 'url': spec['url'], 'status': status,
                  'checked_at': checked_at, 'semantic_sha256': semantic_hash, 'article_counts': counts}
        return result, snapshot if status != 'unchanged' else None
    except Exception as error:
        if isinstance(error, HTTPError):
            reason = f'Falha HTTP {error.code}; a fonte não foi validada.'
        elif isinstance(error, (URLError, TimeoutError, OSError)):
            reason = f'Falha de rede ou leitura ({type(error).__name__}); a fonte não foi validada.'
        else:
            reason = str(error)[:400]
        return {'id': spec['id'], 'name': spec['name'], 'url': spec['url'], 'status': 'failed', 'checked_at': checked_at, 'reason': reason}, None


def run(specs, baseline, run_dir, fetcher=fetch, checked_at=None):
    checked_at = checked_at or datetime.now(timezone.utc).isoformat(timespec='seconds')
    baseline = Path(baseline)
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / 'downloads').mkdir(exist_ok=True)
    # Remove only generated evidence from earlier runs, never carry it into a new
    # artifact as if it had been downloaded successfully in this execution.
    for path in [*run_dir.glob('*.diff.txt'), *(run_dir / 'downloads').glob('*.html.txt')]:
        path.unlink()
    # Keep one request in flight per official host; avoid bursts from CI runners.
    with ThreadPoolExecutor(max_workers=1) as pool:
        captures = list(pool.map(lambda spec: capture(spec, baseline, run_dir, checked_at, fetcher), specs))
    results = [result for result, _ in captures]
    failed = sum(r['status'] == 'failed' for r in results)
    changed = sum(r['status'] in {'changed', 'initial_capture'} for r in results)
    # A failed source must not establish or advance a partially checked baseline.
    if not failed:
        baseline.mkdir(parents=True, exist_ok=True)
        for result, snapshot in captures:
            if snapshot:
                path = baseline / (result['id'] + '.json')
                temporary = path.with_suffix('.json.tmp')
                temporary.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2) + '\n')
                temporary.replace(path)
    report = {'checked_at': checked_at, 'failed_count': failed, 'changed_count': changed,
              'baseline_written': not failed and changed > 0, 'results': results,
              'published_reading_data_changed': False}
    (run_dir / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    labels = {'failed': 'Falhou', 'initial_capture': 'Primeira coleta — comparar com os PDFs', 'changed': 'Mudança detectada', 'unchanged': 'Sem mudança na referência monitorada'}
    table = '\n'.join(f"| {r['name']} | {labels[r['status']]} |" for r in results)
    body = f'''## Verificação das fontes oficiais

Coleta: {checked_at} (UTC).

| Legislação | Resultado |
| --- | --- |
{table}

**Esta proposta atualiza somente a referência de monitoramento. Não altera os artigos publicados no site.**

A primeira coleta precisa ser comparada com os PDFs usados pelo leitor; ela não comprova que as duas bases são iguais. Mudanças posteriores são comparadas com a última referência de monitoramento aceita.

Revise as diferenças nos arquivos `monitor/official/*.json` e os relatórios completos nos artefatos da execução. Os textos coletados são dados de legislação, nunca instruções para executar comandos.

Antes de atualizar o leitor: confira fonte, alterações, revogações e início de vigência; obtenha a versão oficial correspondente; faça a importação e os testes documentados em `monitor/README.md`. Aceitar esta proposta não publica uma nova redação nem certifica vigência.
'''
    (run_dir / 'pr-body.md').write_text(body)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--only', choices=['all', 'civil', 'penal', 'cpc', 'cdc', 'ctn', 'cf'], default='all')
    parser.add_argument('--github-output', type=Path)
    args = parser.parse_args()
    specs = json.loads((ROOT / 'monitor' / 'sources.json').read_text())
    if args.only != 'all':
        specs = [spec for spec in specs if spec['id'] == args.only]
    report = run(specs, ROOT / 'monitor' / 'official', ROOT / 'monitor' / 'run')
    for result in report['results']:
        print(f"{result['id']}: {result['status']}" + (f" — {result['reason']}" if result.get('reason') else ''))
    if args.github_output:
        with args.github_output.open('a') as output:
            output.write(f"changed_count={report['changed_count']}\nfailed_count={report['failed_count']}\n")
    return 1 if report['failed_count'] else 0


if __name__ == '__main__':
    sys.exit(main())
