"""Bounded HTTPS downloads for the official monitor, with verified TLS.

Some Planalto endpoints close Python urllib's connection without a response.
curl with HTTP/1.1 and a compatible, identified user agent has been tested
against the live endpoints. Redirects are checked before following them.
"""
from datetime import datetime, timezone
from email import policy
from email.parser import BytesParser
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urljoin, urlsplit
import shutil
import subprocess
import tempfile
import time

MAX_BYTES = 12 * 1024 * 1024
ALLOWED_HOSTS = {'www.planalto.gov.br', 'planalto.gov.br'}
USER_AGENT = 'Mozilla/5.0 (compatible; Lexa/0.1; public legislation research)'
TRANSIENT_CURL_CODES = {5, 6, 7, 18, 28, 52, 55, 56}
TRANSIENT_HTTP_CODES = {408, 429, 500, 502, 503, 504}


class SourceFetchError(RuntimeError):
    def __init__(self, message, retryable=False, retry_after=None):
        super().__init__(message)
        self.retryable = retryable
        self.retry_after = retry_after


def check_url(url):
    parts = urlsplit(url)
    if parts.scheme != 'https' or parts.hostname not in ALLOWED_HOSTS or parts.port not in (None, 443) or parts.username or parts.password:
        raise ValueError('Destino diferente das fontes HTTPS oficiais permitidas')


def retry_delay(value):
    if not value:
        return None
    try:
        return max(0, int(value))
    except ValueError:
        try:
            date = parsedate_to_datetime(value)
            if date.tzinfo is None:
                date = date.replace(tzinfo=timezone.utc)
            return max(0, (date - datetime.now(timezone.utc)).total_seconds())
        except (ValueError, TypeError, OverflowError):
            return None


def response_headers(raw):
    blocks = [block for block in raw.replace(b'\r\n', b'\n').split(b'\n\n') if block.startswith(b'HTTP/')]
    if not blocks:
        raise SourceFetchError('Resposta sem cabeçalhos HTTP válidos.')
    # Ignore a proxy CONNECT response or an interim 100 response.
    last = blocks[-1].partition(b'\n')[2]
    return BytesParser(policy=policy.default).parsebytes(last + b'\n\n')


def download_once(url):
    check_url(url)
    curl = shutil.which('curl')
    if not curl:
        raise SourceFetchError('curl não está instalado; necessário para a coleta HTTPS.')
    with tempfile.TemporaryDirectory(prefix='lexa-fetch-') as directory:
        body = Path(directory) / 'body'
        headers = Path(directory) / 'headers'
        current = url
        for hop in range(4):
            check_url(current)
            command = [curl, '--disable', '--silent', '--show-error', '--http1.1',
                       '--compressed', '--proto', '=https', '--connect-timeout', '8',
                       '--max-time', '25', '--max-filesize', str(MAX_BYTES),
                       '--user-agent', USER_AGENT, '--header', 'Accept: text/html,application/xhtml+xml',
                       '--output', str(body), '--dump-header', str(headers),
                       '--write-out', '%{http_code}', current]
            try:
                result = subprocess.run(command, capture_output=True, text=True, timeout=30, check=False)
            except subprocess.TimeoutExpired as error:
                raise SourceFetchError('Tempo limite na transferência HTTPS.', retryable=True) from error
            if result.returncode:
                # Do not publish stderr: proxy configuration may contain private
                # details. Exit code and stage suffice; TLS errors are not retried.
                raise SourceFetchError(f'Falha na transferência HTTPS (curl {result.returncode}).',
                                       retryable=result.returncode in TRANSIENT_CURL_CODES)
            if not result.stdout.strip().isdigit():
                raise SourceFetchError('Cliente HTTP retornou um status inválido.')
            status = int(result.stdout.strip())
            metadata = response_headers(headers.read_bytes())
            if status in {301, 302, 303, 307, 308}:
                location = metadata.get('Location')
                if not location or hop == 3:
                    raise SourceFetchError('Redirecionamento ausente ou limite de redirecionamentos excedido.')
                current = urljoin(current, location)
                check_url(current)
                continue
            if status != 200:
                raise SourceFetchError(f'Falha HTTP {status}; a fonte não foi validada.',
                                       retryable=status in TRANSIENT_HTTP_CODES,
                                       retry_after=retry_delay(metadata.get('Retry-After')))
            if metadata.get_content_type() not in {'text/html', 'application/xhtml+xml'}:
                raise SourceFetchError('Tipo de resposta diferente de HTML.')
            if body.stat().st_size > MAX_BYTES:
                raise SourceFetchError('Documento ultrapassa o limite de tamanho.')
            return body.read_bytes(), metadata.get_content_charset()
    raise SourceFetchError('Não foi possível concluir a transferência HTTPS.')


def fetch(spec, attempts=3, sleeper=time.sleep):
    """Retry transient failures only; never fall back to insecure TLS or HTTP."""
    for attempt in range(1, attempts + 1):
        try:
            return download_once(spec['url'])
        except SourceFetchError as error:
            if not error.retryable or attempt == attempts:
                raise SourceFetchError(f'{error} Tentativas realizadas: {attempt}.') from error
            delay = error.retry_after if error.retry_after is not None else 2 ** attempt
            if delay > 30:
                raise SourceFetchError(f'{error} A fonte pediu espera maior que 30 segundos; aguardar próxima execução.') from error
            sleeper(delay)
    raise SourceFetchError('Nenhuma tentativa de coleta foi realizada.')
