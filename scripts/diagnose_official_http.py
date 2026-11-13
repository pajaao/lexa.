"""Read-only, bounded diagnosis; never follow a redirect or write legal data."""
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlsplit
from official_http import response_headers, USER_AGENT

agents = [USER_AGENT, 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36', 'curl/8.5.0']
for host in ['www.planalto.gov.br', 'planalto.gov.br']:
    for i, agent in enumerate(agents):
        with tempfile.TemporaryDirectory() as folder:
            header = Path(folder)/'headers'
            body = Path(folder)/'body'
            url = 'https://'+host+'/ccivil_03/leis/2002/l10406compilada.htm'
            result = subprocess.run(['curl', '--disable', '--silent', '--show-error', '--proto', '=https', '--http1.1', '--max-time', '25', '--max-filesize', '12582912', '--user-agent', agent, '--header', 'Accept: text/html,application/xhtml+xml', '--header', 'Accept-Language: pt-BR,pt;q=0.9', '--output', str(body), '--dump-header', str(header), '--write-out', '%{http_code}', url], capture_output=True, text=True, timeout=30)
            try:
                headers = response_headers(header.read_bytes()) if header.exists() else {}
            except Exception:
                headers = {}
            location = urlsplit(headers.get('Location', ''))
            print(host, 'agent', i, 'curl', result.returncode, 'status', result.stdout, 'redirect', location.scheme, location.hostname, location.path, flush=True)
