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
    def test_documented_cpp_restart_restores_units_and_keeps_raw_provenance(self):
        body=('<p><s>Art. 406. Texto anterior.</s></p><p>Art. 497. Fim do bloco.</p>'
            '<p><a name="livroiitituloicapituloii">CAPÍTULO II</a></p>'
            '<p><a name="art406">Art. 406. Nova redação.</a></p>'
            '<p><s>§ 1º Parágrafo anterior.</s></p><p><s>I - Inciso anterior;</s></p>'
            '<p><s>a) alínea anterior;</s></p><p><s>Pena - multa.</s></p>'
            '<p><s><a name="art498">Art. 498. Trecho recuperado.</a> '
            '<a href="https://www.planalto.gov.br/lei.htm#art1">(Redação dada pela Lei nº 1)</a></s></p>')
        raw=source(body)
        old=previous_blocks('cpp','test.html',raw,{'406','497','498'},documented_restarts=False)
        current=previous_blocks('cpp','test.html',raw,{'406','497','498'})
        self.assertEqual(len(old['records']),1)
        self.assertEqual([r['part'] for r in current['records']],['caput','paragraph','item','letter','penalty','caput'])
        self.assertTrue(all(r['articleId']=='406' for r in current['records'][1:-1]))
        self.assertEqual(current['records'][3]['unitLabel'],'§ 1 · inciso I · alínea a')
        recovered=current['records'][-1]
        self.assertEqual(recovered['articleId'],'498')
        self.assertEqual(recovered['notes'],['(Redação dada pela Lei nº 1)'])
        self.assertIn('https://www.planalto.gov.br/lei.htm#art1',[r['href'] for r in recovered['evidence']['runs']])
        self.assertEqual(recovered['source']['sha256'],hashlib.sha256(raw).hexdigest())
        a,b=recovered['evidence']['charRange']
        self.assertEqual(decode(raw)[0][a:b],recovered['evidence']['rawHtml'])
        self.assertEqual(current['source']['numberingTransitions'][0]['kind'],'documented_restart')

    def test_restart_without_both_native_heading_and_article_anchor_stays_blocked(self):
        for heading,anchor in [('', 'art406'),('<p>CAPÍTULO II</p>','art406'),
                ('<p><a name="capituloii">CAPÍTULO II</a></p>','other-law-406')]:
            raw=source('<p><s>Art. 406. Anterior.</s></p><p>Art. 497. Final.</p>'+heading+
                '<p><s><a name="'+anchor+'">Art. 406. Não associar.</a></s></p><p><s>Art. 498. Também retido.</s></p>')
            with self.subTest(heading=heading,anchor=anchor):
                rows=previous_blocks('cpp','test.html',raw,{'406','497','498'})
                self.assertEqual([r['text'] for r in rows['records']],['Art. 406. Anterior.'])
                self.assertTrue(any('numbering_regression_or_later_document_region' in r['reasons'] for r in rows['excluded']))

    def test_other_law_quote_neither_advances_numbering_nor_leaks_units_or_penalty(self):
        raw=source('<p>Art. 1. Regra própria.</p>'
            '<blockquote><p><a name="capituloii">CAPÍTULO II</a></p>'
            '<p><s>Art. 337-E. Norma citada.</s></p><p><s>§ 1º Outro diploma.</s></p>'
            '<p><s>I - Outra norma;</s></p><p><s>a) outra alínea;</s></p>'
            '<p><s>Pena - multa da norma citada.</s></p></blockquote>'
            '<p><s>Pena - ainda sem novo artigo próprio.</s></p>'
            '<p><s><a name="art2">Art. 2. Própria recuperada.</a></s></p>')
        result=previous_blocks('licitacoes','test.html',raw,{'1','2','337-E'})
        self.assertEqual([r['text'] for r in result['records']],['Art. 2. Própria recuperada.'])
        self.assertTrue(all('blockquote' not in r['evidence']['contextTags'] for r in result['records']))

    def test_clt_approval_decree_has_its_own_scope(self):
        raw=source('<p><s>Art. 1. Decreto de aprovação.</s></p><p>Art. 2. Decreto.</p>'
            '<p>CONSOLIDAÇÃO DAS LEIS DO TRABALHO</p><p><a name="tituloi">TÍTULO I</a></p>'
            '<p><s><a name="art1.">Art. 1. Redação anterior da CLT.</a></s></p>')
        result=previous_blocks('clt','test.html',raw,{'1','2'})
        self.assertEqual([r['text'] for r in result['records']],['Art. 1. Redação anterior da CLT.'])
        self.assertEqual(result['source']['numberingTransitions'][0]['kind'],'approval_decree_separated')

    def test_penal_original_part_requires_proven_native_restart(self):
        original='<p><s>Art. 1. Original.</s></p><p><s>Art. 120. Original final.</s></p>'
        native='<p><a name="partegeral.">PARTE GERAL</a></p><p><a name="art1.">Art. 1. Posterior.</a></p>'
        result=previous_blocks('penal','test.html',source(original+native),{'1','120'})
        self.assertEqual(result['records'],[])
        ambiguous=previous_blocks('penal','test.html',source(original+native.replace('name="partegeral."','name="unrelated"')),{'1','120'})
        self.assertEqual(ambiguous['records'],[])

    def test_penal_original_4_and_5_never_match_reorganized_articles_or_borrow_notes(self):
        original=('<p><s>Art. 1. Original.</s></p>'
            '<p><s>Art. 4. Aplicação territorial.</s></p>'
            '<p><s>Art. 5. Crimes no estrangeiro.</s></p>'
            '<p><s>Art. 116. Texto idêntico.</s></p><p>Art. 120. Fim.</p>')
        later=('<p><a name="partegeral.">PARTE GERAL</a></p>'
            '<p><a name="art1.">Art. 1. Posterior.</a></p>'
            '<p>Art. 4. Tempo do crime.</p><p>Art. 5. Territorialidade.</p>'
            '<p><s>Art. 116. Texto idêntico. (Redação dada pela Lei nº 1)</s></p>')
        rows=previous_blocks('penal','test.html',source(original+later),{'1','4','5','116','120'})['records']
        self.assertEqual([r['articleId'] for r in rows],['116'])
        self.assertEqual(rows[0]['notes'],['(Redação dada pela Lei nº 1)'])
        self.assertGreater(rows[0]['evidence']['block'],4)

    def test_constitution_and_adct_do_not_share_article_numbering(self):
        raw=source('<p><s>Art. 1. Constituição.</s></p><p>Art. 250. Final.</p>'
            '<blockquote><p>ATO DAS DISPOSIÇÕES CONSTITUCIONAIS TRANSITÓRIAS</p></blockquote>'
            '<p><s>Art. 1. ADCT.</s></p>')
        result=previous_blocks('cf','test.html',raw,{'1','250','adct-1'})
        self.assertEqual([r['articleId'] for r in result['records']],['1','adct-1'])

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
