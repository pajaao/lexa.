"""PoC investigativa. Sem dependências. Não utilizar como extrator de produção.
Entrada: JSON das edições realmente emitidas por buildPackage(), sem normalizar runs.
Contagem: candidato = expressão art./arts./artigo(s); lista = um candidato.
A/B/C/D são rótulos do algoritmo, não validação jurídica. E = cabeçalho rejeitado.
"""
import argparse,copy,gzip,hashlib,json,platform,re,statistics,time
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).parent
NUM=r'\d+(?:\.\d{3})*(?:[º°o])?(?:\s*-\s*[A-Za-z])?'
HEAD=re.compile(r'\b(?:arts?\.|artigos?)\s*('+NUM+r')',re.I)
TAIL=re.compile(r'\s*(,|e\b|a\b|até\b)\s*('+NUM+r')',re.I)
LAW=re.compile(r'\b(Lei(?:\s+Complementar)?|Decreto[- ]Lei)\s+n\s*[.º°o]*\s*([\d.]+)\s*,?\s*de\s+(?:\d{1,2}\s+de\s+\w+\s+de\s+)?(\d{4})',re.I)
LAWS={('lei','10406','2002'):'civil',('lei','13105','2015'):'cpc',('lei','8078','1990'):'cdc',('lei','5172','1966'):'ctn',('lei','8069','1990'):'eca',('lei','7210','1984'):'lep',('lei','11340','2006'):'maria-penha',('lei','8429','1992'):'improbidade',('lei','14133','2021'):'licitacoes',('decreto-lei','2848','1940'):'penal',('decreto-lei','3689','1941'):'cpp',('decreto-lei','5452','1943'):'clt'}
def number(s):return re.sub(r'[º°o\s.]','',s).upper()
def u16(s):return len(s.encode('utf-16-le'))//2
def raw(p):return ''.join(r['text'] for r in p['runs'])
def extract(corpus,selected=None):
 catalog={c['code']['id']:c for c in corpus['collections']}
 ids={cid:{a['id']:a for a in c['code']['articles']} for cid,c in catalog.items()}
 out=[]
 for cid,c in catalog.items():
  if cid=='sv':continue # Jurisprudential annotations are outside this statutory PoC.
  if selected and cid not in selected:continue
  for a in c['code']['articles']:
   for field in ['paragraphs']:
    for pi,p in enumerate(a.get(field,[])):
     t=raw(p); mask=[]
     for r in p['runs']:mask.extend([bool(r.get('deleted'))]*len(r['text']))
     matches=list(HEAD.finditer(t))
     for mi,m in enumerate(matches):
      end=m.end();nums=[number(m[1])];range_bad=False
      while (n:=TAIL.match(t,end)):
       new=number(n[2]);conn=n[1];end=n.end()
       if conn in ['a','até']:
        if nums[-1].isdigit() and new.isdigit() and 0<int(new)-int(nums[-1])<=50:
         nums.extend(str(v) for v in range(int(nums[-1])+1,int(new)+1))
        else:range_bad=True;nums.append(new)
       else:nums.append(new)
      nxt=matches[mi+1].start() if mi+1<len(matches) else len(t)
      after=t[end:nxt]
      # Parenthetical amendment provenance cannot qualify an earlier citation.
      after=re.split(r'\((?:Redação|Incluído|Revogado|Vide|Vigência|Promulgação)',after,flags=re.I)[0]
      base={'source':[cid,a['id']],'field':field,'paragraph':pi,'span':[u16(t[:m.start()]),u16(t[:end])],'pythonSpan':[m.start(),end],'quote':t[m.start():end],'edition':c['sha256'],'numbers':list(dict.fromkeys(nums)),'targets':[],'historical':False,'granularity':'article'}
      # Every repeated old/new own-heading is still a heading, not a remissão.
      if m.start()==0 and nums[0]==str(a['number']).upper():
       base.update(status='E',reason='own-heading');out.append(base);continue
      deleted=[mask[j] for j in range(m.start(),end) if not t[j].isspace()]
      hist=bool(deleted) and all(deleted);mixed=any(deleted) and not hist
      target=cid;scope='main';why='unqualified-local';uncertain=False;external=False
      law=LAW.search(after)
      if re.search(r'Código Civil anterior',after,re.I):
       target=None;external=True;why='civil-1916'
      elif law:
       key=(law[1].lower().replace('decreto lei','decreto-lei'),law[2].replace('.',''),law[3])
       target=LAWS.get(key);external=target is None;why='explicit-law:'+':'.join(key)
      elif re.search(r'Constitui[çc][ãa]o',after,re.I):target='cf';scope='main';why='explicit-constitution'
      elif re.search(r'ADCT|deste Ato',after,re.I):target='cf';scope='adct';why='explicit-adct'
      elif re.search(r'dest[ae] (?:Lei|Código)',after,re.I):why='explicit-self';scope=a.get('scope','main')
      elif re.search(r'(?:referid[ao]|mesm[ao]|anterior|seguinte)\s+(?:Lei|Código|artigo)|da\s+(?:Lei|Emenda|Resolução|Medida|Convenção|Código)|do\s+(?:Código|Decreto)',after,re.I):uncertain=True;why='unresolved-norm-context'
      elif a.get('scope')=='adct':uncertain=True;why='adct-scope-not-explicit'
      if re.search(r'artigos?\s+(?:anterior|seguinte)',t[end:],re.I):uncertain=True
      if re.match(r'\s*,\s*(?:§|[IVXLCDM]+\b)',after) and m.group(0).lower().startswith(('arts.','artigos')):
       uncertain=True;why='interleaved-list-not-supported'
      if range_bad and not external:uncertain=True;why='range-not-supported'
      if mixed:uncertain=True;why='mixed-deletion'
      targets=[]
      if not external and not uncertain:
       for num in base['numbers']:
        aid=('adct-' if scope=='adct' else '')+num
        found=ids.get(target,{}).get(aid)
        if not found or found.get('rangeEnd'):
         uncertain=True;why='missing-or-grouped-target';targets=[];break
        targets.append([target,aid])
      base.update(status='D' if hist else 'B' if external else 'C' if uncertain else 'A',targets=targets if not uncertain else [],historical=hist,reason=why)
      out.append(base)
 return out

