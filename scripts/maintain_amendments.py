"""Prepare new EC proposals using official sources; never publishes or edits the current CF."""
import argparse,json,re,hashlib,shutil,time,sys
from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import urljoin,urlsplit
from official_http import fetch,check_url
from amendments_source import Parser,decode,source,clean,ART
from amendments_links import generate
ROOT=Path(__file__).resolve().parent.parent;CANDIDATE=ROOT/'data/amendments/candidate'
INDEX='https://www.planalto.gov.br/ccivil_03/constituicao/emendas/emc/quadro_emc.htm'
ALLOWED={'www.planalto.gov.br','planalto.gov.br','www2.camara.leg.br'}
sha=lambda b:hashlib.sha256(b).hexdigest()
load=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,value):p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
def preserve(path,data):
 path.parent.mkdir(parents=True,exist_ok=True)
 if path.exists() and path.read_bytes()!=data:raise ValueError('Arquivo preservado não pode ser sobrescrito: '+str(path))
 path.write_bytes(data)
def inventory(raw,url=INDEX):
 html,encoding=decode(raw);tree=Parser(html);out={}
 for a in tree.root.all('a'):
  href=urljoin(url,a.attrs.get('href',''));m=re.search(r'/emc/emc(\d+)\.htm(?:l)?(?:#.*)?$',href,re.I)
  if not m:continue
  check_url(href);n=int(m[1]);out[n]={'number':n,'label':clean(a.text()),'url':href,'origin':'quadro_oficial_planalto','encoding':encoding}
 return list(out.values())
DOM='''el=>{const blocks=[];let pieces=[];const boundary=new Set(['P','DIV','BLOCKQUOTE','DIR','TD','TH','TR','LI','H1','H2','H3','H4','BR','HR']);const clean=x=>x.replace(/\\s+/gu,' ').trim();const flush=()=>{if(clean(pieces.join('')))blocks.push(pieces.join(''));pieces=[];};function walk(n){if(n.nodeType===3){pieces.push(n.nodeValue);return;}if(n.nodeType!==1||['SCRIPT','STYLE','HEAD'].includes(n.tagName))return;if(boundary.has(n.tagName))flush();for(const c of n.childNodes)walk(c);if(boundary.has(n.tagName))flush();}walk(el);flush();return blocks;}'''
def verify_browser(html,parsed):
 from playwright.sync_api import sync_playwright
 with sync_playwright() as p:
  browser=p.chromium.launch(executable_path=shutil.which('chromium') or shutil.which('chromium-browser'),args=['--no-sandbox']);page=browser.new_page();page.route('**/*',lambda r:r.abort());page.set_content(re.sub(r'<script\b[^>]*>[\s\S]*?</script\s*>','',html,flags=re.I),wait_until='domcontentloaded');blocks=page.locator('.textoNorma').evaluate(DOM);head=page.locator('h1').all_text_contents();browser.close()
 return {'fullTextAndOrder':[clean(x) for x in blocks]==[clean(x['texto']) for x in parsed['linhas']],'identityHeading':parsed['identidade']['cabecalho'] in [clean(x) for x in head],'blocks':len(blocks),'method':'DOM Chromium independente, rede/scripts da fonte bloqueados; apenas espaços normalizados.'}
