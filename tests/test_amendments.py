"""Offline maintenance and association safety, without changing the real candidate."""
import json,sys,tempfile,unittest,subprocess
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from maintain_amendments import inventory,discover,prepare,incorporate,save,load,CANDIDATE
from amendments_links import inventory as affected

class Amendments(unittest.TestCase):
 def test_discovery_independent_of_constitution(self):
  raw=b'<html><a href="emc142.htm">142</a><a href="emc142.htm">142 repetida</a><a href="../ecr/ecr1.htm">Revisao</a></html>'
  self.assertEqual([x['number'] for x in inventory(raw)],[142])
  with tempfile.TemporaryDirectory() as d:
   result=discover(d,index_bytes=raw)
   self.assertEqual(result['newIdentified'],1);self.assertEqual(result['queue'][0]['status'],'original_source_required');self.assertFalse(result['publicationAuthorized'])

 def test_mentions_and_omissions_are_not_modifications(self):
  def block(text,kind,art='1',id='b1'):return {'texto':text,'classe':kind,'artigo':art,'id':id,'linha':1,'offset':0}
  for command in ['Art. 1º Aplica-se a Constituição Federal.', 'Art. 1º A Emenda Constitucional nº 100 altera a Constituição Federal.']:
   self.assertEqual(affected({'blocos_normativos':[block(command,'artigo_proprio'),block('Art. 5º Texto citado.','artigo_citado','5')]}),[])
  self.assertEqual(affected({'blocos_normativos':[block('Art. 1º O art. 5º da Constituição Federal passa a vigorar com a seguinte redação:','artigo_proprio'),block('Art. 5º ................................ (NR)','artigo_citado','5')]}),[])

 def test_incremental_candidate_requires_review_and_preserves_pending(self):
  # Explicitly fictional EC 999 in a temporary registry, never in the real corpus.
  raw='''<html><head><meta charset="utf-8"></head><body><h1>EMENDA CONSTITUCIONAL Nº 999, DE 1 DE JANEIRO DE 2099</h1><div class="textoNorma"><p>As Mesas da Câmara dos Deputados e do Senado Federal promulgam a seguinte Emenda:</p><p>Art. 1º Texto exclusivamente fictício para teste.</p><p>Brasília, 1 de janeiro de 2099.</p></div></body></html>'''.encode()
  url='https://www2.camara.leg.br/legin/fed/emecon/2099/emendaconstitucional-999-1-janeiro-2099-999999-publicacaooriginal-999999-pl.html'
  with tempfile.TemporaryDirectory() as d:
   d=Path(d);proposal=d/'proposal';candidate=d/'candidate';save(candidate/'catalog.json',{'entries':[],'publicationAuthorized':False,'reviewStatus':'pending'})
   doc=prepare(999,url,raw,proposal,test_only=True)
   self.assertTrue(all(doc['technicalChecks'].values()),doc['technicalChecks'])
   with self.assertRaises(ValueError):incorporate(proposal,candidate)
   save(proposal/'review.json',{'technicalApproved':True,'reviewer':'Fixture técnica','evidence':'Teste isolado, não homologado','publicationAuthorized':False})
   with self.assertRaisesRegex(ValueError,'Fixture'):incorporate(proposal,CANDIDATE)
   self.assertEqual(incorporate(proposal,candidate),999)
   self.assertEqual(load(candidate/'catalog.json')['entries'][0]['review'],'pending')
   self.assertFalse(load(candidate/'documents/ec-999.json')['review']['publicationAuthorized'])
   with self.assertRaisesRegex(ValueError,'já presente'):incorporate(proposal,candidate)
   result=subprocess.run(['node','--input-type=module','-e',"import {buildPackage} from './scripts/build.mjs';const p=await buildPackage({amendmentsCandidate:true,amendmentsDirectory:process.argv[1]});console.log(p.manifest.amendments.count)",str(candidate)],cwd=ROOT,capture_output=True,text=True)
   self.assertEqual(result.returncode,0,result.stderr[-2000:]);self.assertEqual(result.stdout.strip(),'1')
   (proposal/'source.html').write_bytes(b'changed')
   with self.assertRaisesRegex(ValueError,'Original'):incorporate(proposal,candidate)

 def test_incomplete_proposal_cannot_be_incorporated(self):
  raw=b'<html><h1>EMENDA CONSTITUCIONAL N 999</h1><div class="textoNorma"><p>Art. 1 Texto sem fecho</p></div></html>'
  with tempfile.TemporaryDirectory() as d:
   doc=prepare(999,'https://www2.camara.leg.br/emendaconstitucional-999-publicacaooriginal.html',raw,d,browser=False,test_only=True)
   self.assertFalse(all(doc['technicalChecks'].values()))
   with self.assertRaises(ValueError):incorporate(d)

 def test_official_115_omission_alert_is_not_a_normative_quote_repair(self):
  doc=load(CANDIDATE/'documents/ec-115.json');raw=(CANDIDATE/'originals/ec-115.html').read_bytes()
  with tempfile.TemporaryDirectory() as d:
   proposal=prepare(115,doc['source']['url'],raw,Path(d)/'original',test_only=True)
   self.assertTrue(all(proposal['technicalChecks'].values()),proposal['technicalChecks'])
   self.assertTrue(proposal['structuralAlerts']);self.assertTrue(all(x['omissionOnly'] for x in proposal['structuralAlerts']))
   # A substantive, unclosed citation must still be blocked, never normalized.
   altered=raw.replace(proposal['structuralAlerts'][0]['text'].encode('ascii'),b'Texto normativo novo (NR) ')
   self.assertNotEqual(altered,raw)
   rejected=prepare(115,doc['source']['url'],altered,Path(d)/'altered',test_only=True)
   self.assertFalse(rejected['technicalChecks']['citationIntegrity'])

if __name__=='__main__':unittest.main()