def encoded(x):return json.dumps(x,ensure_ascii=False,separators=(',',':')).encode()
def graph(rows):
 edges=defaultdict(list)
 for i,r in enumerate(rows):
  if r['status']=='A':
   for target in r['targets']:edges[tuple(r['source'])+tuple(target)].append(i)
 # Unique source->target edges, with all independent source occurrences retained.
 table=[[*key,occurrences] for key,occurrences in sorted(edges.items())]
 incoming=defaultdict(list)
 for i,e in enumerate(table):incoming[e[2]+':'+e[3]].append(i)
 return {'edges':table,'incoming':dict(incoming)}
def compact_bundle(corpus,rows):
 kept=[(i,r) for i,r in enumerate(rows) if r['status']!='E'];position={old:new for new,(old,_) in enumerate(kept)}
 g=graph(rows)
 return {'schema':0,'commit':corpus['commit'],'extractor_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'editions':{c['code']['id']:c['sha256'] for c in corpus['collections']},
 'occurrences':[[*r['source'],r['field'],r['paragraph'],*r['span'],r['status'],r['historical'],r['reason']] for _,r in kept],
 'edges':[[*e[:4],[position[n] for n in e[4]]] for e in g['edges']], 'incoming':g['incoming']}

def evaluate(corpus,rows):
 gold=json.loads((ROOT/'manual-sample.json').read_text());errors=[]; matched=correct=missing=spurious=right_targets=0;label_counts=Counter();actual_counts=Counter();pred_links=good_links=gold_links=0
 byfield=defaultdict(list)
 for r in rows:byfield[tuple(r['source'])+(r['paragraph'],)].append(r)
 for g in gold:
  expected=g['expected'];actual=[r for r in byfield[g['code'],g['article'],g['paragraph']] if r['field']=='paragraphs' and r['status']!='E'];used=set();cursor=0
  for e in expected:
   start=g['text'].find(e['literal'],cursor);end=start+len(e['literal']);cursor=end;label_counts[e['status']]+=1
   if e['status']=='A':gold_links+=len(e['targets'])
   candidates=[(i,r) for i,r in enumerate(actual) if i not in used and max(start,r['pythonSpan'][0])<min(end,r['pythonSpan'][1])]
   if not candidates:missing+=1;errors.append({'source':[g['code'],g['article'],g['paragraph']],'expected':e,'actual':None});continue
   i,r=candidates[0];used.add(i);matched+=1
   target_ok=set(':'.join(x) for x in r['targets'])==set(e['targets'])
   ok=r['status']==e['status'] and (target_ok or e['status'] in ['B','C','D'])
   correct+=ok;right_targets+=target_ok
   if not ok:errors.append({'source':[g['code'],g['article'],g['paragraph']],'expected':e,'actual':r})
   if r['status']=='A':
    good_links+=len(set(':'.join(x) for x in r['targets']) & set(e['targets'])) if e['status']=='A' else 0
  for i,r in enumerate(actual):
   actual_counts[r['status']]+=1
   if r['status']=='A':pred_links+=len(r['targets'])
   if i not in used:spurious+=1;errors.append({'source':[g['code'],g['article'],g['paragraph']],'expected':None,'actual':r})
 result=dict(paragraphs=len(gold),articles=len({(g['code'],g['article']) for g in gold}),gold_expressions=sum(label_counts.values()),gold_labels=label_counts,detected_expressions=sum(actual_counts.values()),detected_labels=actual_counts,matched=matched,correct_classifications=correct,missed_expressions=missing,spurious_expressions=spurious,detection_precision=matched/(matched+spurious),detection_recall=matched/(matched+missing),classification_accuracy_on_matched=correct/matched,link_predictions=pred_links,correct_link_predictions=good_links,gold_article_links=gold_links,article_link_precision=good_links/pred_links if pred_links else None,article_link_recall=good_links/gold_links,errors=errors)
 return result

