"""Reproducible Chromium baseline; preserves the positional site path and legacy
runs_ms/median_ms fields for the cold initial-library measurement.
No timing value is a pass/fail performance threshold.
"""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import http.server
import hashlib
import importlib.metadata
import json
import mimetypes
import os
from pathlib import Path
import platform
import re
import statistics
import subprocess
import sys
import threading
import time
import unicodedata
from urllib.parse import unquote, urlsplit

from playwright.sync_api import sync_playwright
from support import chromium_executable, app_evaluate
from benchmark_metrics import NetworkLedger, summarize, transfer_summary

ROOT = Path(__file__).resolve().parents[2]


class BenchmarkServer(http.server.ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, directory):
        self.directory = Path(directory).resolve()
        self.audit_phase = None
        self.audit_lock = threading.Lock()
        super().__init__(('127.0.0.1', 0), BenchmarkHandler)

    def begin(self):
        with self.audit_lock:
            self.audit_phase = []
            return self.audit_phase

    def stop(self):
        with self.audit_lock:
            self.audit_phase = None


class BenchmarkHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def do_GET(self):
        with self.server.audit_lock:
            audit = self.server.audit_phase
        path = self.server.directory / unquote(urlsplit(self.path).path).lstrip('/')
        if path.is_dir():
            path = path / 'index.html'
        path = path.resolve()
        if not path.is_relative_to(self.server.directory) or not path.is_file():
            self.send_error(404)
            return
        body = path.read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', mimetypes.guess_type(path)[0] or 'application/octet-stream')
        self.send_header('Content-Length', str(len(body)))
        immutable = bool(re.search(r'\.[a-f0-9]{64}\.json$', path.name) or re.search(r'/app/[a-f0-9]{64}/[^/]+\.js$', path.as_posix()))
        self.send_header('Cache-Control', 'public, max-age=31536000, immutable' if immutable else 'no-cache')
        self.end_headers()
        try:
            self.wfile.write(body)
            if audit is not None:
                with self.server.audit_lock:
                    audit.append(len(body))
        except (BrokenPipeError, ConnectionResetError):
            pass


class Probe:
    def __init__(self, page, context, server, cpu, memory):
        self.page, self.server, self.memory = page, server, memory
        self.session = context.new_cdp_session(page)
        self.session.send('Network.enable')
        self.session.send('Performance.enable')
        self.session.send('Emulation.setCPUThrottlingRate', {'rate': cpu})
        self.ledger = NetworkLedger()
        for event, handler in [('requestWillBeSent', self.ledger.request),
                               ('requestServedFromCache', self.ledger.cached),
                               ('responseReceived', self.ledger.response),
                               ('loadingFinished', self.ledger.finished),
                               ('loadingFailed', self.ledger.failed)]:
            self.session.on('Network.' + event, handler)
        self.memory_limits = set()

    def heap(self):
        if not self.memory:
            return None
        try:
            self.session.send('HeapProfiler.collectGarbage')
            values = {item['name']: item['value'] for item in self.session.send('Performance.getMetrics')['metrics']}
            if 'JSHeapUsedSize' not in values:
                raise RuntimeError('JSHeapUsedSize indisponível')
            return int(values['JSHeapUsedSize'])
        except Exception as error:
            self.memory_limits.add(type(error).__name__ + ': ' + str(error).splitlines()[0])
            return None

    def measure(self, scenario, cache, action, ready, *, navigation=False, model_state='empty'):
        before_heap = self.heap()
        items = self.ledger.begin()
        origin = self.server.begin()
        start = self.page.evaluate('performance.now()')
        action()
        ready()
        dom_ready = self.page.evaluate('performance.now()')
        # For a navigation performance.now() resets; interactions use the old clock.
        duration = dom_ready if navigation else dom_ready - start
        next_frame = self.page.evaluate('''()=>new Promise(resolve=>requestAnimationFrame(()=>
            requestAnimationFrame(()=>resolve(performance.now()))))''')
        self.ledger.stop()
        self.server.stop()
        # Finish byte accounting OUTSIDE the measured interval, without networkidle.
        deadline = time.monotonic() + 5
        while any(not item['finished'] for item in items) and time.monotonic() < deadline:
            self.page.wait_for_timeout(10)
        after_heap = self.heap()
        return {
            'scenario': scenario, 'cache': cache, 'model_state': model_state,
            'duration_ms': round(duration, 2),
            'next_frame_ms': round(next_frame if navigation else next_frame - start, 2),
            'transfer': transfer_summary(items),
            'origin_body_bytes': sum(origin), 'origin_requests': len(origin),
            'js_heap_after_gc_bytes': after_heap,
            'js_heap_delta_bytes': after_heap - before_heap if after_heap is not None and before_heap is not None else None,
        }


