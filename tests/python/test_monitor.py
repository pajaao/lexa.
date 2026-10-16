import json
import tempfile
import unittest
from unittest.mock import Mock, patch
from pathlib import Path
from urllib.error import URLError

from check_official_sources import ROOT, check_url, parse_html, validate, fingerprint, run
from official_http import SourceFetchError, download_once, fetch, response_headers, retry_delay
import subprocess


SPEC = {'id': 'civil', 'name': 'Teste', 'url': 'https://www.planalto.gov.br/lei.htm',
        'identity': 'Lei 10.406', 'last_article': 3, 'min_characters': 40}
HTML = '''<!doctype html><meta charset="utf-8"><h1>Lei 10.406</h1>
<p>Art. 1º Toda pessoa é capaz de direitos.</p>
<p>Art. 2º <strike>Redação anterior.</strike> Redação substituta.</p>
<p>Art. 3º São protegidas as pessoas.</p>'''.encode()


class MonitorTests(unittest.TestCase):
    def test_whitespace_and_innocuous_markup_do_not_create_false_change(self):
        one = parse_html(b'<p>Art. 1 Texto  de <b>exemplo</b>.</p>')
        two = parse_html(b'<p>Art. 1\nTexto de exemplo.</p>')
        self.assertEqual(fingerprint(one), fingerprint(two))

    def test_scripts_hidden_content_and_ordinals(self):
        doc = parse_html(b'<head><title>Ignore</title></head><p>Art. 1<sup>o</sup> Texto.</p><script>doNotExecute()</script><p hidden>SEGREDO</p>')
        text = json.dumps(doc)
        self.assertIn('Art. 1o Texto.', text)
        self.assertNotIn('doNotExecute', text)
        self.assertNotIn('SEGREDO', text)
        self.assertNotIn('Ignore', text)

    def test_deleted_text_and_styles_are_detected(self):
        before = parse_html(b'<p>Art. 1 Texto anterior.</p>')
        after = parse_html(b'<p>Art. 1 <s>Texto anterior.</s></p>')
        styled = parse_html(b'<p>Art. 1 <span style="text-decoration:line-through">Texto anterior.</span></p>')
        self.assertNotEqual(fingerprint(before), fingerprint(after))
        self.assertEqual(fingerprint(after), fingerprint(styled))
        css = parse_html(b'<style>.old{text-decoration:line-through}</style><p>Art. 1 Texto.</p>')
        self.assertEqual(len(css['deletion_styles']), 1)

    def test_encoding_and_invalid_document(self):
        raw = '<meta charset="iso-8859-1"><p>Ação</p>'.encode('cp1252')
        self.assertIn('Ação', json.dumps(parse_html(raw), ensure_ascii=False))
        with self.assertRaises(ValueError):
            validate(parse_html(b'<h1>Access denied</h1>'), SPEC)
        with self.assertRaises(ValueError):
            validate(parse_html(HTML.replace(b'Art. 2', b'Paragrafo 2')), SPEC)

    def test_ranges_and_adct_have_separate_coverage(self):
        spec = {**SPEC, 'id': 'cf', 'last_adct_article': 2}
        raw = ('<h1>Lei 10.406</h1><p>Arts. 1 a 3. Revogados.</p><h2>ATO DAS DISPOSIÇÕES CONSTITUCIONAIS TRANSITÓRIAS</h2>'
               '<p>Art. 1º Primeiro artigo transitório.</p><p>Art. 2º Segundo artigo transitório.</p>').encode()
        self.assertEqual(validate(parse_html(raw), spec), {'main': 3, 'adct': 2})
        with self.assertRaises(ValueError):
            validate(parse_html(raw.replace(b'Art. 2', b'Nota 2')), spec)

    def test_legacy_page_without_charset_and_struck_leading_whitespace(self):
        raw = ('<h1>Lei 10.406</h1><p><span> </span><strike> Art 1. Redação revogada.</strike></p>'
               '<p><strike> </strike> Art. 2º Ação de proteção.</p>'
               '<p>Art. 3º São protegidas as pessoas.</p>').encode('cp1252')
        document = parse_html(raw)
        self.assertEqual(validate(document, SPEC), {'main': 3})
        self.assertIn('Ação', json.dumps(document, ensure_ascii=False))
        with self.assertRaises(ValueError):
            parse_html(raw, 'utf-8') # An explicit contradictory charset must not be ignored.

    def test_constitution_adct_link_in_the_top_index_does_not_change_scope(self):
        spec = {**SPEC, 'id': 'cf', 'last_adct_article': 2}
        raw = ('<h1>Lei 10.406</h1><p><a href="#adct">Ato das Disposições Constitucionais Transitórias</a></p>'
               '<p>Art. 1º Primeiro artigo constitucional.</p><p>Art. 2º Segundo artigo constitucional.</p>'
               '<p>Art. 3º Terceiro artigo constitucional.</p><h2>ATO DAS DISPOSIÇÕES CONSTITUCIONAIS TRANSITÓRIAS</h2>'
               '<p>Art. 1º Primeiro artigo transitório.</p><p>Art. 2º Segundo artigo transitório.</p>').encode()
        self.assertEqual(validate(parse_html(raw), spec), {'main': 3, 'adct': 2})

    def test_first_capture_unchanged_run_and_real_change(self):
        with tempfile.TemporaryDirectory() as directory:
            base, evidence = Path(directory)/'official', Path(directory)/'run'
            first = run([SPEC], base, evidence, fetcher=lambda _: (HTML, None), checked_at='2026-10-15T00:00:00+00:00')
            self.assertEqual(first['results'][0]['status'], 'initial_capture')
            stored = (base/'civil.json').read_bytes()
            second = run([SPEC], base, evidence, fetcher=lambda _: (HTML, None), checked_at='2026-10-16T00:00:00+00:00')
            self.assertEqual(second['changed_count'], 0)
            self.assertEqual((base/'civil.json').read_bytes(), stored)
            self.assertFalse((evidence/'civil.diff.txt').exists())
            third = run([SPEC], base, evidence, fetcher=lambda _: (HTML.replace(b'protegidas', b'respeitadas'), None))
            self.assertEqual(third['results'][0]['status'], 'changed')
            self.assertIn('respeitadas', (evidence/'civil.diff.txt').read_text())
            self.assertFalse(third['published_reading_data_changed'])

    def test_failure_does_not_advance_baselines_or_reuse_old_evidence(self):
        second = {**SPEC, 'id': 'penal'}
        with tempfile.TemporaryDirectory() as directory:
            base, evidence = Path(directory)/'official', Path(directory)/'run'
            run([SPEC, second], base, evidence, fetcher=lambda _: (HTML, None))
            stored = {p.name: p.read_bytes() for p in base.glob('*.json')}
            def fetcher(spec):
                if spec['id'] == 'penal':
                    raise URLError('blocked')
                return HTML.replace(b'protegidas', b'respeitadas'), None
            result = run([SPEC, second], base, evidence, fetcher=fetcher)
            self.assertEqual(result['failed_count'], 1)
            self.assertFalse(result['baseline_written'])
            self.assertEqual(stored, {p.name:p.read_bytes() for p in base.glob('*.json')})
            self.assertFalse((evidence/'downloads/penal.html.txt').exists())
            self.assertTrue((evidence/'report.json').exists())

    def test_reject_migration_and_corrupt_baseline(self):
        with tempfile.TemporaryDirectory() as directory:
            base, evidence = Path(directory)/'official', Path(directory)/'run'
            run([SPEC], base, evidence, fetcher=lambda _: (HTML, None))
            baseline = json.loads((base/'civil.json').read_text())
            baseline['semantic_sha256'] = '0'*64
            (base/'civil.json').write_text(json.dumps(baseline))
            result = run([SPEC], base, evidence, fetcher=lambda _: (HTML, None))
            self.assertEqual(result['failed_count'], 1)
            self.assertIn('inconsistente', result['results'][0]['reason'])

    def test_redirect_destinations_require_official_https(self):
        check_url(SPEC['url'])
        for url in ['http://www.planalto.gov.br/', 'https://example.com/', 'https://user:pass@www.planalto.gov.br/', 'https://www.planalto.gov.br:8443/']:
            with self.assertRaises(ValueError):
                check_url(url)

    def test_validator_against_the_entire_pdf_derived_corpus(self):
        # Synthetic HTML from the supplied PDF extraction, not a claim of live
        # source connectivity. Exercises coverage with all actual article IDs.
        from html import escape
        content = (ROOT/'data/archive/legislation.js').read_text()
        imported = json.loads(content[len('export const imported = '):-2])
        specs = json.loads((ROOT/'monitor/sources.json').read_text())
        for spec in specs:
            with self.subTest(source=spec['id']):
                doc = imported[spec['id']]
                blocks = ['<h1>'+escape(spec['identity'])+'</h1>']
                adct = False
                for article in doc['articles']:
                    if article['scope'] == 'adct' and not adct:
                        blocks.append('<h2>ATO DAS DISPOSIÇÕES CONSTITUCIONAIS TRANSITÓRIAS</h2>')
                        adct = True
                    for paragraph in article['paragraphs']:
                        text = ''.join(escape(r['text']) for r in paragraph['runs'])
                        blocks.append('<p>'+text+'</p>')
                counts = validate(parse_html(''.join(blocks).encode()), spec)
                self.assertGreaterEqual(counts['main'], spec['last_article'])


