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

    def test_partial_veto_revocation_and_truncation_stay_out(self):
        for body in ['<p>Art. 1. Texto <s>parcial</s>.</p>', '<p><s>Art. 1. VETADO.</s></p>',
                     '<p><s>Art. 1. (Revogado pela Lei nº 1).</s></p>', '<p><s>Art. 1. Sem final</s></p>']:
            src=extract('civil','test.html',document(body))
            self.assertFalse(src['entries'][0]['extracted'])
            self.assertEqual(prepare(dict(sources=[src]),reader())['records'],[])

    def test_uncertain_css_and_explicit_mixed_units_are_not_presented(self):
        for body in ['<style>.old {text-decoration:line-through}.old {text-decoration:none}</style><p><s>Art. 1. Antes.</s></p>',
                     '<style>div .old {text-decoration:line-through}</style><p><s>Art. 1. Antes.</s></p>',
                     '<p><s>Art. 1. Antes.<br>§ 1º Outro trecho.</s></p>']:
            src=extract('civil','test.html',document(body))
            self.assertFalse(src['entries'][0]['extracted'])
            self.assertFalse(prepare(dict(sources=[src]),reader())['records'])

    def test_same_number_alone_does_not_map_but_same_group_current_caput_does(self):
        src=extract('civil','test.html',document('<p><s>Art. 1. Antes.</s></p>'))
        self.assertFalse(prepare(dict(sources=[src]),reader())['records'])
        src=extract('civil','test.html',document('<p><s>Art. 1. Antes.</s></p><p>Art. 1. Atual.</p>'))
        mapped=prepare(dict(sources=[src]),reader())
        self.assertEqual(mapped['records'][0]['text'],'Art. 1. Antes.')
        self.assertTrue(mapped['decisions'][0]['currentCaputWitnesses'])
        self.assertEqual(mapped['records'][0]['review'],{'status':'pending'})

    def test_penal_original_part_never_maps_even_with_identical_reader_text(self):
        raw=document('<p><s>Art. 1. Antiga.</s></p><p><s>Art. 4. Território.</s></p>'
                     '<p><s>Art. 5. Estrangeiro.</s></p><p>Art. 120. Fim.</p>'
                     '<h2>PARTE GERAL</h2><p>Art. 1. Atual.</p>')
        src=extract('penal','test.html',raw)
        data=reader('penal','Art. 1. Antiga.')
        for n,t in [('4','Território'),('5','Estrangeiro')]:
            data['penal']['articles'][n]=dict(paragraphs=[dict(runs=[dict(text=f'Art. {n}. {t}.')])])
        result=prepare(dict(sources=[src]),data)
        self.assertFalse(result['records'])
        self.assertTrue(all('incompatible_or_quoted_document_context' in d['reasons'] for d in result['decisions']))

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

    def test_all_thirteen_sources_and_fixture_are_consistent(self):
        run=ROOT/'experiments/previous-wordings-simple/20261021-complete'
        data=read(run/'extraction.json'); result=prepare(data,read(run/'reader.json'))
        self.assertEqual(len(data['sources']),13)
        self.assertEqual(result,read(run/'presentation.json'))
        self.assertEqual(read(ROOT/'tests/fixtures/previous-wordings-simple.json')['records'],result['records'])
        self.assertEqual(len({r['id'] for r in result['records']}),len(result['records']))
        self.assertTrue(all(r['review']=={'status':'pending'} for r in result['records']))
        self.assertTrue(all(d['associated']==(not d['reasons']) for d in result['decisions']))


if __name__=='__main__': unittest.main()