def prepare(number,url,raw,directory,*,browser=True,test_only=False,transport='provided_file'):
 check_url(url,ALLOWED)
 if urlsplit(url).hostname!='www2.camara.leg.br' or f'emendaconstitucional-{number}-' not in url or 'publicacaooriginal' not in url:raise ValueError('Exigir URL oficial da publicação original da Câmara e número correspondente')
 directory=Path(directory);sourcepath=directory/'source.html';preserve(sourcepath,raw);html,encoding=decode(raw);parsed=source(sourcepath,'camara',url)
 number_ok=parsed['identidade']['numero']==number
 lines=parsed['linhas'];first=next((i for i,x in enumerate(lines) if ART.match(x['comparacao'])),None)
 fold=lambda s:''.join(c for c in __import__('unicodedata').normalize('NFD',s).lower() if not __import__('unicodedata').combining(c))
 end=next((i for i,x in enumerate(lines) if first is not None and i>first and re.match(r'^(brasilia\b|mesa(?:s)?\s+d[ao]\b|deputad[oa]\s+|senador(?:a)?\s+)',fold(x['comparacao']))),None)
 body=lines[first:end] if first is not None and end is not None else []
 own=[x['artigo'] for x in body if x.get('classe')=='artigo_proprio'];regular=bool(own) and (own==['único'] or own==[str(n) for n in range(1,len(own)+1)])
 review={'status':'pending','technicalApproved':False,'reviewer':None,'evidence':None,'publicationAuthorized':False}
 checks={'identity':number_ok,'originalPublicationURL':True,'bodyBoundaries':bool(body),'ownArticleSequence':regular,'replacementCharactersAbsent':'\ufffd' not in html,'encodingConfirmed':encoding['criterio'] in ['meta','HTTP','BOM'] or encoding['encoding']=='utf-8'}
 try:independent=verify_browser(html,parsed) if browser else {'fullTextAndOrder':False,'identityHeading':False,'reason':'Verificação independente não executada.'}
 except Exception as e:independent={'fullTextAndOrder':False,'identityHeading':False,'reason':str(e)}
 checks['independentText']=independent['fullTextAndOrder'];checks['independentIdentity']=independent['identityHeading']
 runs=lambda b:[{'text':r['texto'],'deleted':r['riscado']} for r in b['runs']]
 small=lambda b:{'text':b['texto'],'runs':runs(b),'source':{'line':b['linha'],'offset':b['offset']}}
 identity=parsed['identidade'];year_match=re.search(r'\b\d{4}\b',identity['cabecalho']);checks['yearIdentified']=year_match is not None
 preamble=next((x for x in lines if re.search(r'\bAs Mesas\b',x['comparacao'],re.I)),None)
 ementas=[x for x in lines[:first or 0] if x is not preamble and x['comparacao'] in identity['ementas']]
 blocks=[{'id':b['id'],'text':b['texto'],'runs':runs(b),'kind':b.get('classe','nao_classificado'),'ownArticle':b.get('artigo_proprio_contexto'),'citedArticle':b['artigo'] if b.get('classe')=='artigo_citado' else None,'unit':b.get('unidade_marcador'),'source':{'line':b['linha'],'offset':b['offset']}} for b in body]
 # EC115's original has an omission-only dotted line ending in (NR), without
 # closing quotation marks. Preserve that documented presentation, not a claim
 # that normative content was recovered or repaired. Other quote defects block.
 structural_alerts=[{'line':b['linha'],'offset':b['offset'],'text':b['texto'],'omissionOnly':bool(re.fullmatch(r'[.\s…]+\(NR\)\s*[.;]?',b['comparacao'],re.I)),'reason':'Aspas de fechamento ausentes antes de (NR) na fonte original.'} for b in body if b.get('citacao_malformada')]
 checks['citationIntegrity']=all(x['omissionOnly'] for x in structural_alerts)
 checks['allBlocksHaveOwnArticle']=bool(body) and all(b.get('artigo_proprio_contexto') in own for b in body)
 checks['allRunsPreserved']=all(''.join(x['text'] for x in b['runs'])==b['text'] for b in blocks)
 document={'id':f'emc-{number:03d}','number':number,'year':int(year_match[0]) if year_match else None,'date':identity['data_cabecalho'] or identity['data_fecho'],'dateKind':'Data do cabeçalho' if identity['data_cabecalho'] else 'Data do fecho','identity':identity,'source':{'url':url,'sha256':sha(raw),'codificacao':encoding,'identidade':identity},'collection':{'coleta_utc':datetime.now(timezone.utc).isoformat(),'status_http':200 if transport=='official_http' else None,'transport':transport,'sha256':sha(raw),'tamanho_bytes':len(raw)},'technicalStatus':'Verificação técnica executada; revisão da proposta pendente' if all(checks.values()) else 'PENDENTE DE VALIDAÇÃO','technicalChecks':checks,'independent':independent,'caveats':['Preparação automática de proposta; requer revisão técnica e homologação jurídica antes da publicação.'],'review':{'status':'pending','publicationAuthorized':False},'ementas':[small(x) for x in ementas],'preamble':small(preamble) if preamble else None,'blocks':blocks,'closing':[small(x) for x in lines[end:] if not x['comparacao'].startswith('Este texto')] if end else [],'publications':identity['publicacoes'],'ownArticles':own,'testOnly':test_only}
 document['structuralAlerts']=structural_alerts
 if structural_alerts:document['caveats'].append('Anomalias de aspas na fonte preservadas em structuralAlerts; conferir individualmente na revisão técnica.')
 save(directory/'document.json',document)
 if not (directory/'review.json').exists():save(directory/'review.json',review)
 save(directory/'checks.json',{'checks':checks,'independent':independent,'technicalReady':all(checks.values()),'publicationAuthorized':False})
 return document

def legacy(document):
 return {'fonte':document['source'],'blocos_normativos':[{'id':b['id'],'texto':b['text'],'classe':b['kind'],'artigo':b['ownArticle'] if b['kind']=='artigo_proprio' else b['citedArticle'],'linha':b['source']['line'],'offset':b['source']['offset']} for b in document['blocks']]}
