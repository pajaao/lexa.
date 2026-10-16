"""Synthetic HTML fixtures test failures; they are not evidence of live STF access."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import copy
import json
import unittest

from check_stf_sources import INDEX, HOSTS, digest, individual_url, parse_index, parse_item, run
from import_official import load_js
from official_http import check_url

URL = INDEX + '&sumula=1185'


def html(number=1, body='Texto de teste do enunciado, com conteúdo suficientemente longo.', status='', note='Texto de precedente para conferência.', extra=''):
    return f'''<html><head><title>STF</title><script>malicioso()</script></head><body>
    <nav><p>Menu do portal</p></nav><h2>Súmula Vinculante {number}{status}</h2>
    <p>{body}</p><h3>Precedentes Representativos</h3><p>{note}</p>{extra}
    <h3>Observação</h3><p>Data de publicação do enunciado: DJE de 1-1-2026.</p>
    <p>Para informações adicionais, clique aqui.</p><footer>Rodapé fora da súmula</footer></body></html>'''.encode()


def seed(root):
    for folder in ['data/archive','data/official','data/history']:
        (root / folder).mkdir(parents=True,exist_ok=True)
    first = parse_item(html(), 1, URL)
    second = parse_item(html(2), 2, INDEX + '&sumula=1186')
    pdf = {'id': 'sv', 'short': 'SV · STF', 'name': 'Súmulas Vinculantes do STF', 'area': 'Súmulas',
           'kind': 'sumulas', 'source': {'kind': 'supplied_pdf'}, 'articles': [first, second]}
    (root / 'data/archive/sumulas.js').write_text('export const sumulas = ' + json.dumps([pdf]) + ';\n')
    (root / 'data/official/sumulas.js').write_text('export const officialSumulas = [];\n')
    (root / 'data/history/sumulas.js').write_text('export const sumulaUpdates = [];\n')
    return pdf


def fixture_fetch(overrides=None):
    files = {INDEX: b'<a href="?base=26&amp;sumula=1185">S\xc3\xbamula Vinculante 1</a><a href="?base=26&amp;sumula=1186">2</a>',
             URL: html(), INDEX + '&sumula=1186': html(2)}
    files.update(overrides or {})
    return lambda url: (files[url], 'utf-8')


class STFMonitorTests(unittest.TestCase):
    def test_index_discovers_new_number_and_preserves_known_coverage(self):
        raw = b'<a href="?base=26&amp;sumula=1185">1</a><a href="?base=26&amp;sumula=1186">2</a><a href="?base=26&amp;sumula=1500">3</a>'
        known = [{'number': '1', 'url': URL}, {'number': '2', 'url': INDEX + '&sumula=1186'}]
        self.assertEqual(list(parse_index(raw, known)), [1, 2, 3])
        for bad in [b'<p>Access denied</p>', raw.replace(b'>2</a>', b'>4</a>'), raw.replace(b'sumula=1186', b'sumula=1185')]:
            with self.assertRaises(ValueError):
                parse_index(bad, known)

    def test_only_stf_collection_links_and_verified_https_hosts(self):
        self.assertEqual(individual_url('?base=26&sumula=1185'), URL)
        for url in ['http://portal.stf.jus.br/?base=26&sumula=1185',
                    'https://evil.example/?base=26&sumula=1185',
                    INDEX.replace('base=26', 'base=30') + '&sumula=1185',
                    INDEX + '&sumula=1185&sumula=999']:
            with self.assertRaises(ValueError):
                individual_url(url)
        check_url(URL, HOSTS)
        with self.assertRaises(ValueError):
            check_url(URL)  # Planalto's monitor keeps its original scope.

    def test_statement_commentary_and_statuses_not_navigation(self):
        item = parse_item(html(9, status=' (cancelada)'), 9, URL)
        self.assertEqual(item['status'], 'cancelled')
        self.assertNotIn('precedente', item['paragraphs'][0]['runs'][0]['text'])
        joined = ' '.join(r['text'] for p in item['notes'] for r in p['runs'])
        self.assertIn('Data de publicação', joined)
        self.assertNotIn('Rodapé', joined)
        self.assertNotIn('malicioso', joined)
        with self.assertRaises(ValueError):
            parse_item(html(9), 9, URL, item)  # Cancellation cannot silently disappear.
        pending = b'<h2>S\xc3\xbamula Vinculante 30</h2><p>A S\xc3\xbamula Vinculante 30 est\xc3\xa1 pendente de publica\xc3\xa7\xc3\xa3o.</p>'
        self.assertEqual(parse_item(pending, 30, URL)['status'], 'pending')
        self.assertEqual(parse_item(html(1,status=' (suspensa)'), 1, URL)['status'], 'suspended')

    def test_truncation_wrong_title_and_ambiguous_pages_block_import(self):
        for bad in [html(2), b'<h2>S\xc3\xbamula Vinculante 1</h2><p>Bloqueio</p>',
                    html() + html(body='Outro enunciado completamente diferente do primeiro.')]:
            with self.assertRaises(ValueError):
                parse_item(bad, 1, URL)
        previous = parse_item(html(note='Precedente longo. ' * 100), 1, URL)
        with self.assertRaises(ValueError):
            parse_item(html(), 1, URL, previous)

    def test_complete_capture_is_stable_and_history_detects_notes_status_and_new_entries(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            seed(root)
            candidate, report = run(root, fixture_fetch(), sleeper=lambda _: None, now='2026-10-16T12:00:00+00:00')
            self.assertTrue(report['first_official_capture'])
            history = load_js(root / 'data/history/sumulas.js', 'sumulaUpdates')
            self.assertEqual(history[0]['kind'], 'baseline')
            self.assertEqual(history[0]['changes'], [])
            tracked = ['data/official/sumulas.js', 'data/history/sumulas.js', 'monitor/stf/index.json', 'monitor/stf/items/1.json']
            before = {path: (root / path).read_bytes() for path in tracked}
            run(root, fixture_fetch(), sleeper=lambda _: None, now='2026-10-17T12:00:00+00:00')
            self.assertEqual(before, {path: (root / path).read_bytes() for path in tracked})
            new_index = b'<a href="?base=26&amp;sumula=1185">1</a><a href="?base=26&amp;sumula=1186">2</a><a href="?base=26&amp;sumula=1500">3</a>'
            changed = fixture_fetch({INDEX: new_index, URL: html(status=' (cancelada)', note='Novo precedente de teste.'), INDEX + '&sumula=1500': html(3)})
            candidate, _ = run(root, changed, sleeper=lambda _: None)
            event = load_js(root / 'data/history/sumulas.js', 'sumulaUpdates')[-1]
            self.assertEqual([c['type'] for c in event['changes']], ['changed', 'added'])
            self.assertEqual(event['changes'][0]['kind'], 'vinculante')
            self.assertIn('Cancelada', event['changes'][0]['after']['title'])
            self.assertEqual(len(candidate['articles']), 3)
            self.assertEqual(json.loads((root / 'monitor/stf/items/3.json').read_text())['semantic_sha256'], digest(candidate['articles'][2]))

    def test_mid_capture_failure_changes_no_tracked_candidates(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            seed(root)
            run(root, fixture_fetch(), sleeper=lambda _: None)
            before = {str(path.relative_to(root)): path.read_bytes() for path in root.rglob('*') if path.is_file() and 'run' not in path.parts}
            broken = fixture_fetch({INDEX + '&sumula=1186': b'<h1>Access denied</h1>'})
            with self.assertRaises(ValueError):
                run(root, broken, sleeper=lambda _: None)
            after = {str(path.relative_to(root)): path.read_bytes() for path in root.rglob('*') if path.is_file() and 'run' not in path.parts}
            self.assertEqual(before, after)
            self.assertEqual(json.loads((root / 'monitor/run/stf/report.json').read_text())['status'], 'failed')


if __name__ == '__main__':
    unittest.main()
