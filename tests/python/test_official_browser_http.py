import base64
import json
from pathlib import Path
import subprocess
import types
import unittest
from unittest.mock import Mock, patch

import official_browser_http as client
from official_http import SourceFetchError, fetch


URL = 'https://www.planalto.gov.br/lei.htm'
RAW = b'<p>Art. 1\xba A\xe7\xe3o.</p>'


class BrowserTransportTests(unittest.TestCase):
    def browser(self, responses, extra_request=None):
        session = Mock()
        page = Mock()
        browser = Mock()
        context = browser.new_context.return_value
        context.new_page.return_value = page
        context.new_cdp_session.return_value = session
        callbacks = {}
        session.on.side_effect = lambda name, callback: callbacks.update({name: callback})
        def send(method, params=None):
            if method == 'Fetch.takeResponseBodyAsStream':
                return {'stream': 'stream'}
            if method == 'IO.read':
                return {'data': base64.b64encode(RAW).decode(), 'base64Encoded': True, 'eof': True}
            return {}
        session.send.side_effect = send
        responses = iter(responses)
        def navigate(url, **kwargs):
            callback = callbacks['Fetch.requestPaused']
            request = {'requestId': 'request', 'resourceType': 'Document', 'request': {'url': url}}
            callback(request)
            if extra_request:
                callback({'requestId': 'resource', 'resourceType': 'Script', 'request': {'url': extra_request}})
            status, headers = next(responses)
            callback({**request, 'responseStatusCode': status, 'responseHeaders': [
                {'name': name, 'value': value} for name, value in headers.items()]})
            raise RuntimeError('navigation intentionally aborted')
        page.goto.side_effect = navigate
        playwright = Mock()
        playwright.chromium.launch.return_value = browser
        manager = Mock()
        manager.__enter__ = Mock(return_value=playwright)
        manager.__exit__ = Mock(return_value=False)
        module = types.ModuleType('playwright.sync_api')
        module.sync_playwright = Mock(return_value=manager)
        return module, playwright, browser, context, page, session

    def collect(self, responses, extra_request=None):
        setup = self.browser(responses, extra_request)
        with patch.dict('sys.modules', {'playwright.sync_api': setup[0]}):
            result = client.collect(URL)
        return result, setup

    def test_raw_response_preserves_non_utf8_bytes_without_executing_page(self):
        result, setup = self.collect([(200, {'Content-Type': 'text/html; charset=windows-1252'})], URL+'/script.js')
        self.assertEqual(result, (RAW, 'windows-1252'))
        _, playwright, browser, context, page, session = setup
        browser.new_context.assert_called_once_with(java_script_enabled=False, service_workers='block', accept_downloads=False)
        self.assertNotIn('ignore_https_errors', browser.new_context.call_args.kwargs)
        browser.close.assert_called_once()
        self.assertTrue(any(c.args == ('Fetch.failRequest', {'requestId': 'resource', 'errorReason': 'Aborted'}) for c in session.send.call_args_list))
        self.assertFalse(any(c.args == ('Fetch.continueRequest', {'requestId': 'resource'}) for c in session.send.call_args_list))
        page.goto.assert_called_once_with(URL, wait_until='commit', timeout=25000)

    def test_official_relative_redirect_is_checked_then_followed(self):
        result, setup = self.collect([(302, {'Location': '/new.htm'}), (200, {'Content-Type': 'text/html'})])
        self.assertEqual(result[0], RAW)
        self.assertEqual([c.args[0] for c in setup[4].goto.call_args_list], [URL, 'https://www.planalto.gov.br/new.htm'])

    def test_unsafe_redirects_are_never_contacted(self):
        for target in ['https://gov.br/planalto', 'http://www.planalto.gov.br/lei.htm',
                       'https://user:password@www.planalto.gov.br/', 'https://www.planalto.gov.br:8443/']:
            with self.subTest(target=target):
                setup = self.browser([(302, {'Location': target})])
                with patch.dict('sys.modules', {'playwright.sync_api': setup[0]}):
                    with self.assertRaises(ValueError):
                        client.collect(URL)
                self.assertEqual(setup[4].goto.call_count, 1)
                setup[2].close.assert_called_once()

    def test_redirect_loop_is_bounded(self):
        setup = self.browser([(302, {'Location': URL})]*4)
        with patch.dict('sys.modules', {'playwright.sync_api': setup[0]}):
            with self.assertRaisesRegex(SourceFetchError, 'Limite de redirecionamentos'):
                client.collect(URL)
        self.assertEqual(setup[4].goto.call_count, 4)

    def test_http_status_and_type_are_validated_before_body(self):
        for status, headers in [(503, {'Retry-After': '10'}), (200, {'Content-Type': 'application/pdf'}),
                                (302, {}), (200, {'Content-Type': 'text/html', 'Content-Length': str(client.MAX_BYTES+1)})]:
            setup = self.browser([(status, headers)])
            with patch.dict('sys.modules', {'playwright.sync_api': setup[0]}):
                with self.assertRaises(SourceFetchError) as caught:
                    client.collect(URL)
            self.assertFalse(any(c.args[0] == 'Fetch.takeResponseBodyAsStream' for c in setup[5].send.call_args_list))
            if status == 503:
                self.assertTrue(caught.exception.retryable)
                self.assertEqual(caught.exception.retry_after, 10)

    def test_stream_enforces_limit_without_content_length_and_closes(self):
        session = Mock()
        session.send.side_effect = [{'data': 'abcd'}, {'data': 'e', 'eof': True}, {}]
        with patch.object(client, 'MAX_BYTES', 4):
            with self.assertRaisesRegex(SourceFetchError, 'limite de tamanho'):
                client.read_stream(session, 'stream')
        self.assertEqual(session.send.call_args_list[-1].args, ('IO.close', {'handle': 'stream'}))
        self.assertEqual(session.send.call_args_list[1].args[1]['size'], 1)

    def test_tls_or_navigation_error_does_not_fall_back_to_insecure_access(self):
        setup = self.browser([])
        setup[4].goto.side_effect = RuntimeError('certificate error with private diagnostic')
        with patch.dict('sys.modules', {'playwright.sync_api': setup[0]}):
            with self.assertRaisesRegex(SourceFetchError, 'navegação HTTPS') as caught:
                client.collect(URL)
        self.assertFalse(caught.exception.retryable)
        self.assertNotIn('private', str(caught.exception))
        setup[2].close.assert_called_once()

    def test_worker_timeout_is_bounded_and_transient(self):
        with patch.object(client.subprocess, 'run', side_effect=subprocess.TimeoutExpired('worker', 40)) as run:
            with self.assertRaises(SourceFetchError) as caught:
                client.download_once(URL)
        self.assertTrue(caught.exception.retryable)
        self.assertEqual(run.call_args.kwargs['timeout'], 40)

    def test_worker_returns_exact_bytes_and_never_publishes_stderr(self):
        def worker(command, **kwargs):
            directory = Path(command[4])
            (directory/'metadata.json').write_text(json.dumps({'ok': True, 'charset': 'windows-1252'}))
            (directory/'body').write_bytes(RAW)
            return subprocess.CompletedProcess(command, 0, b'', b'private')
        with patch.object(client.subprocess, 'run', side_effect=worker):
            self.assertEqual(client.download_once(URL), (RAW, 'windows-1252'))
        with patch.object(client.subprocess, 'run', return_value=subprocess.CompletedProcess([], 1, b'', b'private')):
            with self.assertRaises(SourceFetchError) as caught:
                client.download_once(URL)
        self.assertNotIn('private', str(caught.exception))

    def test_selected_client_keeps_shared_retry_policy(self):
        downloader = Mock(side_effect=[SourceFetchError('HTTP 503', retryable=True, retry_after=3), (RAW, None)])
        sleep = Mock()
        self.assertEqual(fetch({'url': URL}, downloader=downloader, sleeper=sleep), (RAW, None))
        sleep.assert_called_once_with(3)


if __name__ == '__main__':
    unittest.main()
