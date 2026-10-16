"""Ordinary Chromium transport for the public STF pages.

No personal browser profile, stealth patches, CAPTCHA solving or ignored TLS
errors. Denied responses stop the capture and leave diagnostics for review.
"""
from pathlib import Path
from urllib.parse import urlsplit
import json

from official_http import SourceFetchError, check_url

HOSTS = frozenset({'portal.stf.jus.br', 'www.stf.jus.br'})


class STFBrowser:
    def __init__(self, evidence, executable_path=None):
        self.evidence = Path(evidence)
        self.executable_path = executable_path
        self.runtime = self.browser = self.context = self.page = None
        self.blocked_hosts = set()

    def __enter__(self):
        from playwright.sync_api import sync_playwright
        self.evidence.mkdir(parents=True, exist_ok=True)
        self.runtime = sync_playwright().start()
        try:
            options = {'headless': True}
            if self.executable_path:
                options['executable_path'] = self.executable_path
            self.browser = self.runtime.chromium.launch(**options)
            self.context = self.browser.new_context(locale='pt-BR', accept_downloads=False, service_workers='block')
            self.context.route('**/*', self.guard)
            self.page = self.context.new_page()
            return self
        except Exception:
            self.__exit__(None, None, None)
            raise

    def guard(self, route):
        try:
            check_url(route.request.url, HOSTS)
        except ValueError:
            self.blocked_hosts.add(urlsplit(route.request.url).hostname or '(sem host)')
            route.abort()
        else:
            route.continue_()

    def diagnose(self, url, status, error):
        report = {'transport': 'chromium', 'url': url, 'status': status,
                  'error': str(error)[:2000], 'blocked_resource_hosts': sorted(self.blocked_hosts)}
        if self.browser:
            report['browser_version'] = self.browser.version
        if self.page:
            try:
                report['title'] = self.page.title()
                self.evidence.joinpath('access-diagnostic.html').write_text(self.page.content()[:2 * 1024 * 1024])
                self.page.screenshot(path=str(self.evidence / 'access-diagnostic.png'), timeout=5000)
            except Exception:
                report['page_capture'] = 'indisponível'
        self.evidence.joinpath('access-diagnostic.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')

    def fetch(self, url):
        check_url(url, HOSTS)
        status = None
        try:
            response = self.page.goto(url, wait_until='domcontentloaded', timeout=30000)
            if response is None:
                raise SourceFetchError('Navegação sem resposta HTTP verificável.')
            status = response.status
            check_url(self.page.url, HOSTS)
            if status != 200:
                raise SourceFetchError(f'Falha HTTP {status} no Chromium; a fonte não foi validada.')
            self.page.wait_for_function(r"document.body && /S[uú]mulas?\s+Vinculantes?/i.test(document.body.innerText)", timeout=12000)
            # Allow ordinary page scripts to complete their initial updates. The
            # importer still requires full coverage and validates content volume.
            self.page.wait_for_timeout(400)
            raw = self.page.content().encode('utf-8')
            if len(raw) > 12 * 1024 * 1024:
                raise SourceFetchError('Documento ultrapassa o limite de tamanho.')
            return raw, 'utf-8'
        except Exception as error:
            self.diagnose(url, status, error)
            if isinstance(error, SourceFetchError):
                raise
            raise SourceFetchError('Falha ao abrir a página no Chromium; consulte access-diagnostic.json.') from error

    def __exit__(self, *_):
        if self.browser:
            self.browser.close()
        if self.runtime:
            self.runtime.stop()
