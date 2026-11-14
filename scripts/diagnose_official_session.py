"""Small, read-only same-origin checks; never follow a redirect or print cookies."""
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from urllib.parse import urlsplit

from official_http import MAX_BYTES, USER_AGENT, check_url, response_headers
from check_official_sources import ROOT, parse_html, validate

spec = json.loads((ROOT/'monitor/sources.json').read_text(encoding='utf-8'))[0]
cases = [('session_initial', spec['url'], []), ('session_repeat', spec['url'], []),
         ('cache_revalidation', spec['url'], ['--header', 'Cache-Control: no-cache', '--header', 'Pragma: no-cache']),
         ('file_case', spec['url'].replace('l10406', 'L10406'), []),
         ('directory_case', spec['url'].replace('ccivil_03', 'CCIVIL_03'), [])]
with tempfile.TemporaryDirectory(prefix='lexa-session-diagnostic-') as directory:
    body, header, cookies = [Path(directory)/name for name in ['body', 'header', 'cookies']]
    for name, url, extra in cases:
        check_url(url)
        command = [shutil.which('curl'), '--disable', '--silent', '--show-error', '--http1.1', '--compressed',
                   '--proto', '=https', '--connect-timeout', '8', '--max-time', '20', '--max-filesize', str(MAX_BYTES),
                   '--user-agent', USER_AGENT, '--header', 'Accept: text/html,application/xhtml+xml',
                   '--cookie', str(cookies), '--cookie-jar', str(cookies),
                   '--output', str(body), '--dump-header', str(header), '--write-out', '%{http_code}', *extra, url]
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=25, check=False)
            item = {'case': name, 'curl_exit': result.returncode, 'status': result.stdout.strip()}
            fields = response_headers(header.read_bytes())
            item['header_names'] = sorted(set(fields.keys()))
            if fields.get('Location'):
                target = urlsplit(fields['Location'])
                item['redirect'] = {'scheme': target.scheme, 'host': target.hostname, 'path': target.path}
            if result.returncode == 0 and body.exists() and body.stat().st_size <= MAX_BYTES:
                try:
                    item['articles'] = validate(parse_html(body.read_bytes(), fields.get_content_charset()), spec)
                    item['document_valid'] = True
                except ValueError:
                    item['document_valid'] = False
            print(json.dumps(item), flush=True)
        except (subprocess.TimeoutExpired, OSError, RuntimeError):
            print(json.dumps({'case': name, 'diagnostic_failed': True}), flush=True)