def simulate(corpus):
 baseline=extract(corpus,{'civil'});g=graph(baseline)
 def edges_to_927(rows):return [e[:4] for e in graph(rows)['edges'] if e[:2]==['civil','927']]
 original=edges_to_927(baseline);results=[]
 for scenario in ['add','remove','change','delete-target','strike','rename-target']:
  edition=copy.deepcopy(corpus);c=next(c for c in edition['collections'] if c['code']['id']=='civil');a=next(a for a in c['code']['articles'] if a['id']=='927');r=a['paragraphs'][0]['runs'][0]
  if scenario=='add':r['text']=r['text'].replace('arts. 186 e 187','arts. 186, 187 e 188')
  if scenario=='remove':r['text']=r['text'].replace('(arts. 186 e 187)','')
  if scenario=='change':r['text']=r['text'].replace('arts. 186 e 187','arts. 186 e 188')
  if scenario=='delete-target':c['code']['articles']=[v for v in c['code']['articles'] if v['id']!='187']
  if scenario=='strike':r['deleted']=True
  if scenario=='rename-target':next(v for v in c['code']['articles'] if v['id']=='187')['id']='187-X'
  c['sha256']=hashlib.sha256(encoded(c['code'])).hexdigest()
  new=extract(edition,{'civil'});got=edges_to_927(new)
  wanted={'add':[['civil','927','civil',str(n)] for n in [186,187,188]],'remove':[],'change':[['civil','927','civil',str(n)] for n in [186,188]],'delete-target':[],'strike':[],'rename-target':[]}[scenario]
  assert got==wanted,(scenario,got)
  results.append(dict(scenario=scenario,before=original,after=got,pass_assertion=True,source_edition_changed=c['sha256']!=next(z for z in corpus['collections'] if z['code']['id']=='civil')['sha256']))
 # Target-only edit across norms: source SHA stays unchanged, inventory hash changes.
 edition=copy.deepcopy(corpus);target=next(c for c in edition['collections'] if c['code']['id']=='civil');target['code']['articles']=[a for a in target['code']['articles'] if a['id']!='397'];target['sha256']=hashlib.sha256(encoded(target['code'])).hexdigest()
 before=[r for r in extract(corpus,{'cpc'}) if r['source']==['cpc','240'] and r['status']=='A'];after=[r for r in extract(edition,{'cpc'}) if r['source']==['cpc','240'] and r['status']=='A'];assert before and not after
 results.append(dict(scenario='target-only-change-other-norm',source_sha_unchanged=True,article_240_no_active_relation_after=True,pass_assertion=True))
 return results

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--corpus',default='/tmp/lexa-remissoes-fase0/corpus.json');args=ap.parse_args();corpus=json.load(open(args.corpus));digest=hashlib.sha256(Path(args.corpus).read_bytes()).hexdigest()
 primary={'civil','cf','cpc','licitacoes'};timings=[]
 for _ in range(5):
  start=time.perf_counter();rows=extract(corpus,primary);timings.append(time.perf_counter()-start)
 all_rows=extract(corpus);g=graph(rows);metrics=evaluate(corpus,all_rows)
 # Capture raw scan data separately from gold validation; no corpus-wide precision claim.
 def counts(rs):return dict(Counter(r['status'] for r in rs))
 primary_json=encoded(rows);graph_json=encoded(g);allgraph=encoded(graph(all_rows));counts_articles={c['code']['id']:len(c['code']['articles']) for c in corpus['collections']}
 sizes={}
 for name,data in [('primary_candidates_verbose',primary_json),('primary_graph',graph_json),('all_graph',allgraph)]:sizes[name]={'json_bytes':len(data),'gzip_bytes':len(gzip.compress(data,mtime=0))}
 for name,rs in [('primary_complete_bundle',rows),('all_complete_bundle',all_rows)]:
  b=encoded(compact_bundle(corpus,rs));sizes[name]={'json_bytes':len(b),'gzip_bytes':len(gzip.compress(b,mtime=0))}
 for cid in sorted(primary):
  b=encoded(graph([r for r in rows if r['source'][0]==cid]));sizes['graph_'+cid]={'json_bytes':len(b),'gzip_bytes':len(gzip.compress(b,mtime=0))}
 report=dict(commit=corpus['commit'],corpus_sha256=digest,python=platform.python_version(),platform=platform.platform(),cpu=Path('/proc/cpuinfo').read_text().split('model name')[1].split('\n')[0].strip(': \t'),articles=counts_articles,primary_articles=sum(v for k,v in counts_articles.items() if k in primary),all_articles=sum(counts_articles.values()),scanned_statutory_articles=sum(v for k,v in counts_articles.items() if k!='sv'),primary_counts=counts(rows),all_counts=counts(all_rows),manual_evaluation=metrics,timing_seconds=timings,median_seconds=statistics.median(timings),timing_conditions='In-memory corpus, sequential Python stdlib, five runs, no CPU throttling; excludes corpus loading/serialization and browser/network.',sizes=sizes,primary_edges=len(g['edges']),all_edges=len(graph(all_rows)['edges']),inverse_186=[g['edges'][i] for i in g['incoming'].get('civil:186',[])],simulations=simulate(corpus))
 for file,data in [('results.json',report),('primary-candidates.json',rows),('primary-graph.json',g),('complete-bundle.json',compact_bundle(corpus,all_rows))]: (ROOT/file).write_text(json.dumps(data,ensure_ascii=False,indent=2))
 assert hashlib.sha256(Path(args.corpus).read_bytes()).hexdigest()==digest
 print(json.dumps({k:v for k,v in report.items() if k not in ['manual_evaluation','inverse_186','simulations']},ensure_ascii=False,indent=2));print(json.dumps(metrics,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
