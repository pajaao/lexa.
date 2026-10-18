"""Read-only, standard-library verifier. No imports from the audited pipeline."""
import argparse,csv,hashlib,json,re
from collections import Counter,defaultdict
from pathlib import Path

REVIEW=['decision','justification','evidenceConsulted','needsAdjudication']
def compact(value):return json.dumps(value,ensure_ascii=False,separators=(',',':'))
def sha(value):return hashlib.sha256(value if isinstance(value,bytes) else value.encode()).hexdigest()
def text(paragraph):return ''.join(r['text'] for r in paragraph['runs'])
def utf16_slice(value,start,end):return value.encode('utf-16-le')[2*start:2*end].decode('utf-16-le')
def wire(v):return compact(v) if isinstance(v,(dict,list)) else str(v)
def edge_row(e):
 ev=e['evidence'];join=lambda f:' | '.join(str(f(v)) for v in ev)
 return dict(recordType='edge',id=e['edgeId'],source=e['source']['codeId'],sourceScope=e['source']['scope'],sourceArticle=e['source']['articleId'],sourceSHA=e['source']['editionSha256'],target=e['target']['codeId'],targetScope=e['target']['scope'],targetArticle=e['target']['articleId'],targetSHA=e['target']['editionSha256'],occurrenceIds=e['occurrenceIds'],status=e['status'],paragraphs=join(lambda v:v['paragraph']),startUTF16=join(lambda v:v['span']['start']),endUTF16=join(lambda v:v['span']['end']),literal=join(lambda v:v['literal']),normativeEvidence=join(lambda v:(v['normEvidence'] or {}).get('text','')),syntaxClasses=join(lambda v:v['syntaxClass']),historicalState=join(lambda v:compact(v['historical'])),eligibilityReason=join(lambda v:v['verification']['objectiveReason']),evidence=ev,sourceContext=[text(e['source']['article']['paragraphs'][v['paragraph']]) for v in ev],targetContext=text(e['target']['article']['paragraphs'][0]),evidenceFile='arestas.json#'+e['edgeId'],**dict.fromkeys(REVIEW,''))
def rejected_row(r):
 return dict(recordType='rejection',id=r['id'],source=r['source']['codeId'],sourceScope=r['source']['scope'],sourceArticle=r['source']['articleId'],sourceSHA=r['source']['editionSha256'],target='',targetScope='',targetArticle='',targetSHA='',occurrenceIds=[r['id']],status=r['category'],paragraphs=r['span']['paragraph'],startUTF16=r['span']['start'],endUTF16=r['span']['end'],literal=r['literal'],normativeEvidence=(r['normEvidence'] or {}).get('text',''),syntaxClasses='',historicalState=r['historical'],eligibilityReason=r['exclusionReason']+' / '+r['diagnosticReason'],evidence={k:r[k] for k in ['span','normEvidence','qualifiers','historical','resolution','exclusionReason','diagnosticReason','sampling']},sourceContext=text(r['sourceDocument']['article']['paragraphs'][r['span']['paragraph']]),targetContext='',evidenceFile='rejeicoes-amostra.json#'+r['id'],**dict.fromkeys(REVIEW,''))
def facet(o,reason):return dict(historical=o['historical']['state']!='clear',ambiguity=bool(re.search('norm|scope|identity|qualifier|implicit',o['reason'],re.I)),reproduction=bool(re.search('amendment|reproduc',o['reason'],re.I)),unauthorizedSyntax=bool(re.search('syntax|range|complex',reason,re.I)))
def stratum(o,reason,f):
 parts=[o['source']['codeId'],o['source']['scope'],o['classification'],reason,o['reason'],*[str(f[k]).lower() for k in ['historical','ambiguity','reproduction','unauthorizedSyntax']]]
 return '|'.join(parts)
