"""Bounded, verified HTTPS collection through Chromium's network stack.

Read the response stream, never the rendered DOM. Scripts and subresources are
disabled; every redirect is validated before the next request is sent.
"""
import base64
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from urllib.parse import urljoin

from official_http import MAX_BYTES, SourceFetchError, check_url, response_headers, retry_delay, TRANSIENT_HTTP_CODES


def read_stream(session, handle):
    body = bytearray()
    try:
        while True:
            chunk = session.send('IO.read', {'handle': handle, 'size': min(65536, MAX_BYTES + 1 - len(body))})
            body.extend(base64.b64decode(chunk['data'], validate=True) if chunk.get('base64Encoded') else chunk['data'].encode('utf-8'))
            if len(body) > MAX_BYTES:
                raise SourceFetchError('Documento ultrapassa o limite de tamanho.')
            if chunk.get('eof'):
                return bytes(body)
    finally:
        session.send('IO.close', {'handle': handle})


def collect(url, allowed_hosts=None):
    from playwright.sync_api import sync_playwright, TimeoutError as NavigationTimeout
    check_url(url, allowed_hosts)
    with sync_playwright() as p:
        options = {'headless': True}
        if os.environ.get('LEXA_CHROMIUM'):
            options['executable_path'] = os.environ['LEXA_CHROMIUM']
        browser = p.chromium.launch(**options)
        context = browser.new_context(java_script_enabled=False, service_workers='block', accept_downloads=False)
        page = context.new_page()
        session = context.new_cdp_session(page)
        state = {}

        def paused(event):
            request_id = event['requestId']
            if 'responseStatusCode' not in event:
                # No styles, images, scripts, frames, or automatic redirect hops.
                if event.get('resourceType') == 'Document' and event['request']['url'] == state['url']:
                    session.send('Fetch.continueRequest', {'requestId': request_id})
                else:
                    session.send('Fetch.failRequest', {'requestId': request_id, 'errorReason': 'Aborted'})
                return
            try:
                status = event['responseStatusCode']
                raw_headers = b'HTTP/1.1 ' + str(status).encode() + b' Response\r\n' + b''.join(
                    (item['name'] + ': ' + item['value'] + '\r\n').encode('utf-8') for item in event.get('responseHeaders', [])) + b'\r\n'
                headers = response_headers(raw_headers)
                if status in {301, 302, 303, 307, 308}:
                    location = headers.get('Location')
                    if not location:
                        raise SourceFetchError('Redirecionamento sem destino.')
                    target = urljoin(state['url'], location)
                    check_url(target, allowed_hosts)
                    state['redirect'] = target
                elif status != 200:
                    raise SourceFetchError(f'Falha HTTP {status}; a fonte não foi validada.',
                                           retryable=status in TRANSIENT_HTTP_CODES,
                                           retry_after=retry_delay(headers.get('Retry-After')))
                else:
                    if headers.get_content_type() not in {'text/html', 'application/xhtml+xml'}:
                        raise SourceFetchError('Tipo de resposta diferente de HTML.')
                    if int(headers.get('Content-Length', '0')) > MAX_BYTES:
                        raise SourceFetchError('Documento ultrapassa o limite de tamanho.')
                    handle = session.send('Fetch.takeResponseBodyAsStream', {'requestId': request_id})['stream']
                    state['result'] = (read_stream(session, handle), headers.get_content_charset())
            except Exception as error:
                state['error'] = error
            finally:
                session.send('Fetch.failRequest', {'requestId': request_id, 'errorReason': 'Aborted'})

        session.on('Fetch.requestPaused', paused)
        session.send('Fetch.enable', {'patterns': [
            {'urlPattern': '*', 'requestStage': 'Request'},
            {'urlPattern': '*', 'requestStage': 'Response'}]})
        try:
            current = url
            for hop in range(4):
                check_url(current, allowed_hosts)
                state.clear()
                state['url'] = current
                try:
                    page.goto(current, wait_until='commit', timeout=25000)
                except Exception as error:
                    # Intercepted responses are intentionally aborted after
                    # their raw bytes (or redirect metadata) have been read.
                    if not any(key in state for key in ('result', 'redirect', 'error')):
                        raise SourceFetchError('Falha na navegação HTTPS do Chromium.',
                                               retryable=isinstance(error, NavigationTimeout)) from error
                if 'error' in state:
                    raise state['error']
                if 'result' in state:
                    return state['result']
                if 'redirect' not in state or hop == 3:
                    raise SourceFetchError('Limite de redirecionamentos excedido.')
                current = state['redirect']
        finally:
            browser.close()


def download_once(url, allowed_hosts=None):
    check_url(url, allowed_hosts)
    with tempfile.TemporaryDirectory(prefix='lexa-browser-fetch-') as directory:
        try:
            result = subprocess.run([sys.executable, str(Path(__file__).resolve()), '--worker', url, directory,
                                     json.dumps(sorted(allowed_hosts) if allowed_hosts is not None else None)],
                                    capture_output=True, timeout=40, check=False)
        except subprocess.TimeoutExpired as error:
            raise SourceFetchError('Tempo limite na coleta HTTPS do Chromium.', retryable=True) from error
        metadata_path = Path(directory) / 'metadata.json'
        if result.returncode or not metadata_path.exists():
            raise SourceFetchError('Cliente Chromium não concluiu a coleta HTTPS.')
        metadata = json.loads(metadata_path.read_text(encoding='utf-8'))
        if not metadata['ok']:
            raise SourceFetchError(metadata['reason'], retryable=metadata.get('retryable', False), retry_after=metadata.get('retry_after'))
        body = Path(directory) / 'body'
        if body.stat().st_size > MAX_BYTES:
            raise SourceFetchError('Documento ultrapassa o limite de tamanho.')
        return body.read_bytes(), metadata['charset']


if __name__ == '__main__':
    _, _, url, directory, hosts = sys.argv
    try:
        raw, charset = collect(url, json.loads(hosts))
        (Path(directory) / 'body').write_bytes(raw)
        metadata = {'ok': True, 'charset': charset}
    except Exception as error:
        metadata = {'ok': False, 'reason': str(error) if isinstance(error, (SourceFetchError, ValueError)) else 'Falha no cliente HTTPS do Chromium.',
                    'retryable': getattr(error, 'retryable', False), 'retry_after': getattr(error, 'retry_after', None)}
    (Path(directory) / 'metadata.json').write_text(json.dumps(metadata), encoding='utf-8')