def library_ready(page, count):
    page.wait_for_function('count=>document.querySelectorAll("#cards .code-card").length===count', arg=count)


def search_ready(page, query, group_count):
    page.wait_for_function('''({query,count})=>document.querySelector('#library-search')?.value===query &&
        document.querySelectorAll('.text-result-group').length===count &&
        !document.querySelector('#library-results').textContent.includes('Carregando') &&
        [...document.querySelectorAll('.text-result mark')].some(mark=>
          mark.textContent.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase()===query)''', arg={'query': query, 'count': group_count})


def reader_ready(page):
    page.wait_for_function('document.querySelectorAll("#articles .article").length>0')


def offline_ready(page, complete=False):
    page.wait_for_function('navigator.serviceWorker.controller!==null && document.querySelector("#pwa-status").textContent.includes("preparada")')
    if complete and page.locator('#pwa-cache-all').count():
        page.locator('.pwa-help').evaluate('(el)=>el.open=true')
        page.locator('#pwa-cache-all').click()
        page.wait_for_function('document.querySelector("#pwa-status").dataset.offlineMode==="full"')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', nargs='?', type=Path, default=ROOT/'dist')
    parser.add_argument('--runs', type=int, default=5)
    parser.add_argument('--cpu', type=float, default=4)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--no-memory', action='store_true')
    parser.add_argument('--skip-offline', action='store_true')
    args = parser.parse_args()
    if args.runs < 1 or args.cpu < 1:
        parser.error('--runs e --cpu devem ser maiores ou iguais a 1')
    directory = args.directory.resolve()
    catalog = json.loads((directory/'catalog.json').read_text(encoding='utf-8'))
    count = len(catalog['collections'])
    # Expected result groups come from the exact build being benchmarked, not a
    # hard-coded collection count that becomes stale when a law is added.
    expected = {query: 0 for query in ['dignidade', 'educacao']}
    for spec in catalog['collections']:
        content = json.loads((directory/spec['file']).read_text(encoding='utf-8'))
        fields = []
        for article in content['articles']:
            fields.extend(''.join(run['text'] for run in p['runs']) for p in [*article['paragraphs'], *article.get('notes', [])])
            fields.append(article.get('title', ''))
        normalized = [''.join(c for c in unicodedata.normalize('NFD', text) if not unicodedata.combining(c)).lower() for text in fields]
        for query in expected:
            expected[query] += any(query in field for field in normalized)
    server = BenchmarkServer(directory)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f'http://127.0.0.1:{server.server_port}/'
    samples, errors, memory_limits = [], [], set()
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(executable_path=chromium_executable(), args=[
                '--no-sandbox', '--disable-dev-shm-usage', '--no-proxy-server', '--disable-background-networking'])
            browser_version = browser.version

            @contextmanager
            def session(offline=False):
                context = browser.new_context(service_workers='allow' if offline else 'block',
                    viewport={'width': 375, 'height': 812}, locale='pt-BR', timezone_id='America/Sao_Paulo')
                page = context.new_page()
                page.set_default_timeout(90_000)
                page.on('pageerror', lambda error: errors.append(str(error)))
                probe = Probe(page, context, server, args.cpu, not args.no_memory)
                try:
                    yield page, probe
                finally:
                    memory_limits.update(probe.memory_limits)
                    context.close()

            for run in range(1, args.runs + 1):
                for cache in ['cold', 'warm_http']:
                    with session() as (page, probe):
                        if cache == 'warm_http':
                            page.goto(base)
                            library_ready(page, count)
                            page.locator('#library-search').fill('dignidade')
                            search_ready(page, 'dignidade', expected['dignidade'])
                        # A reload guarantees a fresh JS model but keeps HTTP cache.
                        navigate = (lambda: page.reload(wait_until='commit')) if cache == 'warm_http' else (lambda: page.goto(base, wait_until='commit'))
                        samples.append({'run': run, **probe.measure('library_initial', cache, navigate,
                            lambda: library_ready(page, count), navigation=True)})
                        assert app_evaluate(page,'collections.every(code=>!code.loaded)')
                        for scenario, query, state in [('global_search_first', 'dignidade', 'empty'),
                                                       ('global_search_subsequent', 'educacao', 'data_and_indexes_loaded'),
                                                       ('global_search_repeated', 'dignidade', 'data_and_indexes_loaded')]:
                            samples.append({'run': run, **probe.measure(scenario, cache,
                                lambda q=query: page.locator('#library-search').fill(q),
                                lambda q=query: search_ready(page, q, expected[q]), model_state=state)})
                    # Independent contexts keep the global search from warming readers.
                    for code in ['civil', 'cpc', 'clt']:
                        with session() as (page, probe):
                            page.goto(base);library_ready(page, count)
                            if cache == 'warm_http':
                                page.locator(f'.code-card[href="#/{code}"]').click();reader_ready(page)
                                page.evaluate("localStorage.removeItem('lexa-last-reading')")
                                page.goto(base)
                                page.reload()
                                library_ready(page, count)
                            page.evaluate('''()=>Promise.all(document.getAnimations().filter(a=>a.playState==='running' && Number.isFinite(a.effect.getTiming().iterations)).map(a=>a.finished.catch(()=>{})))''')
                            assert app_evaluate(page,'(id)=>!collections.find(code=>code.id===id).loaded', code)
                            samples.append({'run': run, **probe.measure('reader_open_'+code, cache,
                                lambda: page.locator(f'.code-card[href="#/{code}"]').click(), lambda: reader_ready(page))})
                            for direction, button in [('next', '#next-page'), ('previous', '#previous-page')]:
                                previous = page.locator('#articles .article').first.get_attribute('id')
                                samples.append({'run': run, **probe.measure('reader_'+direction+'_'+code, cache,
                                    lambda b=button: page.locator(b).click(),
                                    lambda old=previous: page.wait_for_function('old=>{const first=document.querySelector("#articles .article");return first&&first.id!==old;}', arg=old),
                                    model_state='collection_loaded')})
                if not args.skip_offline:
                    with session(offline=True) as (page, probe):
                        samples.append({'run': run, **probe.measure('offline_first_visit', 'fresh_install',
                            lambda: page.goto(base, wait_until='commit'), lambda: offline_ready(page), navigation=True)})
                    with session(offline=True) as (page, probe):
                        samples.append({'run': run, **probe.measure('offline_preparation', 'fresh_install',
                            lambda: page.goto(base, wait_until='commit'),
                            lambda: offline_ready(page, complete=True),
                            navigation=True)})
                print(f'Execução {run}/{args.runs} concluída', file=sys.stderr, flush=True)
            browser.close()
    finally:
        server.shutdown();server.server_close();thread.join()
    if errors:
        raise RuntimeError('Erros JavaScript durante o benchmark: '+str(errors))
    summary = {}
    for sample in samples:
        key = sample['scenario'] + ':' + sample['cache']
        summary.setdefault(key, []).append(sample)
    summary = {key: summarize(values) for key, values in summary.items()}
    legacy = [sample['duration_ms'] for sample in samples if sample['scenario']=='library_initial' and sample['cache']=='cold']
    report = {
        'schema_version': 2, 'runs_ms': legacy, 'median_ms': statistics.median(legacy),
        'metadata': {
            'timestamp_utc': datetime.now(timezone.utc).isoformat(),
            'revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
            'tracked_changes_present': bool(subprocess.check_output(['git','diff','--name-only'],cwd=ROOT,text=True).strip()),
            'platform': platform.platform(), 'architecture': platform.machine(), 'logical_cpus': os.cpu_count(),
            'chromium': browser_version, 'playwright': importlib.metadata.version('playwright'),
            'python': platform.python_version(), 'node': subprocess.check_output(['node','--version'],text=True).strip(),
            'cpu_throttling': args.cpu, 'runs': args.runs, 'viewport': {'width':375,'height':812},
            'locale':'pt-BR','timezone':'America/Sao_Paulo', 'compression':'none', 'network':'HTTP loopback; no network throttle',
            'service_workers':'blocked except offline scenarios (separate fresh contexts); offline_preparation explicitly requests full library when supported',
            'warm_http':'primed outside timing; document reload resets JS; no saved reading prefetch',
            'timing':'navigation performance.now(); interactions from just before action to functional DOM readiness; includes typing/debounce and automation round trips',
            'next_frame':'two requestAnimationFrame callbacks after readiness; not completion of animations',
            'transfer':'CDP loadingFinished encodedDataLength including response headers; cached/worker responses excluded from network_bytes',
            'origin_body':'server audit of response bodies only, excluding headers; includes worker-initiated downloads absent from page CDP',
            'offline_transfer':'use origin_body_bytes for offline_preparation; page CDP excludes worker network',
            'memory':'V8 page JSHeapUsedSize after requested GC, outside timing; not peak, RSS, DOM, GPU or worker heap',
            'memory_enabled':not args.no_memory, 'memory_limitations':sorted(memory_limits),
            'html_bytes':(directory/'index.html').stat().st_size,
            'html_sha256':hashlib.sha256((directory/'index.html').read_bytes()).hexdigest(),
            'catalog_sha256':hashlib.sha256((directory/'catalog.json').read_bytes()).hexdigest(),
            'benchmark_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'host_isolation':'shared execution container; CPU frequency and competing host load uncontrolled',
            'catalog_collections':count, 'expected_search_groups':expected,
        }, 'summary': summary, 'samples': samples,
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    main()