def incorporate(directory,candidate=CANDIDATE):
 directory=Path(directory);candidate=Path(candidate);document=load(directory/'document.json');review=load(directory/'review.json')
 if not all(document['technicalChecks'].values()) or not review.get('technicalApproved') or not review.get('reviewer') or not review.get('evidence'):raise ValueError('Proposta sem verificações ou revisão técnica documentada')
 if review.get('publicationAuthorized') is not False:raise ValueError('Inclusão candidata não autoriza publicação')
 if document.get('testOnly') and candidate.resolve()==CANDIDATE.resolve():raise ValueError('Fixture não pode entrar na candidata real')
 raw=(directory/'source.html').read_bytes()
 if sha(raw)!=document['source']['sha256']:raise ValueError('Original da proposta alterado')
 catalog=load(candidate/'catalog.json');n=document['number']
 if any(x['number']==n for x in catalog['entries']):raise ValueError('EC já presente; não sobrescrever')
 preserve(candidate/'originals'/f'ec-{n}.html',raw);save(candidate/'documents'/f'ec-{n}.json',document);save(candidate/'evidence'/f'ec-{n}.json',{'technicalReview':review,'checks':load(directory/'checks.json')})
 catalog['entries'].append({'id':document['id'],'number':n,'year':document['year'],'date':document['date'],'dateKind':document['dateKind'],'ementa':'\n'.join(x['text'] for x in document['ementas']),'document':f'documents/ec-{n}.json','sha256':sha((candidate/'documents'/f'ec-{n}.json').read_bytes()),'original':f'originals/ec-{n}.html','originalSha256':sha(raw),'technicalStatus':document['technicalStatus'],'review':'pending'})
 catalog['entries'].sort(key=lambda x:x['number']);save(candidate/'catalog.json',catalog)
 # The same documentary mechanism regenerates all links, never a hand-maintained association table.
 module=(ROOT/'data/official/legislation.js').read_text(encoding='utf-8');cf=json.loads(module[module.index('{'):].strip().rstrip(';'))['cf'];mon=load(ROOT/'monitor/official/cf.json');records=[legacy(load(candidate/x['document'])) for x in catalog['entries']];save(candidate/'links-audit.json',generate(cf,mon,records))
 return n

def discover(output,index_bytes=None,collect=False):
 output=Path(output);raw=index_bytes if index_bytes is not None else fetch({'url':INDEX},attempts=2)[0];digest=sha(raw);preserve(output/'sources'/f'index-{digest}.html',raw)
 known={x['number'] for x in load(CANDIDATE/'catalog.json')['entries']};found=inventory(raw);new=[x for x in found if x['number'] not in known];queue=[]
 for entry in new[:10]:
  item={**entry,'status':'original_source_required','publicationAuthorized':False}
  if collect:
   try:
    data,_=fetch({'url':entry['url']},attempts=2);preserve(output/'sources'/f'planalto-{entry["number"]}-{sha(data)}.html',data);html,_=decode(data)
    originals={urljoin(entry['url'],a.attrs.get('href','')) for a in Parser(html).root.all('a') if 'www2.camara.leg.br' in a.attrs.get('href','') and 'publicacaooriginal' in a.attrs.get('href','') and f'emendaconstitucional-{entry["number"]}-' in a.attrs.get('href','')}
    if len(originals)==1:
     url=originals.pop();raw_original,_=fetch({'url':url},attempts=2,allowed_hosts=ALLOWED);doc=prepare(entry['number'],url,raw_original,output/f'ec-{entry["number"]}',transport='official_http');item['status']='proposal_prepared';item['technicalChecks']=doc['technicalChecks']
    else:item['reason']='Publicação original da Câmara não encontrada de forma inequívoca no documento oficial. Fornecer URL oficial ao comando prepare; sem reconstrução ou publicação.'
   except Exception as e:item['status']='failed';item['reason']=str(e)
   time.sleep(.8)
  queue.append(item)
 result={'index':{'url':INDEX,'sha256':digest,'collectedAt':datetime.now(timezone.utc).isoformat(),'transport':'provided_file' if index_bytes is not None else 'official_http','status_http':None if index_bytes is not None else 200},'totalIdentified':len(found),'newIdentified':len(new),'queue':queue,'publicationAuthorized':False,'limit':10,'unprocessedNew':new[10:]};save(output/'proposals.json',result);return result
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
 d=sub.add_parser('discover');d.add_argument('--output',type=Path,default=ROOT/'monitor/run/amendments');d.add_argument('--index-file',type=Path);d.add_argument('--collect',action='store_true')
 a=sub.add_parser('prepare');a.add_argument('--number',type=int,required=True);a.add_argument('--original-url',required=True);a.add_argument('--file',type=Path);a.add_argument('--output',type=Path,required=True)
 i=sub.add_parser('incorporate-candidate');i.add_argument('directory',type=Path)
 args=p.parse_args()
 if args.command=='discover':print(json.dumps(discover(args.output,args.index_file.read_bytes() if args.index_file else None,args.collect),ensure_ascii=False))
 elif args.command=='prepare':
  check_url(args.original_url,ALLOWED);raw=args.file.read_bytes() if args.file else fetch({'url':args.original_url},attempts=2,allowed_hosts=ALLOWED)[0];doc=prepare(args.number,args.original_url,raw,args.output,transport='provided_file' if args.file else 'official_http');print(json.dumps({'number':doc['number'],'checks':doc['technicalChecks'],'review':'pending'},ensure_ascii=False))
 else:print('Incluída somente na candidata:',incorporate(args.directory))