class OfficialHTTPTests(unittest.TestCase):
    @staticmethod
    def response(command, status=200, headers=b'Content-Type: text/html; charset=utf-8\r\n', body=HTML, code=0):
        if not code:
            Path(command[command.index('--output')+1]).write_bytes(body)
            Path(command[command.index('--dump-header')+1]).write_bytes(
                b'HTTP/1.1 200 Connection established\r\n\r\nHTTP/1.1 '+str(status).encode()+b' Status\r\n'+headers+b'\r\n')
        return subprocess.CompletedProcess(command, code, str(status), 'potentially private proxy diagnostic')

    @patch('official_http.shutil.which', return_value='/usr/bin/curl')
    def test_retries_closed_connections_using_identified_http1_client(self, _):
        commands=[]
        def transfer(command, **kwargs):
            commands.append(command)
            return self.response(command, code=52 if len(commands)==1 else 0)
        sleeper=Mock()
        with patch('official_http.subprocess.run', side_effect=transfer):
            raw,encoding=fetch(SPEC,sleeper=sleeper)
        self.assertEqual(raw,HTML)
        self.assertEqual(encoding,'utf-8')
        self.assertEqual(len(commands),2)
        sleeper.assert_called_once_with(2)
        for cmd in commands:
            self.assertEqual(cmd[1],'--disable')
            self.assertIn('--http1.1',cmd)
            self.assertIn('--max-filesize',cmd)
            self.assertNotIn('--insecure',cmd)
            self.assertNotIn('-k',cmd)

    @patch('official_http.shutil.which', return_value='/usr/bin/curl')
    def test_redirect_checked_before_following(self, _):
        with patch('official_http.subprocess.run', side_effect=lambda cmd,**kw:self.response(cmd,status=302,headers=b'Location: https://example.com/\r\n')) as transfer:
            with self.assertRaises(ValueError):
                download_once(SPEC['url'])
            self.assertEqual(transfer.call_count,1)

    @patch('official_http.shutil.which', return_value='/usr/bin/curl')
    def test_tls_verification_failure_is_fatal_and_does_not_expose_proxy_details(self, _):
        sleeper=Mock()
        with patch('official_http.subprocess.run', side_effect=lambda cmd,**kw:self.response(cmd,code=60)) as transfer:
            with self.assertRaises(SourceFetchError) as caught:
                fetch(SPEC,sleeper=sleeper)
            self.assertEqual(transfer.call_count,1)
        self.assertNotIn('private proxy',str(caught.exception))
        sleeper.assert_not_called()

    def test_transient_failure_backoff_is_bounded(self):
        sleeper=Mock()
        with patch('official_http.download_once',side_effect=SourceFetchError('Conexão encerrada',retryable=True)) as transfer:
            with self.assertRaisesRegex(SourceFetchError,'Tentativas realizadas: 3'):
                fetch(SPEC,sleeper=sleeper)
            self.assertEqual(transfer.call_count,3)
        self.assertEqual([call.args[0] for call in sleeper.call_args_list],[2,4])

    def test_honors_retry_after_without_retrying_earlier_than_requested(self):
        sleeper=Mock()
        with patch('official_http.download_once',side_effect=[SourceFetchError('HTTP 503',retryable=True,retry_after=3),(HTML,'utf-8')]):
            self.assertEqual(fetch(SPEC,sleeper=sleeper),(HTML,'utf-8'))
        sleeper.assert_called_once_with(3)
        sleeper.reset_mock()
        with patch('official_http.download_once',side_effect=SourceFetchError('HTTP 429',retryable=True,retry_after=120)) as transfer:
            with self.assertRaisesRegex(SourceFetchError,'próxima execução'):
                fetch(SPEC,sleeper=sleeper)
            self.assertEqual(transfer.call_count,1)
        sleeper.assert_not_called()
        self.assertEqual(retry_delay('15'),15)
        self.assertIsNone(retry_delay('invalid'))

    @patch('official_http.shutil.which', return_value='/usr/bin/curl')
    def test_http_error_page_and_non_html_payload_are_rejected(self, _):
        for status,headers in [(503,b'Content-Type: text/html\r\n'),(200,b'Content-Type: application/pdf\r\n')]:
            with self.subTest(status=status):
                with patch('official_http.subprocess.run',side_effect=lambda cmd,**kw:self.response(cmd,status=status,headers=headers)):
                    with self.assertRaises(SourceFetchError):
                        download_once(SPEC['url'])


if __name__ == '__main__':
    unittest.main()
