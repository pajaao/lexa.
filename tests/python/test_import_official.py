import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from check_official_sources import fingerprint
from import_official import ROOT, convert, prepare, history_event, load_js


class OfficialImportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.specs=json.loads((ROOT/'monitor/sources.json').read_text(encoding='utf-8'))
        cls.snapshots={s['id']:json.loads((ROOT/'monitor/official'/(s['id']+'.json')).read_text(encoding='utf-8')) for s in cls.specs}
        cls.converted={s['id']:convert(s,cls.snapshots[s['id']]) for s in cls.specs}

    def article(self,code,id):
        return next(a for a in self.converted[code]['articles'] if a['id']==id)

    def text(self,article):
        return '\n'.join(''.join(r['text'] for r in p['runs']) for p in article['paragraphs'])

    def test_configured_actual_snapshots_and_source_timezone(self):
        self.assertEqual(len(self.converted),13)
        for id,doc in self.converted.items():
            self.assertEqual(doc['source']['sha256'],self.snapshots[id]['semantic_sha256'])
            self.assertEqual(len({a['id'] for a in doc['articles']}),len(doc['articles']))
            self.assertEqual(doc['source']['kind'],'official_html')
        example=copy.deepcopy(self.snapshots['civil']);example['captured_at']='2026-10-16T00:33:21+00:00'
        spec=next(s for s in self.specs if s['id']=='civil')
        self.assertIn('15/10/2026',convert(spec,example)['source']['edition'])

    def test_long_articles_preserve_provisions_and_historical_caput(self):
        self.assertIn('LXXIX',self.text(self.article('cf','5')))
        self.assertIn('§ 4º O Brasil se submete',self.text(self.article('cf','5')))
        self.assertIn('VI - as provas',self.text(self.article('cpc','319')))
        self.assertIn('c) com seu comportamento anterior',self.text(self.article('penal','13')))
        twelve=self.article('cpc','12')
        self.assertTrue(any(r['deleted'] and 'deverão obedecer' in r['text'] for p in twelve['paragraphs'] for r in p['runs']))
        self.assertTrue(any(not r['deleted'] and 'atenderão, preferencialmente' in r['text'] for p in twelve['paragraphs'] for r in p['runs']))
        self.assertEqual(self.article('ctn','52')['rangeEnd'],58)
        self.assertEqual(self.article('civil','1620')['rangeEnd'],1629)

    def test_penal_penalty_remains_in_article_213_not_rubric_of_214(self):
        blocks = self.snapshots['penal']['document']['blocks']
        article = self.article('penal', '213')
        following = self.article('penal', '214')
        self.assertEqual(article['title'], 'Estupro')
        self.assertEqual([p['sourceBlock'] for p in article['paragraphs']], list(range(1375, 1381)))
        self.assertEqual([p['runs'] for p in article['paragraphs']], blocks[1374:1380])
        self.assertNotIn('title', following)
        self.assertEqual([p['sourceBlock'] for p in following['paragraphs']], [1381])
        self.assertEqual(following['paragraphs'][0]['runs'], blocks[1380])

    def test_penal_penalties_with_notes_are_not_rubrics(self):
        # Preserve the source runs, including deletion flags and amendment notes.
        spec = next(s for s in self.specs if s['id'] == 'penal')
        for prefix in ('Pena - ', 'Pena – ', 'Pena — ', 'Pena: ', 'Penas - '):
            with self.subTest(prefix=prefix):
                snapshot = copy.deepcopy(self.snapshots['penal'])
                runs = snapshot['document']['blocks'][1379]
                runs[0]['text'] = prefix + 'reclusão (Nota da fonte)'
                runs[0]['deleted'] = True
                snapshot['semantic_sha256'] = fingerprint(snapshot['document'])
                converted = convert(spec, snapshot)
                article = next(a for a in converted['articles'] if a['id'] == '213')
                following = next(a for a in converted['articles'] if a['id'] == '214')
                self.assertEqual(article['paragraphs'][-1]['runs'], runs)
                self.assertEqual(article['paragraphs'][-1]['sourceBlock'], 1380)
                self.assertNotIn('title', following)

    def test_penal_nearby_rubrics_and_penalty_heading_are_preserved(self):
        for id, title in [('43', 'Penas restritivas de direitos'),
                          ('211', 'Destruição, subtração ou ocultação de cadáver'),
                          ('212', 'Vilipêndio a cadáver'), ('213', 'Estupro')]:
            with self.subTest(article=id):
                self.assertEqual(self.article('penal', id)['title'], title)

    def test_penal_reprocessing_preserves_text_and_other_official_collections(self):
        previous = load_js(ROOT/'data/official/legislation.js', 'officialImported')
        def content(collection):
            from collections import Counter
            return Counter([a['title'] for a in collection['articles'] if a.get('title')] +
                           [''.join(r['text'] for r in p['runs']).strip()
                            for a in collection['articles'] for p in a['paragraphs']])
        self.assertEqual(content(previous['penal']), content(self.converted['penal']))
        for id, candidate in self.converted.items():
            if id != 'penal':
                with self.subTest(collection=id):
                    self.assertEqual(candidate, previous[id])

    def test_penal_four_penalties_keep_source_blocks_and_runs(self):
        blocks = self.snapshots['penal']['document']['blocks']
        for owner, following, penalty_block in [('213', '214', 1380),
                                               ('215-A', '216', 1388),
                                               ('309', '310', 1952),
                                               ('359-M', '359-M-A', 2358)]:
            with self.subTest(article=owner):
                article = self.article('penal', owner)
                next_article = self.article('penal', following)
                penalty = article['paragraphs'][-1]
                self.assertEqual(penalty['sourceBlock'], penalty_block)
                self.assertEqual(penalty['runs'], blocks[penalty_block-1])
                self.assertNotIn('title', next_article)
                self.assertEqual(next_article['paragraphs'][0]['sourceBlock'], penalty_block+1)
                self.assertEqual(next_article['paragraphs'][0]['runs'], blocks[penalty_block])

    def test_constitution_namespaces_preamble_and_end_boundaries(self):
        self.assertIn('A República Federativa do Brasil',self.text(self.article('cf','1')))
        self.assertIn('O Presidente da República',self.text(self.article('cf','adct-1')))
        self.assertIn('Nós, representantes',self.converted['cf']['introductions'][0]['text'])
        self.assertLess(len(self.converted['cf']['introductions'][0]['text']),1500)
        self.assertIn('disposições correspondentes deste Código.',self.text(self.article('civil','2046')))
        self.assertNotIn('CAPÍTULO XIII',self.text(self.article('civil','2046')))
        self.assertNotIn('DILMA ROUSSEFF',self.text(self.article('cpc','1072')))

    def test_snapshot_corruption_css_and_missing_content_fail_closed(self):
        spec=self.specs[0];snapshot=self.snapshots[spec['id']]
        broken=copy.deepcopy(snapshot);broken['semantic_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'Hash'):
            convert(spec,broken)
        broken=copy.deepcopy(snapshot);broken['document']['deletion_styles']=['.old{text-decoration:line-through}'];broken['semantic_sha256']=fingerprint(broken['document'])
        with self.assertRaisesRegex(ValueError,'CSS'):
            convert(spec,broken)
        broken=copy.deepcopy(snapshot);broken['document']['blocks']=broken['document']['blocks'][:40];broken['semantic_sha256']=fingerprint(broken['document'])
        with self.assertRaises(ValueError):
            convert(spec,broken)

    def test_preparation_is_repeatable_and_leaves_pdfs_and_archive_untouched(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for folder in ['data/archive','data/official','data/history']:(root/folder).mkdir(parents=True,exist_ok=True)
            shutil.copytree(ROOT/'monitor/official',root/'monitor/official')
            shutil.copyfile(ROOT/'monitor/sources.json',root/'monitor/sources.json')
            shutil.copyfile(ROOT/'data/archive/legislation.js',root/'data/archive/legislation.js')
            (root/'data/official/legislation.js').write_text('export const officialImported = {};\n', encoding='utf-8')
            archive=(root/'data/archive/legislation.js').read_bytes()
            prepare(root)
            first=(root/'data/official/legislation.js').read_bytes()
            manifest=(root/'sources/official-manifest.json').read_bytes()
            history=(root/'data/history/legislation.js').read_bytes()
            recorded=load_js(root/'data/history/legislation.js','updateHistory')
            self.assertEqual(len(recorded),13)
            self.assertTrue(all(e['kind']=='baseline' and not e['changes'] for e in recorded))
            _,report=prepare(root)
            self.assertEqual(first,(root/'data/official/legislation.js').read_bytes())
            self.assertEqual(manifest,(root/'sources/official-manifest.json').read_bytes())
            self.assertEqual(history,(root/'data/history/legislation.js').read_bytes())
            self.assertEqual(archive,(root/'data/archive/legislation.js').read_bytes())
            self.assertTrue(all(not d['added'] and not d['removed'] and not d['changed'] for d in report.values()))
            # Introducing the history feature after an HTML edition was already
            # merged establishes its baseline without inventing a text change.
            (root/'data/history/legislation.js').unlink()
            prepare(root)
            self.assertEqual(history,(root/'data/history/legislation.js').read_bytes())

    def test_history_compares_real_versions_preserves_full_text_and_deduplicates(self):
        def doc(sha,text):
            return {'source':{'sha256':sha,'converterVersion':1,'capturedAt':'2026-10-16T00:33:21+00:00','url':'https://www.planalto.gov.br/'},
                    'articles':[{'id':'1','number':'1','scope':'main','paragraphs':[{'runs':[{'text':text,'deleted':False}]}]}]}
        old,new=doc('old','Art. 1º Prazo de dez dias.'),doc('new','Art. 1º Prazo de quinze dias.')
        baseline=history_event('civil',None,old,[])
        self.assertEqual(baseline['kind'],'baseline');self.assertEqual(baseline['changes'],[])
        event=history_event('civil',old,new,[baseline])
        self.assertEqual(event['kind'],'text');self.assertEqual(event['changes'][0]['type'],'changed')
        revision=event['changes'][0]
        self.assertIn('dez',revision['before']['paragraphs'][0]['runs'][0]['text'])
        self.assertIn('quinze',revision['after']['paragraphs'][0]['runs'][0]['text'])
        self.assertIsNone(history_event('civil',old,new,[baseline,event]))
        self.assertIsNone(history_event('civil',new,new,[baseline,event]))
        formatted=doc('format','Art. 1º  Prazo de\nquinze dias.')
        event=history_event('civil',new,formatted,[baseline])
        self.assertEqual(event['kind'],'source');self.assertEqual(event['changes'],[])
        reprocessed=doc('old','Art. 1º Correção de extração.');reprocessed['source']['converterVersion']=2
        self.assertEqual(history_event('civil',old,reprocessed,[baseline])['kind'],'processing')

    def test_history_distinguishes_added_and_missing_articles(self):
        old=copy.deepcopy(self.converted['civil']);new=copy.deepcopy(old)
        old['source']['sha256']='old';new['source']['sha256']='new'
        del new['articles'][0]
        extra=copy.deepcopy(new['articles'][0]);extra['id']='2047';extra['number']='2047';new['articles'].append(extra)
        baseline=history_event('civil',None,old,[])
        event=history_event('civil',old,new,[baseline])
        statuses={c['articleId']:c['type'] for c in event['changes']}
        self.assertEqual(statuses['1'],'removed');self.assertEqual(statuses['2047'],'added')


if __name__=='__main__':
    unittest.main()
