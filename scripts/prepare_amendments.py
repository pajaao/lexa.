"""Prepare a local EC candidate from verified source records; never authorizes publication."""
import argparse,json,re,hashlib,shutil
from pathlib import Path
from amendments_links import generate
ROOT=Path(__file__).resolve().parent.parent
load=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,obj):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
def prepare(base,output):
 corpus=base/'validacao/revalidacao-final/acervo-tecnicamente-validado.json';report=base/'validacao/revalidacao-final/resultado-geral.json';records=load(corpus)['registros'];results={r['id']:r for r in load(report)['registros']}
 if len({r['id'] for r in records})!=len(records):raise ValueError('EC duplicada')
 module=(ROOT/'data/official/legislation.js').read_text(encoding='utf-8');cf=json.loads(module[module.index('{'):].strip().rstrip(';'))['cf'];mon=load(ROOT/'monitor/official/cf.json')
 if cf['source']['sha256']!=mon['semantic_sha256']:raise ValueError('Constituição e snapshot são de edições diferentes')
 entries=[];corpus_hash=sha(corpus)
 for r in records:
  if not r['situacao'].startswith('VALIDADA TECNICAMENTE') or results[r['id']]['falhas']:raise ValueError('Registro sem validação técnica: '+r['id'])
  source=base/r['fonte']['arquivo'];evidence=base/'validacao/revalidacao-final'/r['evidencia']
  if sha(source)!=r['fonte']['sha256']:raise ValueError('Original alterado: '+r['id'])
  number=r['fonte']['identidade']['numero'];identity=r['fonte']['identidade'];year=int(re.search(r'\d{4}',identity['cabecalho'])[0]);blocks=[]
  for b in r['blocos_normativos']:
   runs=[{'text':x['texto'],'deleted':x['riscado']} for x in b['runs']]
   if ''.join(x['text'] for x in runs)!=b['texto']:raise ValueError('Runs não preservam o bloco')
   blocks.append({'id':b['id'],'text':b['texto'],'runs':runs,'kind':b['classe'],'ownArticle':b['artigo_proprio_contexto'],'citedArticle':b.get('artigo_citado_contexto_documental'),'unit':b['unidade_documental'],'source':{'line':b['linha'],'offset':b['offset']}})
  if '\n'.join(x['text'] for x in blocks)!=r['texto_normativo_documentado']:raise ValueError('Texto normativo incompleto')
  small=lambda b:{'text':b['texto'],'runs':[{'text':x['texto'],'deleted':x['riscado']} for x in b['runs']],'source':{'line':b['linha'],'offset':b['offset']}}
  document={'id':r['id'],'number':number,'year':year,'date':identity['data_cabecalho'] or identity['data_fecho'],'dateKind':'Data do cabeçalho' if identity['data_cabecalho'] else 'Data do fecho','identity':identity,'source':r['fonte'],'collection':r['metadados_coleta'],'technicalStatus':r['situacao'],'caveats':r['ressalvas_documentais'],'review':{'status':'pending','publicationAuthorized':False},'evidence':{'path':r['evidencia'],'sha256':sha(evidence),'content':load(evidence)},'preamble':small(r['preambulo']) if r['preambulo'] else None,'ementas':[small(x) for x in r['ementas']],'blocks':blocks,'closing':[small(x) for x in r['assinaturas_e_fecho']],'publications':r['publicacoes'],'ownArticles':r['artigos_proprios']}
  # Detailed prior comparisons stay in the preservation bundle, not the first reader download.
  preservation={'evidence':document.pop('evidence'),'originalSource':r['fonte'],'inputCorpusHash':corpus_hash}
  docpath=output/'documents'/f'ec-{number}.json';save(docpath,document);save(output/'evidence'/f'ec-{number}.json',preservation)
  rawpath=output/'originals'/f'ec-{number}.html';rawpath.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,rawpath)
  if sha(rawpath)!=r['fonte']['sha256']:raise ValueError('Cópia não íntegra')
  entries.append({'id':r['id'],'number':number,'year':year,'date':document['date'],'dateKind':document['dateKind'],'ementa':'\n'.join(x['text'] for x in document['ementas']),'document':str(docpath.relative_to(output)).replace('\\','/'),'sha256':sha(docpath),'original':str(rawpath.relative_to(output)).replace('\\','/'),'originalSha256':sha(rawpath),'technicalStatus':r['situacao'],'review':'pending'})
 audit=generate(cf,mon,records);save(output/'links-audit.json',audit)
 save(output/'catalog.json',{'schemaVersion':1,'publicationAuthorized':False,'reviewStatus':'pending','sourceCorpus':{'path':str(corpus),'sha256':sha(corpus)},'constitutionSemanticHash':mon['semantic_sha256'],'entries':sorted(entries,key=lambda x:x['number'])})
 print(json.dumps({'documents':len(entries),'links':audit['summary'],'output':str(output)},ensure_ascii=False))
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,default=Path('D:/Projetos/Extracao-Emendas-Constitucionais'));p.add_argument('--output',type=Path,default=ROOT/'data/amendments/candidate');a=p.parse_args();prepare(a.source,a.output)
