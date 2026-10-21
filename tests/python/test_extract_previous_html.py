"""Boundary, nature and provenance checks independent of the PDF comparison."""
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
from extract_previous_html import prepare_document, EvidenceHTML, decode, split_notes, unit, row_key


def document(body):
    return ('<!-- saved from url=(0050)https://www.planalto.gov.br/test.htm -->'
            '<html><head><meta charset="utf-8"></head><body>'+body+'</body></html>').encode()


def newer(text='Art. 5. Texto novo.'):
    return '<p>'+text+' <a href="https://www.planalto.gov.br/lei.htm#art1">(Redação dada pela Lei nº 1, de 2000)</a></p>'


from saved_html_source import source_path


class Extraction(unittest.TestCase):
    def extract(self, body, existing=(), reader=None):
        return prepare_document('civil','example.html',document(body),existing,reader)

    def test_all_deletion_tags_and_inline_styles(self):
        for opening,closing in [('<strike>','</strike>'),('<del>','</del>'),('<s>','</s>'),
                                ('<span style="text-decoration:line-through">','</span>'),
                                ('<span style="text-decoration-line:line-through">','</span>')]:
            with self.subTest(opening=opening):
                result=self.extract('<p>'+opening+'Art. 5. Texto antigo.'+closing+'</p>'+newer())
                self.assertEqual([r['wording']['status'] for r in result['records']],['previous','current_candidate'])
                self.assertTrue(all(r['review']=={'status':'pending'} for r in result['records']))

    def test_empty_anchor_and_ordinal_are_not_previous_wordings(self):
        result=self.extract('<p>Art. 5. Regra.</p><p><strike><a name="p1"></a></strike>§ 1<s>º</s> Texto intacto.</p>')
        self.assertEqual(result['records'],[])

    def test_partial_strike_is_excluded(self):
        result=self.extract('<p>Art. 5. Texto <strike>parcialmente</strike> riscado.</p>'+newer())
        self.assertEqual(result['records'],[])

    def test_inline_penalty_does_not_become_part_of_caput(self):
        result=self.extract('<p><strike>Art. 5. Texto antigo: Pena - reclusão.</strike></p>'+newer())
        self.assertEqual(result['records'][0]['text'],'Art. 5. Texto antigo:')
        self.assertIn('Pena -',result['records'][0]['evidence']['rawText'])
        self.assertNotIn('Pena -',result['records'][0]['evidence']['rawUnitText'])

    def test_editorial_link_is_not_borrowed_from_next_version(self):
        result=self.extract('<p><strike><a name="art5old"></a>Art. 5. Texto antigo.</strike></p>'+newer())
        old,new=result['records']
        self.assertIsNone(old['reference'])
        self.assertEqual(new['evidence']['editorialNotes'][0]['links'],['https://www.planalto.gov.br/lei.htm#art1'])
        self.assertEqual(old['evidence']['anchors'],['art5old'])

    def test_parent_hierarchy_and_letter(self):
        body='<p>Art. 5. Regra:</p><p>§ 1º Enunciado:</p><p>I - item:</p><p><s>a) regra antiga;</s></p>'+newer('a) regra nova;')
        rows=self.extract(body)['records']
        self.assertEqual(len(rows),2)
        self.assertEqual(rows[0]['part'],'letter')
        self.assertEqual(rows[0]['unitLabel'],'§ 1 · inciso I · alínea a')
        self.assertEqual(unit('§ 2º-A. Texto.' )[2],'§ 2-A')

    def test_paragraph_with_children_is_not_exported_as_complete(self):
        body='<p>Art. 5. Regra.</p><p><s>§ 1º Antes:</s></p><p>I - anterior;</p>'+newer('§ 1º Depois:')+'<p>I - posterior;</p>'
        result=self.extract(body)
        self.assertEqual(result['records'],[])
        self.assertTrue(any('unit_has_unrepresented_children'in e.get('reasons',[]) for e in result['excluded']))

    def test_incomplete_and_mixed_units_are_excluded(self):
        for old in ['Art. 5. Texto interrompido','Art. 5. Texto. (Redação dada sem fechar',
                    'Art. 5. Texto. § 1º Outro texto.']:
            self.assertEqual(self.extract('<p><strike>'+old+'</strike></p>'+newer())['records'],[])

    def test_duplicate_body_different_notes_is_not_textual_change(self):
        result=self.extract('<p><strike>Art. 5. Mesmo texto.</strike></p>'+newer('Art. 5. Mesmo texto.'))
        self.assertEqual(result['records'],[])
        self.assertIn('same_normative_body_different_documentary_entries',result['excluded'][0]['reasons'])

    def test_veto_and_css_rules_are_not_silently_accepted(self):
        for old in ['Art. 5. (VETADO).','Art. 5. Texto. (Revogado pela Lei nº 2)']:
            self.assertEqual(self.extract('<p><s>'+old+'</s></p>'+newer())['records'],[])
        result=self.extract('<style>.old{text-decoration:line-through}</style><p><s>Art. 5. Texto anterior.</s></p>'+newer())
        self.assertEqual(result['records'],[])

    def test_promulgation_in_norm_is_not_an_editorial_event(self):
        rows=self.extract('<p><s>Art. 5. Um ano após sua promulgação.</s></p>'+newer())['records']
        self.assertEqual(len(rows),2)
        self.assertEqual(self.extract('<p><s>Art. 5. Texto. (Promulgado posteriormente)</s></p>'+newer())['records'],[])

    def test_effect_note_and_explicit_bare_adct_reference(self):
        result=self.extract('<p>Art. 5. Regra.</p><p><s>§ 1º Antes.</s></p>'+newer('§ 1º Depois. (Produção de efeito) Vide art. 96 - ADCT'))
        self.assertEqual([r['text'] for r in result['records']],['§ 1º Antes.','§ 1º Depois.'])
        self.assertIn('Vide art. 96 - ADCT',result['records'][1]['notes'])
        self.assertIn('(Produção de efeito)',result['records'][1]['notes'])
        self.assertEqual(split_notes('Regra. (Vide art. 96 - ADCT)')[1],['(Vide art. 96 - ADCT)'])

    def test_dashless_item_requires_preceding_struck_same_item(self):
        body='<p>Art. 5. Regra:</p><p><s>IV - Antes;</s></p>'+newer('IV depois;')
        rows=self.extract(body)['records']
        self.assertEqual(len(rows),2)
        self.assertEqual(rows[1]['unitLabel'],'caput · inciso IV')
        self.assertEqual(rows[1]['text'],'IV depois;')
        self.assertEqual(self.extract(body.replace('IV depois','V depois'))['records'],[])

    def test_existing_rows_are_not_modified_or_duplicated(self):
        body='<p><s>Art. 5. Texto anterior.</s></p>'+newer()
        baseline=self.extract(body)['records']
        before=json.dumps(baseline,ensure_ascii=False)
        result=self.extract(body,baseline)
        self.assertEqual(result['records'],[])
        self.assertEqual(len(result['duplicateEvidence']),2)
        self.assertEqual(json.dumps(baseline,ensure_ascii=False),before)
        self.assertTrue(all(r['natureMatches'] for r in result['validation']))
        wrong=[dict(baseline[0],articleId='6')]
        self.assertEqual(self.extract(body,wrong)['validation'][0]['result'],'text_only_wrong_or_unresolved_unit')

    def test_encoding_and_no_unicode_rewrite(self):
        text='a\u0300'
        body='<p><s>Art. 5. Texto '+text+'.</s></p>'+newer()
        raw=document(body).decode().replace('charset="utf-8"','charset="UTF-16LE"').encode('utf-16')
        self.assertEqual(decode(raw)[1],'utf-16')
        result=prepare_document('civil','example.html',raw)
        self.assertIn(text,result['records'][0]['text'])

    def test_evidence_range_and_source_hash(self):
        raw=document('<p><s>Art. 5. Texto antigo.</s></p>'+newer())
        result=prepare_document('civil','example.html',raw)
        source=decode(raw)[0]
        for r in result['records']:
            a,z=r['evidence']['charRange']
            self.assertEqual(source[a:z],r['evidence']['rawHtml'])
            self.assertEqual(r['source']['sha256'],hashlib.sha256(raw).hexdigest())
            self.assertEqual(split_notes(r['evidence']['rawUnitText'])[0],r['text'])

    def test_unknown_reader_article_is_not_exported(self):
        result=self.extract('<p><s>Art. 5. Antigo.</s></p>'+newer(),reader={'6'})
        self.assertEqual(result['records'],[])

    def test_truncated_last_unit_and_adjacent_note_are_not_completed(self):
        result=self.extract('<p><s>Art. 5. Texto anterior.</s></p><p>Art. 5. Texto sem final</p>'
                            '<p>(Redação dada pela Lei nº 1, de 2000)</p>')
        self.assertEqual(result['records'],[])

    def test_quoted_normative_units_do_not_become_own_law_versions(self):
        result=self.extract('<blockquote><p><s>Art. 5. Texto anterior.</s></p>'+newer()+'</blockquote>')
        self.assertEqual(result['records'],[])
        self.assertTrue(any('quoted_or_indented_container_requires_review' in e['reasons'] for e in result['excluded']))

    def test_adct_namespace_does_not_reuse_constitution_article_one(self):
        raw=document('<p>Art. 250. Regra.</p><p>ATO DAS DISPOSIÇÕES CONSTITUCIONAIS TRANSITÓRIAS</p>'
                     '<p><s>Art. 1º Antes.</s></p>'+newer('Art. 1º Depois.'))
        rows=prepare_document('cf','example.html',raw,reader_ids={'250','adct-1'})['records']
        self.assertEqual([r['articleId'] for r in rows],['adct-1','adct-1'])

    def test_generated_corpus_reference_validation_and_integrity(self):
        folder=ROOT/'experiments/html-history/results'
        if not (folder/'records.json').exists():
            self.skipTest('Execute the local extraction before checking its corpus.')
        validation=json.loads((folder/'validation.json').read_text(encoding='utf-8'))
        self.assertEqual(len(validation),96)
        self.assertTrue(all(v['result']=='exact_text_and_unit' and v['natureMatches'] for v in validation))
        records=json.loads((folder/'records.json').read_text(encoding='utf-8'))
        existing=json.loads((ROOT/'experiments/html-history/existing-records.json').read_text(encoding='utf-8'))
        identities=[(*row_key(r),r['text']) for r in existing+records]
        self.assertEqual(len(identities),len(set(identities)))
        self.assertEqual(len({r['id'] for r in existing+records}),len(existing)+len(records))
        for record in records:
            self.assertEqual(record['review'],{'status':'pending'})
            self.assertEqual(split_notes(record['evidence']['rawUnitText'])[0],record['text'])
            self.assertIn(record['part'],{'caput','paragraph','item','letter'})
            source=source_path(record['source']['document'],record['source']['sha256'])
            if source.exists():
                decoded,_=decode(source.read_bytes())
                a,b=record['evidence']['charRange']
                self.assertEqual(decoded[a:b],record['evidence']['rawHtml'])
        inventory=json.loads((folder/'inventory.json').read_text(encoding='utf-8'))
        self.assertEqual(len(inventory),13)
        self.assertTrue(all(i['records']==0 for i in inventory if i['codeId']in {'civil','cpc','cdc','ctn','clt'}))
        self.assertTrue(next(i for i in inventory if i['codeId']=='cf')['warnings'])
        manifest=json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
        self.assertFalse(manifest['publicationAllowed'])
        for name,expected in manifest['files'].items():
            self.assertEqual(hashlib.sha256((folder/name).read_bytes()).hexdigest(),expected)
        expected=manifest['extractorSha256']
        editions=[ROOT/'scripts/extract_previous_html.py',ROOT/'experiments/html-history/script-archives'/expected/'extract_previous_html.py']
        self.assertTrue(any(p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==expected for p in editions),'The exact parser edition used for this historical snapshot must remain preserved')


if __name__=='__main__':
    unittest.main()
