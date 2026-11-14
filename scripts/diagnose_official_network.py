"""Read-only HTTPS/DNS comparison. Never follow redirects or update legal data."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
from urllib.parse import urlsplit

from official_http import MAX_BYTES, USER_AGENT, check_url, response_headers
from check_official_sources import ROOT, parse_html, validate


def diagnose():
    spec = json.loads((ROOT/'monitor/sources.json').read_text(encoding='utf-8'))[0]
    check_url(spec['url'])
    host = urlsplit(spec['url']).hostname
    addresses = {}
    for name, family in [('IPv4', socket.AF_INET), ('IPv6', socket.AF_INET6)]:
        try:
            addresses[name] = sorted({row[4][0] for row in socket.getaddrinfo(host, 443, family, socket.SOCK_STREAM)})
        except socket.gaierror as error:
            addresses[name] = {'error_code': error.errno}
    report = {'collected_at': datetime.now(timezone.utc).isoformat(), 'source_url': spec['url'],
              'dns': addresses, 'proxy_variable_present': {key: bool(os.environ.get(key)) for key in ['HTTPS_PROXY', 'ALL_PROXY', 'NO_PROXY']},
              'requests': [], 'legal_data_modified': False}
    curl = shutil.which('curl')
    if not curl:
        raise RuntimeError('curl ausente')
    for family, flags in [('auto', []), ('IPv4', ['--ipv4']), ('IPv6', ['--ipv6'])]:
        with tempfile.TemporaryDirectory(prefix='lexa-network-diagnostic-') as directory:
            body, headers = Path(directory)/'body', Path(directory)/'headers'
            command = [curl, '--disable', '--silent', '--show-error', '--http1.1', '--compressed',
                       '--proto', '=https', '--connect-timeout', '8', '--max-time', '20',
                       '--max-filesize', str(MAX_BYTES), '--user-agent', USER_AGENT,
                       '--header', 'Accept: text/html,application/xhtml+xml',
                       '--output', str(body), '--dump-header', str(headers), '--write-out', '%{json}',
                       *flags, spec['url']]
            item = {'family': family}
            try:
                result = subprocess.run(command, capture_output=True, text=True, timeout=25, check=False)
                item['curl_exit'] = result.returncode
                try:
                    metadata = json.loads(result.stdout)
                    item['transfer'] = {key: metadata.get(key) for key in ['http_code', 'remote_ip', 'http_version', 'ssl_verify_result', 'time_total', 'size_download', 'content_type']}
                except ValueError:
                    item['transfer'] = {'invalid_client_metadata': True}
                try:
                    fields = response_headers(headers.read_bytes())
                    item['headers'] = {key: fields.get(key) for key in ['Date', 'Server', 'Content-Type', 'Content-Length', 'Strict-Transport-Security'] if fields.get(key)}
                    if fields.get('Location'):
                        destination = urlsplit(fields['Location'])
                        item['redirect'] = {'scheme': destination.scheme, 'host': destination.hostname, 'path': destination.path}
                except (OSError, ValueError, RuntimeError):
                    fields = None
                if body.exists() and body.stat().st_size <= MAX_BYTES:
                    raw = body.read_bytes()
                    item['body_bytes'] = len(raw)
                    item['raw_sha256'] = hashlib.sha256(raw).hexdigest()
                    document = parse_html(raw, fields.get_content_charset() if fields else None)
                    # Plain text only, never cookies, scripts, rendered HTML or headers with credentials.
                    item['visible_text_sample'] = ' '.join(run['text'] for block in document['blocks'] for run in block)[:3000]
                    try:
                        item['article_counts'] = validate(document, spec)
                        item['document_valid'] = True
                    except ValueError as error:
                        item['document_valid'] = False
                        item['validation_error'] = str(error)
            except subprocess.TimeoutExpired:
                item['timeout'] = True
            report['requests'].append(item)
            print(json.dumps(item, ensure_ascii=True), flush=True)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = diagnose()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'dns': report['dns'], 'proxy_variable_present': report['proxy_variable_present']}, ensure_ascii=True))
