import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts'))
from saved_html_source import source_path
from refresh_previous_html_sources import process, reprocess, INPUTS
from prepare_previous_only import ensure_source_baseline


TEMP=Path(__file__).resolve().parents[2]/'test-results'
TEMP.mkdir(exist_ok=True)


class SourceRefresh(unittest.TestCase):
    def test_exact_source_edition_uses_archive_and_rejects_tampering(self):
        with tempfile.TemporaryDirectory(dir=TEMP) as directory:
            root=Path(directory)
            (root/'HTML').mkdir()
            (root/'HTML/test.html').write_bytes(b'new edition')
            digest=hashlib.sha256(b'old edition').hexdigest()
            archive=root/'experiments/html-history/source-archives'/digest/'test.html'
            archive.parent.mkdir(parents=True)
            archive.write_bytes(b'old edition')
            self.assertEqual(source_path('test.html',digest,root),archive)
            archive.write_bytes(b'changed')
            with self.assertRaises(ValueError):
                source_path('test.html',digest,root)
            with self.assertRaises(ValueError):
                source_path('../test.html',digest,root)

    def test_old_batch_command_refuses_changed_source_before_writing(self):
        with tempfile.TemporaryDirectory(dir=TEMP) as directory:
            root=Path(directory)
            (root/'HTML').mkdir()
            (root/'HTML/test.html').write_bytes(b'old')
            manifest=root/'experiments/html-history/previous-only/manifest.json'
            manifest.parent.mkdir(parents=True)
            manifest.write_text(json.dumps({'sources':{'test.html':hashlib.sha256(b'old').hexdigest()}}),encoding='utf-8')
            ensure_source_baseline(root)
            (root/'HTML/test.html').write_bytes(b'new')
            with self.assertRaises(ValueError):
                ensure_source_baseline(root)

    def test_only_three_sources_are_processed_and_existing_text_is_not_added_twice(self):
        with tempfile.TemporaryDirectory(dir=TEMP) as directory:
            folder=Path(directory)
            reader={'cf':['250','adct-138'],'cpp':['811'],'cpc':['1072']}
            bodies={'cf':'<p>Art. 250. Regra.</p><p>ATO DAS DISPOSIÇÕES CONSTITUCIONAIS TRANSITÓRIAS</p><p><s>Art. 138. Anterior.</s></p>',
                'cpp':'<p><s>Art. 811. Anterior.</s></p>',
                'cpc':'<p><s>Art. 1072. Anterior.</s></p>'}
            for code,name in INPUTS.items():
                (folder/name).write_text('<!-- saved from url=(0050)https://www.planalto.gov.br/test.htm -->'
                    '<html><meta charset="utf-8">'+bodies[code]+'</html>',encoding='utf-8')
            first=process(folder,[],reader)
            self.assertEqual(len(first['additions']),3)
            second=process(folder,first['additions'],reader)
            self.assertEqual(second['additions'],[])
            self.assertEqual({r['codeId'] for r in second['summary']},{'cf','cpp','cpc'})
            self.assertTrue(all(r['outcome']=='same_normative_text' for r in second['comparisons']))

    def test_saved_refresh_keeps_all_records_and_other_ten_sources(self):
        root=Path(__file__).resolve().parents[2]
        runs=sorted(p for p in (root/'experiments/html-history/source-refresh').glob('*/manifest.json') if json.loads(p.read_text(encoding='utf-8')).get('runKind')!='numbering_reprocess')
        if not runs:
            self.skipTest('Run the controlled source refresh first')
        run=runs[-1].parent
        manifest=json.loads((run/'manifest.json').read_text(encoding='utf-8'))
        result=json.loads((run/'results.json').read_text(encoding='utf-8'))
        before=json.loads((run/'previous-fixture-before.json').read_text(encoding='utf-8'))['records']
        correction=root/'experiments/html-history/association-review/20261021/fixture-before.json'
        after=json.loads((correction if correction.exists() else root/'tests/fixtures/previous-wordings-html.json').read_text(encoding='utf-8'))['records']
        self.assertEqual(after[:len(before)],before)
        baseline=json.loads((root/'experiments/html-history/existing-records.json').read_text(encoding='utf-8'))
        baseline+=json.loads((root/'tests/fixtures/legislative-history-html.json').read_text(encoding='utf-8'))['records']
        baseline+=before
        self.assertEqual(json.loads((run/'existing.json').read_text(encoding='utf-8')),baseline)
        expected=before+result['additions']
        later=sorted(p for p in (root/'experiments/html-history/source-refresh').glob('*/manifest.json') if p.parent.name>run.name and json.loads(p.read_text(encoding='utf-8')).get('runKind')=='numbering_reprocess')
        for p in later:
            snapshot=json.loads((p.parent/'previous-fixture-before.json').read_text(encoding='utf-8'))['records']
            self.assertEqual(snapshot,expected)
            expected+=json.loads((p.parent/'results.json').read_text(encoding='utf-8'))['additions']
        self.assertEqual(after,expected)
        self.assertEqual(len({r['id'] for r in after}),len(after))
        self.assertFalse(manifest['publicationAllowed'])
        self.assertTrue(all(r['review']=={'status':'pending'} and r['wording']['status']=='previous' for r in result['additions']))
        self.assertTrue({r['codeId'] for r in result['additions']} <= {'cf','cpp','cpc'})
        changed={n for n,h in manifest['sourcesBefore'].items() if manifest['sourcesAfter'][n]!=h}
        self.assertEqual(changed,{'Constituição.html','Del3689.html','L13105compilada.html'})
        for name,digest in manifest['sourcesAfter'].items():
            self.assertEqual(hashlib.sha256((root/'HTML'/name).read_bytes()).hexdigest(),digest)
        for name,digest in manifest['sourcesBefore'].items():
            self.assertTrue(source_path(name,digest).is_file())
        for name,digest in manifest['files'].items():
            self.assertEqual(hashlib.sha256((run/name).read_bytes()).hexdigest(),digest)

    def test_numbering_reprocess_is_additive_and_does_not_mutate_existing_records(self):
        with tempfile.TemporaryDirectory(dir=TEMP) as directory:
            folder=Path(directory)
            text=('<!-- saved from url=(0050)https://www.planalto.gov.br/test.htm -->'
                '<meta charset="utf-8"><p><s>Art. 406. Anterior.</s></p><p>Art. 497. Final.</p>'
                '<p><a name="capituloii">CAPÍTULO II</a></p><p><a name="art406">Art. 406. Atual.</a></p>'
                '<p><s>Art. 498. Recuperada.</s></p>')
            (folder/'Del3689.html').write_text(text,encoding='utf-8')
            first=reprocess(folder,[],{'cpp':['406','497','498']},['cpp'])
            self.assertEqual(len(first['additions']),2)
            snapshot=json.dumps(first['additions'],ensure_ascii=False)
            second=reprocess(folder,first['additions'],{'cpp':['406','497','498']},['cpp'])
            self.assertEqual(second['additions'],[])
            self.assertEqual(json.dumps(first['additions'],ensure_ascii=False),snapshot)

    def test_saved_numbering_run_preserves_baseline_states_sources_and_raw_evidence(self):
        from extract_previous_html import decode, split_notes
        root=Path(__file__).resolve().parents[2]
        runs=sorted(p for p in (root/'experiments/html-history/source-refresh').glob('*/manifest.json') if json.loads(p.read_text(encoding='utf-8')).get('runKind')=='numbering_reprocess')
        if not runs:
            self.skipTest('Run the corrected numbering preparation first')
        run=runs[-1].parent
        m=json.loads((run/'manifest.json').read_text(encoding='utf-8'))
        result=json.loads((run/'results.json').read_text(encoding='utf-8'))
        baseline=json.loads((run/'previous-fixture-before.json').read_text(encoding='utf-8'))['records']
        correction=root/'experiments/html-history/association-review/20261021/fixture-before.json'
        actual=json.loads((correction if correction.exists() else root/'tests/fixtures/previous-wordings-html.json').read_text(encoding='utf-8'))['records']
        self.assertEqual(actual,baseline+result['additions'])
        self.assertEqual(m['sourcesBefore'],m['sourcesAfter'])
        self.assertFalse(m['publicationAllowed'])
        decoded={}
        for row in result['additions']:
            self.assertEqual(row['review'],{'status':'pending'})
            self.assertEqual(row['wording']['status'],'previous')
            self.assertNotIn('blockquote',row['evidence']['contextTags'])
            name=row['source']['document']
            if name not in decoded:
                raw=(root/'HTML'/name).read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(),row['source']['sha256'])
                decoded[name]=decode(raw)[0]
            a,b=row['evidence']['charRange']
            self.assertEqual(decoded[name][a:b],row['evidence']['rawHtml'])
            self.assertEqual(split_notes(row['evidence']['rawText'])[0],row['text'])
        self.assertTrue(all(not r['recognizedBefore'] or r['recognizedAfter'] for r in result['comparisons']))


if __name__=='__main__':
    unittest.main()
