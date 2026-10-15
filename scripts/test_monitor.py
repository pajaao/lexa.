import json
import tempfile
import unittest
from pathlib import Path
from urllib.error import URLError

from check_official_sources import ROOT, check_url, parse_html, validate, fingerprint, run


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
        for url in ['http://www.planalto.gov.br/', 'https://example.com/', 'https://user:pass@www.planalto.gov.br/']:
            with self.assertRaises(ValueError):
                check_url(url)

    def test_validator_against_the_entire_pdf_derived_corpus(self):
        # Synthetic HTML from the supplied PDF extraction, not a claim of live
        # source connectivity. Exercises coverage with all actual article IDs.
        from html import escape
        content = (ROOT/'content.js').read_text()
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


if __name__ == '__main__':
    unittest.main()
