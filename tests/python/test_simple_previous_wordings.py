import hashlib
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from extract_struck_html import extract, read, ROOT
from present_struck_html import prepare


def document(body, encoding='utf-8'):
    return ('<!-- saved from url=(0050)https://www.planalto.gov.br/test.htm -->'
            f'<html><head><meta charset="{encoding}"></head><body>'+body+'</body></html>').encode(encoding)


def reader(code='civil', text='Art. 1. Atual.'):
    return {code:dict(articles={'1':dict(paragraphs=[dict(runs=[dict(text=text,deleted=False)])])})}


class SimplePrevious(unittest.TestCase):
    def test_codifications_and_verbatim_evidence(self):
        for enc in ['utf-8','cp1252','utf-16']:
            raw=document('<p><s>Art. 1. Ação anterior.</s></p>',enc)
            source=extract('civil','test.html',raw); entry=source['entries'][0]
            self.assertEqual(entry['text'],'Art. 1. Ação anterior.')
            self.assertEqual(entry['source']['sha256'],hashlib.sha256(raw).hexdigest())
            a,b=entry['evidence']['charRange']
            self.assertEqual(raw.decode(enc)[a:b],entry['evidence']['rawHtml'])

    def test_supported_strike_tags_inline_css_and_embedded_selectors(self):
        for start,end in [('<s>','</s>'),('<strike>','</strike>'),('<del>','</del>'),
                          ('<span style="text-decoration-line:line-through">','</span>'),
                          ('<span class="old">','</span>'),('<span id="old">','</span>')]:
            raw=document('<style>.old,span#old {text-decoration:line-through}</style><p>'+start+'Art. 1. Antiga.'+end+'</p>')
            self.assertTrue(extract('civil','test.html',raw)['entries'][0]['extracted'])

    def test_fragments_and_punctuation_do_not_require_complete_versions(self):
        src=extract('civil','test.html',document('<p>Art. 1. Texto <s>parcial</s>.</p>'))
        result=prepare(dict(sources=[src]),reader())
        self.assertEqual(result['records'][0]['text'],'parcial')
        for body in ['<p><s>Art. 1. VETADO.</s></p>','<p><s>Art. 1. (Revogado pela Lei nº 1).</s></p>']:
            self.assertFalse(prepare(dict(sources=[extract('civil','test.html',document(body))]),reader())['records'])
        src=extract('civil','test.html',document('<p><s>Art. 1. Trecho sem ponto final</s></p>'))
        self.assertEqual(prepare(dict(sources=[src]),reader())['records'][0]['text'],'Art. 1. Trecho sem ponto final')

    def test_uncertain_css_stays_out_and_joint_units_are_labeled(self):
        for body in ['<style>.old {text-decoration:line-through}.old {text-decoration:none}</style><p><s>Art. 1. Antes.</s></p>',
                     '<style>div .old {text-decoration:line-through}</style><p><s>Art. 1. Antes.</s></p>']:
            src=extract('civil','test.html',document(body))
            self.assertFalse(src['entries'][0]['extracted'])
        src=extract('civil','test.html',document('<p><s>Art. 1. Antes.<br>§ 1º Outro trecho.</s></p>'))
        record=prepare(dict(sources=[src]),reader())['records'][0]
        self.assertEqual(record['part'],'article')
        self.assertIn('múltiplas subdivisões',record['unitLabel'])

    def test_documentary_article_does_not_require_current_caput(self):
        src=extract('civil','test.html',document('<p><s>Art. 1. Antes.</s></p>'))
        mapped=prepare(dict(sources=[src]),reader())
        self.assertEqual(mapped['records'][0]['text'],'Art. 1. Antes.')
        self.assertTrue(mapped['decisions'][0]['documentaryAssociated'])
        self.assertEqual(mapped['decisions'][0]['articleBlock'],0)
        self.assertEqual(mapped['records'][0]['review'],{'status':'pending'})

    def test_penal_original_part_preserves_source_number_without_current_equivalence(self):
        raw=document('<p><s>Art. 1. Antiga.</s></p><p><s>Art. 4. Território.</s></p>'
                     '<p><s>Art. 5. Estrangeiro.</s></p><p>Art. 120. Fim.</p>'
                     '<h2>PARTE GERAL</h2><p>Art. 1. Atual.</p>')
        src=extract('penal','test.html',raw)
        data=reader('penal')
        for n in ['4','5']:data['penal']['articles'][n]=dict(paragraphs=[])
        result=prepare(dict(sources=[src]),data)
        self.assertEqual([r['articleId'] for r in result['records']],['1','4','5'])
        self.assertTrue(all('não estabelecida' in r['documentaryContext'] for r in result['records']))

    def test_quote_never_supplies_article_or_current_caput_witness(self):
        raw=document('<p>Art. 1. Atual.</p><blockquote><p><s>Art. 1. De outra lei.</s></p></blockquote>'
                     '<p><s>§ 1º Sem artigo próprio.</s></p>')
        result=prepare(dict(sources=[extract('civil','test.html',raw)]),reader())
        self.assertFalse(result['records'])

    def test_notes_links_stay_with_the_occurrence_and_duplicates_stay_evidence(self):
        raw=document('<p><s>Art. 1. Antes.</s> <a href="https://www.planalto.gov.br/a.htm">(Redação dada pela Lei nº 1)</a></p>'
                     '<p><s>Art. 1. Antes.</s> (Redação dada pela Lei nº 2)</p><p>Art. 1. Atual.</p>')
        src=extract('civil','test.html',raw); result=prepare(dict(sources=[src]),reader())
        self.assertEqual(len(src['entries']),2)
        self.assertEqual(len(result['records']),1)
        row=result['records'][0]
        self.assertEqual(row['notes'],['(Redação dada pela Lei nº 1)'])
        self.assertEqual(row['reference'],row['notes'][0])
        self.assertEqual(row['evidence']['editorialNotes'][0]['links'],['https://www.planalto.gov.br/a.htm'])
        self.assertIn('duplicate_documentary_text',result['decisions'][1]['reasons'])

    def test_adct_table_of_contents_does_not_change_constitution_scope(self):
        raw=document('<p>ATO DAS DISPOSIÇÕES CONSTITUCIONAIS TRANSITÓRIAS</p>'
                     '<p><s>Art. 1. Constituição antiga.</s></p><p>Art. 250. Fim.</p>'
                     '<p>ATO DAS DISPOSIÇÕES CONSTITUCIONAIS TRANSITÓRIAS</p>'
                     '<p><s>Art. 1. ADCT antigo.</s></p>')
        rows=extract('cf','test.html',raw)['entries']
        self.assertEqual([r['context']['articleId'] for r in rows],['1','adct-1'])

    def test_two_struck_letter_bodies_with_unstruck_labels_are_preserved(self):
        raw=document('<p>Art. 1. Atual.</p><p>I - Lista.</p>'
                     '<p>a) <s>Primeira antiga;</s><br>\nb) <s>Segunda antiga;</s></p>')
        src=extract('civil','test.html',raw)
        row=src['entries'][0]
        self.assertTrue(row['extracted'], row['reasons'])
        self.assertEqual(row['text'],'a) Primeira antiga; b) Segunda antiga;')
        self.assertIn('Alíneas a), b)',row['unitLabel'])
        self.assertEqual(len(prepare(dict(sources=[src]),reader())['records']),1)

    def test_internal_references_letters_and_malformed_notes_preserve_article(self):
        raw=document('<p><s>Art. 1. Conforme art. 2 e art. 3.</s></p>'
                     '<p><s>a) Prioridade;</s></p>'
                     '<p><s>§ 1º Texto recuperável.</s> (Revogado pela Lei nº 1</p>')
        result=prepare(dict(sources=[extract('civil','test.html',raw)]),reader())
        self.assertEqual(len(result['records']),3)
        self.assertTrue(all(r['articleId']=='1' for r in result['records']))
        self.assertEqual(result['records'][2]['text'],'§ 1º Texto recuperável.')
        self.assertIn('incomplete_editorial_note_preserved',result['records'][2]['documentaryWarnings'])

    def test_native_blockquote_and_revogado_in_normative_sentence(self):
        raw=document('<blockquote><p><a name="art1"></a>Art. 1. Fonte.</p>'
                     '<p><s>I - Antiga.</s></p></blockquote>'
                     '<p><s>Art. 2. Revogado o livramento, não pode ser novamente concedido.</s></p>')
        data=reader();data['civil']['articles']['2']=dict(paragraphs=[])
        records=prepare(dict(sources=[extract('civil','test.html',raw)]),data)['records']
        self.assertEqual([r['articleId'] for r in records],['1','2'])
        self.assertIn('Revogado o livramento',records[1]['text'])

    def test_caption_uses_adjacent_article_and_structures_never_use_previous_article(self):
        raw=document('<p>Art. 1. Atual.</p><p><b><s>Rubrica específica</s></b></p><p>Art. 2. Seguinte.</p>'
                     '<h2><s>CAPÍTULO II</s></h2><p><s>DA LEGISLAÇÃO</s></p>')
        data=reader();data['civil']['articles']['2']=dict(paragraphs=[])
        result=prepare(dict(sources=[extract('civil','test.html',raw)]),data)
        self.assertEqual(len(result['records']),1)
        self.assertEqual(result['records'][0]['articleId'],'2')
        self.assertEqual(result['records'][0]['part'],'rubric')

    def test_separate_fragments_do_not_join_current_words_and_ordinals_are_not_wordings(self):
        raw=document('<p>Art. 1. <s>Antes</s> texto atual <s>outro</s>.</p>'
                     '<p>§ 1<s>º</s> Texto atual.</p>')
        result=prepare(dict(sources=[extract('civil','test.html',raw)]),reader())
        self.assertEqual([r['text'] for r in result['records']],['Antes','outro'])
        self.assertTrue(all('fragmentTextRange' in r['evidence'] for r in result['records']))

    def test_spaced_article_marker_uses_own_anchor_not_previous_article(self):
        raw=document('<p>Art. 1. Atual.</p><p><b><s>Rubrica antiga</s></b></p>'
                     '<p><a name="art2"></a>A <s>rt. 2. Antiga.</s></p>')
        data=reader();data['civil']['articles']['2']=dict(paragraphs=[])
        records=prepare(dict(sources=[extract('civil','test.html',raw)]),data)['records']
        self.assertTrue(all(r['articleId']=='2' for r in records))
        self.assertEqual(records[1]['text'],'A rt. 2. Antiga.')

    def test_editorial_vigencia_and_bold_caption_cluster_are_not_normative_fragments(self):
        raw=document('<p>Art. 1. Atual.</p><p>§ 1º Texto atual. <s>(Vide Decreto nº 1) Vigência</s></p>'
                     '<p><b><s>Nome antigo</s></b></p><p><span style="font-weight:700">Nome novo.</span></p><p>Art. 2. Texto.</p>')
        data=reader();data['civil']['articles']['2']=dict(paragraphs=[])
        records=prepare(dict(sources=[extract('civil','test.html',raw)]),data)['records']
        self.assertEqual(len(records),1)
        self.assertEqual(records[0]['text'],'Nome antigo')
        self.assertEqual(records[0]['articleId'],'2')

    def test_unbold_caption_after_section_title_binds_to_following_article(self):
        raw=document('<h2>SECÇÃO I</h2><p>DA LEGISLAÇÃO</p>'
                     '<p style="text-align:left"><s>Regras comuns</s></p><p>Art. 1. Texto.</p>')
        result=prepare(dict(sources=[extract('civil','test.html',raw)]),reader())
        self.assertEqual(len(result['records']),1)
        self.assertEqual(result['records'][0]['articleId'],'1')
        self.assertEqual(result['records'][0]['part'],'rubric')

    def test_all_thirteen_sources_and_fixture_are_consistent(self):
        run=ROOT/'experiments/previous-wordings-simple/20261021-associations-corrected'
        data=read(run/'extraction.json'); result=prepare(data,read(run/'reader.json'))
        self.assertEqual(len(data['sources']),13)
        self.assertEqual(result,read(run/'presentation.json'))
        self.assertEqual(read(ROOT/'tests/fixtures/previous-wordings-simple.json')['records'],result['records'])
        self.assertEqual(len({r['id'] for r in result['records']}),len(result['records']))
        self.assertTrue(all(r['review']=={'status':'pending'} for r in result['records']))
        self.assertTrue(all(d['associated']==(not d['reasons']) for d in result['decisions']))
        entries={e['id']:e for source in data['sources'] for e in source['entries']}
        for record in result['records']:
            entry=entries[record['id'].split('-fragment-')[0]]
            if 'fragmentTextRange' in record['evidence']:
                a,z=record['evidence']['fragmentTextRange']
                self.assertEqual(record['text'],' '.join(entry['evidence']['rawText'][a:z].split()))
            else:self.assertEqual(record['text'],entry['text'])
            self.assertEqual(record['articleId'],entry['context']['articleId'])
            self.assertIsNotNone(entry['context']['articleBlock'])



if __name__=='__main__': unittest.main()
