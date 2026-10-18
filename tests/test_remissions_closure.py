import csv,importlib.util,json,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('closure',ROOT/'scripts/verify_remissions_closure.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
class ClosureVerification(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.folder=Path(self.tmp.name)/'audit';shutil.copytree(ROOT/'docs/remissoes/fase-1a-2',self.folder)
 def refresh(self,name):
  m=json.loads((self.folder/'manifesto.json').read_text());b=(self.folder/name).read_bytes();m['files'][name]={'sha256':v.sha(b),'bytes':len(b)};(self.folder/'manifesto.json').write_text(json.dumps(m))
 def mutate_json(self,edit):
  p=self.folder/'arestas.json';j=json.loads(p.read_text());edit(j);p.write_text(json.dumps(j,ensure_ascii=False));self.refresh('arestas.json')
 def expect_failure(self,label):
  result=v.verify(self.folder);self.assertFalse(result['ok']);self.assertIn(label,{d['check'] for d in result['divergences']})
 def test_original_artifacts(self):
  result=v.verify(self.folder);self.assertTrue(result['ok'],result['divergences']);self.assertEqual(result['counts']['participations'],353);self.assertFalse(result['snapshotProvided'])
 def test_corrupt_hash(self):
  p=self.folder/'arestas.csv';p.write_bytes(p.read_bytes()+b' ');self.expect_failure('file-sha256')
 def test_changed_id_with_fresh_checksum(self):
  self.mutate_json(lambda j:j['edges'][0].update(edgeId='0'*64));self.expect_failure('edge-id-derived')
 def test_duplicated_edge_with_fresh_checksum(self):
  self.mutate_json(lambda j:j['edges'].append(j['edges'][0]));self.expect_failure('edge-tuple-unique')
 def test_divergent_csv_with_fresh_checksum(self):
  p=self.folder/'arestas.csv';s=p.read_text(encoding='utf-8-sig');s=s.replace('"edge"','"WRONG"',1);p.write_text(s,encoding='utf-8-sig');self.refresh('arestas.csv');self.expect_failure('csv-json-correspondence')
 def test_human_decision_filled_with_fresh_checksum(self):
  p=self.folder/'revisao-humana.csv'
  with p.open(encoding='utf-8-sig',newline='') as f:reader=csv.DictReader(f);cols=reader.fieldnames;rows=list(reader)
  rows[0]['decision']='APROVADO INDEVIDAMENTE'
  with p.open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=cols);w.writeheader();w.writerows(rows)
  self.refresh('revisao-humana.csv');self.expect_failure('csv-review-empty')
 def test_utf16_span_corruption(self):
  self.mutate_json(lambda j:j['edges'][0]['evidence'][0]['span'].update(start=1));self.expect_failure('utf16-span')
 def test_rank_corruption(self):
  p=self.folder/'rejeicoes-amostra.json';j=json.loads(p.read_text());j['sampling']['records'][0]['sampling']['rank']='0'*64;p.write_text(json.dumps(j,ensure_ascii=False));self.refresh('rejeicoes-amostra.json');self.expect_failure('sample-rank')
 def test_utf16_is_not_codepoint_index(self):
  self.assertEqual(v.utf16_slice('🧭 art. 5',0,2),'🧭')
  with self.assertRaises(UnicodeDecodeError):v.utf16_slice('🧭 art. 5',0,1)
 def test_parenthetical_ids_and_no_release(self):
  edges=json.loads((self.folder/'arestas.json').read_text())['edges'];expected={e['edgeId'] for e in edges if e['evidence'][0]['syntaxClass']=='parenthetical-article-list'}
  with (ROOT/'docs/remissoes/fase-1a-2-fechamento/parenteticas.csv').open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))
  self.assertEqual(len(rows),30);self.assertEqual({r['edgeId'] for r in rows},expected);self.assertTrue(all(r['provisionalConclusion']=='pendente de decisão' for r in rows));self.assertTrue(all(r['individualAssessment'] and r['literal'] for r in rows))
if __name__=='__main__':unittest.main()
