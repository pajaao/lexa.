from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock
import json
import unittest

from official_http import SourceFetchError
from stf_browser import STFBrowser

URL = 'https://portal.stf.jus.br/jurisprudencia/sumariosumulas.asp?base=26'


class STFBrowserTests(unittest.TestCase):
    def transport(self, path, status=200):
        browser = STFBrowser(path)
        browser.page = Mock()
        browser.browser = Mock(version='fixture')
        browser.page.url = URL
        browser.page.goto.return_value.status = status
        browser.page.content.return_value = '<h1>Súmulas Vinculantes</h1>'
        browser.page.title.return_value = 'STF'
        return browser

    def test_success_reads_rendered_html_and_waits_for_content(self):
        with TemporaryDirectory() as path:
            browser = self.transport(path)
            raw, codec = browser.fetch(URL)
            self.assertEqual(codec, 'utf-8')
            self.assertIn('Súmulas Vinculantes', raw.decode())
            browser.page.wait_for_function.assert_called_once()
            self.assertFalse((Path(path) / 'access-diagnostic.json').exists())

    def test_403_is_never_imported_or_retried_and_has_diagnostics(self):
        with TemporaryDirectory() as path:
            browser = self.transport(path, 403)
            with self.assertRaisesRegex(SourceFetchError, '403'):
                browser.fetch(URL)
            browser.page.wait_for_function.assert_not_called()
            browser.page.goto.assert_called_once()
            report = json.loads((Path(path) / 'access-diagnostic.json').read_text())
            self.assertEqual(report['status'], 403)
            self.assertEqual(report['url'], URL)
            browser.page.screenshot.assert_called_once()

    def test_unexpected_navigation_and_nonofficial_resources_are_blocked(self):
        browser = STFBrowser('/unused')
        route = Mock()
        route.request.url = 'https://example.com/script.js'
        browser.guard(route)
        route.abort.assert_called_once()
        route.continue_.assert_not_called()
        route.request.url = URL
        browser.guard(route)
        route.continue_.assert_called_once()
        with self.assertRaises(ValueError):
            browser.fetch('http://portal.stf.jus.br/')


if __name__ == '__main__':
    unittest.main()
