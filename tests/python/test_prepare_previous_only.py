import sys
from pathlib import Path
import unittest
import json
import hashlib

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from prepare_previous_only import previous_blocks
from extract_previous_html import decode,split_notes


def source(body):
    return ('<!-- saved from url=(0050)https://www.planalto.gov.br/test.htm -->'
        '<meta charset="utf-8">'+body).encode()


from saved_html_source import source_path


class PreviousOnly(unittest.TestCase):
    def test_generated_previous_only_fixture_preserves_local_text_and_hashes(self):
        root=Path(__file__).resolve().parents[2]
        fixture=root/'tests/fixtures/previous-wordings-html.json'
        if not fixture.exists():
            self.skipTest('Prepare the local fixture first')
        rows=json.loads(fixture.read_text(encoding='utf-8'))['records']
        sources={}
        ids=set()
        for row in rows:
            self.assertNotIn(row['id'],ids)
            ids.add(row['id'])
            self.assertEqual(row['wording']['status'],'previous')
            self.assertEqual(row['review']['status'],'pending')
            name=row['source']['document']
            key=(name,row['source']['sha256'])
            if key not in sources:
                raw=source_path(*key).read_bytes()
                sources[key]=(decode(raw)[0],hashlib.sha256(raw).hexdigest())
            text,digest=sources[key]
            self.assertEqual(row['source']['sha256'],digest)
            a,b=row['evidence']['charRange']
            self.assertEqual(text[a:b],row['evidence']['rawHtml'])
            self.assertEqual(split_notes(row['evidence']['rawText'])[0],row['text'])
        caputs=[r['text'] for r in rows if r['codeId']=='penal' and r['articleId']=='216' and r['part']=='caput']
        self.assertEqual(len(caputs),2)
        self.assertTrue(any('mulher honesta' in t for t in caputs))
        self.assertTrue(any('Induzir alguém' in t for t in caputs))
        self.assertTrue(all('superior hierárquico' not in t for t in caputs))

    def prepare(self,body):
        return previous_blocks('penal','test.html',source(body),{'1','2','216','216-A'})

    def test_previous_does_not_require_replacement_reference_or_date(self):
        rows=self.prepare('<p><s>Art. 1. Texto anterior.</s></p>')['records']
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['wording']['status'],'previous')
        self.assertEqual(rows[0]['review']['status'],'pending')
        self.assertIsNone(rows[0]['reference'])

    def test_revoked_article_keeps_actual_previous_text_but_not_placeholder(self):
        rows=self.prepare('<p><s>Art. 216. Texto antigo. (Revogado pela Lei nº 1)</s></p>'
            '<p>Art. 216-A. Texto diferente.</p>')['records']
        self.assertEqual([(r['articleId'],r['text']) for r in rows],[('216','Art. 216. Texto antigo.')])
        self.assertEqual(rows[0]['notes'],['(Revogado pela Lei nº 1)'])
        self.assertEqual(self.prepare('<p><s>Art. 1. (Revogado pela Lei nº 1)</s></p>')['records'],[])
        rows=self.prepare('<p>Art. 1. Regra.</p><p><s>§ 1º (VETADO).</s></p><p><s>I - (VETADO):</s></p>')['records']
        self.assertEqual(rows,[])

    def test_mixed_truncated_and_unstruck_are_not_previous_wordings(self):
        for body in ['<p>Art. 1. Atual.</p>','<p><s>Art. 1. Sem final</s></p>',
                     '<p>Art. 1. Palavra <s>isolada</s>.</p>']:
            self.assertEqual(self.prepare(body)['records'],[])

    def test_plain_unit_marker_does_not_make_struck_body_mixed(self):
        rows=self.prepare('<p>Art. 1. <s>Redação anterior.</s></p>')['records']
        self.assertEqual([r['text'] for r in rows],['Art. 1. Redação anterior.'])
        self.assertEqual(self.prepare('<p>Art. 1. Texto <s>parcial</s>.</p>')['records'],[])

    def test_penalty_is_preserved_without_borrowing_replacement(self):
        rows=self.prepare('<p><s>Art. 1. Antes: Pena - multa.</s></p>'
            '<p><s>Pena - reclusão.</s></p>')['records']
        self.assertEqual([r['text'] for r in rows],['Art. 1. Antes: Pena - multa.','Pena - reclusão.'])
        self.assertEqual([r['part'] for r in rows],['article','penalty'])


if __name__=='__main__':
    unittest.main()