def verify(folder,snapshot=None):
 folder=Path(folder);issues=[];checks=Counter();dependent=[]
 def check(ok,label,where=''):
  checks[label]+=1
  if not ok:issues.append({'check':label,'record':where})
 try:
  manifest=json.loads((folder/'manifesto.json').read_text());edges_doc=json.loads((folder/'arestas.json').read_text());sample_doc=json.loads((folder/'rejeicoes-amostra.json').read_text())
 except (OSError,ValueError) as e:return {'ok':False,'divergences':[{'check':'read-json','record':str(e)}]}
 check(set(manifest['files'])=={'arestas.json','arestas.csv','rejeicoes-amostra.json','revisao-humana.csv'},'manifest-file-set')
 for name,spec in manifest['files'].items():
  data=(folder/name).read_bytes();check(sha(data)==spec['sha256'],'file-sha256',name);check(len(data)==spec['bytes'],'file-size',name)
 edges=edges_doc['edges'];sample=sample_doc['sampling'];records=sample['records'];occurrences={};pairs=[];hashes={};participations=0
 check(len(edges)==329,'edge-count');check(len({e['edgeId'] for e in edges})==len(edges)==329,'edge-id-unique')
 check(edges_doc['counts']==manifest['counts']==sample_doc['counts'],'declared-counts-correspondence')
 check(dict(Counter(e['status'] for e in edges))=={k:v for k,v in manifest['counts']['statuses'].items() if v},'status-counts')
 check(edges_doc['policy']['mode']=='experimental-only' and set(edges_doc['policy']['classes'])=={'self-qualified-article-list','parenthetical-article-list','adct-self-article','numbered-law-article-list'},'experimental-policy-contract')
 for field in ['schema','baseCommit','editionSet','generation','extractor','policy']:check(edges_doc[field]==sample_doc[field],'metadata-correspondence',field)
 check(len(records)==354,'sample-count');check(len({r['id'] for r in records})==len(records)==354,'sample-id-unique')
 def doc_identity(d):
  check(sha(compact(d['article']))==d['articleSha256'],'article-sha256',d['codeId']+'/'+d['articleId'])
  check(d['article']['id']==d['articleId'] and d['article']['number']==d['number'] and d['article'].get('scope','main')==d['scope'],'article-metadata',d['articleId'])
  if d['codeId'] in hashes:check(hashes[d['codeId']]==d['editionSha256'],'norm-sha-consistency',d['codeId'])
  hashes[d['codeId']]=d['editionSha256']
 def span(s,p,key):
  try:
   n=len(text(p).encode('utf-16-le'))//2
   good=type(s['start']) is int and type(s['end']) is int and 0<=s['start']<s['end']<=n and utf16_slice(text(p),s['start'],s['end'])==s['text']
  except (KeyError,UnicodeError,TypeError):good=False
  check(good,'utf16-span',key)
 def blank(r,key):check(set(r)==set(REVIEW) and all(r[k]=='' for k in REVIEW),'human-review-empty',key)
 for e in edges:
  key=e['edgeId'];s=e['source'];t=e['target'];doc_identity(s);doc_identity(t);blank(e['review'],key)
  pair=[s['codeId'],s['articleId'],t['codeId'],t['articleId']];pairs.append(tuple(pair));check(key==sha(compact([edges_doc['generation'],*pair])),'edge-id-derived',key)
  check(e['occurrenceIds']==[v['occurrenceId'] for v in e['evidence']],'edge-occurrence-correspondence',key)
  check(len(set(e['occurrenceIds']))==len(e['occurrenceIds']),'edge-participation-unique',key)
  for v in e['evidence']:
   oid=v['occurrenceId'];participations+=1;p=s['article']['paragraphs'][v['paragraph']];check(v['paragraphRuns']==p['runs'],'runs-correspondence',oid)
   check(v['span']['paragraph']==v['paragraph'] and v['span']['field']=='paragraphs' and v['span']['offsetUnit']==v['offsetUnit']=='utf16' and v['literal']==v['span']['text'],'location-metadata',oid)
   for part in [v['span'],*v['qualifiers'],*([v['normEvidence']] if v['normEvidence'] else [])]:span(part,p,oid)
   source=dict(codeId=s['codeId'],articleId=s['articleId'],scope=s['scope'],editionSha256=s['editionSha256'])
   check(oid==sha(compact([edges_doc['extractor']['editionSetSha256'],source,v['paragraph'],v['span']['start'],v['span']['end']])),'occurrence-id-derived',oid)
   signature=compact([source,{k:v[k] for k in v if k!='verification'}])
   if oid in occurrences:check(occurrences[oid]==signature,'repeated-occurrence-consistent',oid)
   occurrences[oid]=signature
 check(len(set(pairs))==len(edges)==329,'edge-tuple-unique');check(len(occurrences)==272,'occurrence-count');check(participations==353,'participation-count')
 sample_groups=defaultdict(list)
 for r in records:
  blank(r['review'],r['id']);d=r['sourceDocument'];doc_identity(d);check(all(r['source'][k]==d[k] for k in ['codeId','articleId','scope','editionSha256']),'sample-source-correspondence',r['id']);p=d['article']['paragraphs'][r['span']['paragraph']]
  check(r['paragraphRuns']==p['runs'],'sample-runs',r['id'])
  check(r['id'] not in occurrences,'accepted-rejected-disjoint',r['id'])
  for part in [r['span'],*r['qualifiers'],*([r['normEvidence']] if r['normEvidence'] else [])]:span(part,p,r['id'])
  check(r['id']==sha(compact([edges_doc['extractor']['editionSetSha256'],r['source'],r['span']['paragraph'],r['span']['start'],r['span']['end']])),'sample-id-derived',r['id'])
  surrogate=dict(source=r['source'],classification=r['classification'],historical=r['historical'],reason=r['diagnosticReason']);f=facet(surrogate,r['exclusionReason']);key=stratum(surrogate,r['exclusionReason'],f)
  check(f==r['facets'] and key==r['sampling']['stratum'],'sample-stratum',r['id'])
  check(r['sampling']['seed']==sample['seed'],'sample-seed',r['id']);check(r['sampling']['rank']==sha(sample['seed']+'\0'+r['id']),'sample-rank',r['id']);sample_groups[key].append(r)
 check(sample['seed']=='lexa-1a2-rejeicoes-v1','declared-sampling-seed');check(len(sample_groups)==203,'strata-count');check(sample['population']==4624 and sample['perStratum']==2,'sample-design')
 check(sum(g[0]['sampling']['population'] for g in sample_groups.values())==4624,'strata-population-sum')
 for key,g in sample_groups.items():check(len(g)==min(2,g[0]['sampling']['population']) and all(r['sampling']['selected']==len(g) and r['sampling']['population']==g[0]['sampling']['population'] for r in g),'stratum-quota',key)
 def check_csv(name,expected):
  with (folder/name).open(encoding='utf-8-sig',newline='') as f:reader=csv.DictReader(f);rows=list(reader);columns=reader.fieldnames
  check(len(rows)==len(expected),'csv-count',name);check(columns==list(expected[0]),'csv-columns',name)
  check(len({(r['recordType'],r['id']) for r in rows})==len(rows),'csv-ids-unique',name)
  for i,(r,wanted) in enumerate(zip(rows,expected)):
   check(all(r.get(k)==wire(v) for k,v in wanted.items()) and set(r)==set(wanted),'csv-json-correspondence',name+':'+str(i+2))
   check(all(r.get(k)=='' for k in REVIEW),'csv-review-empty',name+':'+str(i+2))
  return len(rows)
 er=[edge_row(e) for e in edges];rr=[rejected_row(r) for r in records]
 check_csv('arestas.csv',er);review_count=check_csv('revisao-humana.csv',er+rr)
 if snapshot:
  snap=json.loads(Path(snapshot).read_text());corpus=snap['corpus'];codes={c['code']['id']:c for c in corpus['collections']};audit=snap['audit']
  check(sha(compact(corpus))==manifest['legalCorpusHash'],'full-corpus-hash')
  for code_id,digest in hashes.items():check(codes[code_id]['sha256']==digest==sha(compact(codes[code_id]['code'])),'full-norm-sha256',code_id)
  for d in [x for e in edges for x in [e['source'],e['target']]]+[r['sourceDocument'] for r in records]:
   art=next(a for a in codes[d['codeId']]['code']['articles'] if a['id']==d['articleId']);check(art==d['article'],'artifact-corpus-article',d['articleId'])
  dec={d['occurrenceId']:d for d in audit['decisions']};population=[o for o in audit['occurrences'] if not dec[o['id']]['eligible']];groups=defaultdict(list)
  for o in population:
   why=dec[o['id']]['reason'];f=facet(o,why);key=stratum(o,why,f);groups[key].append((sha(sample['seed']+'\0'+o['id']),o['id']))
  chosen={oid for group in groups.values() for _,oid in sorted(group)[:2]}
  check(len(population)==4624 and len(groups)==203,'full-rejection-population')
  check(chosen=={r['id'] for r in records},'deterministic-selection-full-population')
  check({d['occurrenceId'] for d in audit['decisions'] if d['eligible']}==set(occurrences),'accepted-population-correspondence')
 else:dependent.append('Sem população completa: quota/rank conferidos, mas não é possível provar que nenhum rejeitado não selecionado teria rank menor.')
 dependent.extend(['Classificações, universo de candidatos e motivos da população são fornecidos pelo pipeline, não homologados pelo verificador.','SHA de edição depende do corpus incorporado, não certifica autenticidade externa, vigência ou revisão jurídica humana.'])
 return dict(ok=not issues,checks=dict(checks),counts=dict(edges=len(edges),occurrences=len(occurrences),participations=participations,rejectedSample=len(records),reviewCSV=review_count,strata=len(sample_groups)),divergences=issues,metadataDependencies=dependent,snapshotProvided=bool(snapshot))
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('folder');parser.add_argument('--snapshot');parser.add_argument('--output');args=parser.parse_args();result=verify(args.folder,args.snapshot);body=json.dumps(result,ensure_ascii=False,indent=2)+'\n'
 if args.output:
  if Path(args.output).resolve().parent==Path(args.folder).resolve():parser.error('Output must be outside the approved artifact directory')
  Path(args.output).write_text(body)
 else:print(body)
 raise SystemExit(0 if result['ok'] else 1)
