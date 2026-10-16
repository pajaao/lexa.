import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from check_official_sources import fingerprint
from import_official import ROOT, convert, prepare


class OfficialImportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.specs=json.loads((ROOT/'monitor/sources.json').read_text())
        cls.snapshots={s['id']:json.loads((ROOT/'monitor/official'/(s['id']+'.json')).read_text()) for s in cls.specs}
        cls.converted={s['id']:convert(s,cls.snapshots[s['id']]) for s in cls.specs}

    def article(self,code,id):
        return next(a for a in self.converted[code]['articles'] if a['id']==id)

    def text(self,article):
        return '\n'.join(''.join(r['text'] for r in p['runs']) for p in article['paragraphs'])

    def test_six_actual_accepted_snapshots_and_source_timezone(self):
        self.assertEqual(len(self.converted),6)
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
            shutil.copytree(ROOT/'monitor/official',root/'monitor/official')
            shutil.copyfile(ROOT/'monitor/sources.json',root/'monitor/sources.json')
            shutil.copyfile(ROOT/'content.js',root/'content.js')
            (root/'official-content.js').write_text('export const officialImported = {};\n')
            archive=(root/'content.js').read_bytes()
            prepare(root)
            first=(root/'official-content.js').read_bytes()
            manifest=(root/'sources/official-manifest.json').read_bytes()
            _,report=prepare(root)
            self.assertEqual(first,(root/'official-content.js').read_bytes())
            self.assertEqual(manifest,(root/'sources/official-manifest.json').read_bytes())
            self.assertEqual(archive,(root/'content.js').read_bytes())
            self.assertTrue(all(not d['added'] and not d['removed'] and not d['changed'] for d in report.values()))


if __name__=='__main__':
    unittest.main()
