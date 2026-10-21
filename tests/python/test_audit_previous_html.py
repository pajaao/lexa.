import sys
import json
import hashlib
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'scripts'))
from audit_previous_html import coverage
from extract_previous_html import prepare_document, decode


def document(body):
    return ('<!-- saved from url=(0050)https://www.planalto.gov.br/test.htm -->'
        '<meta charset="utf-8">'+body).encode()


from saved_html_source import source_path


class Coverage(unittest.TestCase):
    def test_saved_ledger_keeps_source_hashes_ranges_and_unique_ids(self):
        root = Path(__file__).resolve().parents[2]
        path = root/'experiments/html-history/safeguards/coverage.json'
        if not path.exists():
            self.skipTest('Run the experimental coverage audit first')
        ledger = json.loads(path.read_text(encoding='utf-8'))
        self.assertFalse(ledger['publicationAllowed'])
        ids = set()
        self.assertEqual(len(ledger['sources']), 13)
        for source in ledger['sources']:
            raw = source_path(source['file'],source['sha256']).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), source['sha256'])
            text = decode(raw)[0]
            self.assertEqual(source['detectedStruckBlocks'], len(source['entries']))
            for entry in source['entries']:
                self.assertNotIn(entry['id'], ids)
                ids.add(entry['id'])
                a,b = entry['charRange']
                self.assertEqual(text[a:b], entry['rawHtml'])
                self.assertTrue(entry['decisions'])
                self.assertTrue(any(r['deleted'] and r['text'].strip() for r in entry['runs']))

    def test_unrecognized_partial_and_ordinal_are_preserved(self):
        raw = document('<p><s>Texto sem marcador.</s></p>'
            '<p>Art. 1. Texto <s>parcial</s>.</p><p>§ 1<s>º</s> Regra.</p>')
        result = prepare_document('civil', 'example.html', raw)
        ledger = coverage('civil', 'example.html', raw, result)
        self.assertEqual(ledger['detectedStruckBlocks'], 3)
        self.assertEqual(ledger['blocksByDisposition'], {'unassociated': 3})
        source = decode(raw)[0]
        for entry in ledger['entries']:
            a,b = entry['charRange']
            self.assertEqual(source[a:b], entry['rawHtml'])

    def test_prepared_and_excluded_remain_distinguishable(self):
        raw = document('<p><s>Art. 1. Antigo.</s></p>'
            '<p>Art. 1. Novo. (Redação dada pela Lei nº 1)</p>'
            '<p><s>Art. 2. (VETADO).</s></p>')
        result = prepare_document('civil', 'example.html', raw)
        ledger = coverage('civil', 'example.html', raw, result)
        self.assertEqual(ledger['blocksByDisposition'], {'prepared': 1, 'excluded': 1})
        self.assertEqual(ledger['entries'][0]['decisions'][0]['recordId'], result['records'][0]['id'])
        self.assertTrue(ledger['entries'][1]['decisions'][0]['reasons'])

    def test_duplicate_evidence_is_accounted_without_new_records(self):
        raw = document('<p><s>Art. 1. Antigo.</s></p>'
            '<p>Art. 1. Novo. (Redação dada pela Lei nº 1)</p>')
        existing = prepare_document('civil', 'example.html', raw)['records']
        result = prepare_document('civil', 'example.html', raw, existing)
        self.assertEqual(result['records'], [])
        self.assertEqual(coverage('civil', 'example.html', raw, result)
            ['blocksByDisposition'], {'duplicate_evidence': 1})


if __name__ == '__main__':
    unittest.main()
