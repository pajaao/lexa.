"""Documentary note rules reused from the 58/103/115 POC; no legal consolidation."""
import re,collections
TARGET={}
REF=re.compile(r'Emenda (?P<grafia>Constitucional|Constituição Constitucional)\s+n[º°o.]?\s*(?P<n>\d+)\s*,\s*de\s+(?P<data>[^()]{0,75}?\d{4})',re.I)
OP=re.compile(r'^(Redação dada|Incluíd[oa]s?|Acrescid[oa]s?|Revogad[oa]s?|Renumerad[oa]s?|Transformad[oa]s?)\s+pel[ao]\s+',re.I)
ART=re.compile(r'^(?:Art\.?\s*)(\d+(?:-[A-Z])?)[ºo°.]*',re.I)
PAR=re.compile(r'^§\s*(\d+)[ºo°.]*(-[A-Z])?')
INC=re.compile(r'^([IVXLCDM]+)\s*[-–—]')
ALI=re.compile(r'^([a-z])\s*\)')
clean=lambda x:re.sub(r'\s+',' ',x).strip()
def text(p):return ''.join(r['text'] for r in p['runs'])
def bracket(s,pos):
 stack=[]
 for i,c in enumerate(s):
  if c=='(':stack.append(i)
  elif c==')' and stack:
   start=stack.pop()
   if start<pos<i:return start,i+1,s[start:i+1]
 return None

def unit(s,state):
 s=re.sub(r'^["“«]\s*','',clean(s));m=ART.match(s)
 if m:state.clear();return 'caput',s[m.end():]
 m=PAR.match(s)
 if m:state.clear();state['p']='§'+m[1]+(m[2] or '');return state['p'],s[m.end():]
 if re.match(r'^Parágrafo\s+[úu]nico',s):state.clear();state['p']='paragrafo_unico';return state['p'],re.sub(r'^Parágrafo\s+[úu]nico\.?','',s)
 m=INC.match(s)
 if m:state['i']=m[1];return '/'.join([state['p']] if state.get('p') else [])+('/' if state.get('p') else '')+m[1],s[m.end():]
 m=ALI.match(s)
 if m:return '/'.join(([state['p']] if state.get('p') else [])+([state['i']] if state.get('i') else [])+[m[1]+')']),s[m.end():]
 return None,s

def inventory(ec):
 out=[];skipped=[];article=None;scope=None;own=None;state={};owntext='';repealing=False;repealscope=False
 for b in ec['blocos_normativos']:
  s=clean(b['texto']);plain=re.sub(r'^["“«]\s*','',s)
  if b['classe']=='artigo_proprio':
   own=b['artigo'];owntext=s;article=None;state={};repealing=False;repealscope=False;scope='adct' if 'Ato das Disposições Constitucionais Transitórias' in s else 'main' if 'Constituição Federal' in s else None
   # Never confirm a quotation merely because the caput mentions the Constitution.
   if not re.search(r'passa[m]? a vigorar|fica[m]? (?:acrescid|alterad)|nova redação|acrescent|alterad',s,re.I) or re.search(r'Emenda Constitucional.+Constituição Federal',s,re.I):scope=None;repealing=bool(re.search(r'\bRevogam-se\b',s));repealscope=False;continue
  if repealing:
   if re.match(r'^[IVXLCDM]+\s*[-–—]',s):repealscope='os seguintes dispositivos da Constituição Federal' in s
   if repealscope:
    m=re.search(r'§\s*(\d+)\s+do\s+art\.\s*(\d+(?:-[A-Z])?)',s)
    if m:out.append({'scope':'main','artigo':m[2],'unidade':'§'+m[1],'operacao_original':'revogacao_expressa','artigo_ec':own,'bloco_ec':b['id'],'texto_literal_ec':b['texto'],'linha_html':b['linha'],'offset_html':b['offset'],'fundamento':'Revogam-se + inciso que identifica dispositivos da Constituição Federal + alvo literal.'})
   continue
  if b['classe']=='artigo_citado':
   m=ART.match(plain);article=m[1] if m else None;state={}
  if article is None or scope is None:continue
  u,body=unit(s,state)
  if u is None:continue
  # Pontilhados de omissão não demonstram nova redação do caput ou da subdivisão omitida.
  substantive=re.sub(r'\(NR\)|\(AC\)','',body);substantive=re.sub(r'[\s.\-–—"“”«»;:]','',substantive)
  if not re.search(r'[^\W\d_]|\d',substantive):continue
  out.append({'scope':scope,'artigo':article,'unidade':u,'operacao_original':'trecho_reproduzido_em_comando_modificador','artigo_ec':own,'comando_modificador_literal':owntext,'bloco_ec':b['id'],'texto_literal_ec':b['texto'],'linha_html':b['linha'],'offset_html':b['offset'],'fundamento':'Dispositivo reproduzido em citação pertencente ao comando modificador explícito da Constituição/ADCT.'})
 return out

def scan(cf,mon):
 out=[];represented=set()
 for article in cf['articles']:
  state={}
  for pi,p in enumerate(article['paragraphs']):
   s=text(p);u,_=unit(s,state);sb=p.get('sourceBlock');represented.add(sb)
   for m in REF.finditer(s):
    n=int(m['n'])
    if n not in TARGET:continue
    br=bracket(s,m.start());note=br[2] if br else None;notehead=clean(note[1:-1]) if note else '';op=OP.match(notehead);isnote=bool(op and br[0]+1+op.end()==m.start());year=int(re.search(r'\d{4}$',m['data'])[0]);norm=s[:br[0]] if br else s
    # A marcação do texto normativo antes da nota determina se é redação anterior.
    relevant=[];at=0
    for r in p['runs']:
     end=at+len(r['text']);piece=r['text'][:max(0,min(len(r['text']),len(norm)-at))]
     if piece.strip():relevant.append(r['deleted'])
     at=end
    status='anterior_riscada' if relevant and all(relevant) else 'marcacao_mista' if any(relevant) else 'texto_nao_riscado'
    reason='nota_modificadora' if isnote else 'vide_nao_e_modificacao' if re.match(r'^Vide\b',notehead,re.I) else 'mencao_normativa_ou_nota_sem_comando_modificador'
    snapshot=mon['document']['blocks'][sb-1] if sb and 0<sb<=len(mon['document']['blocks']) else None
    out.append({'ec':n,'ano':year,'artigo_id':article['id'],'artigo_numero':article['number'],'scope':article['scope'],'unidade':u,'operacao_nota':op[1] if isnote else None,'nota_literal':note,'referencia_literal':m[0],'texto_bloco_literal':s,'norma_antes_da_nota_literal':norm,'estado_documental':status,'grafia_atipica_controlada':m['grafia']=='Constituição Constitucional','origem':{'sourceBlock_base_1':sb,'monitor_index_base_0':sb-1 if sb else None,'paragrafo_index':pi,'pointer_dados':f"/cf/articles/{cf['articles'].index(article)}/paragraphs/{pi}",'pointer_monitor':f'/document/blocks/{sb-1}' if sb else None,'offset_nota_no_bloco':[br[0],br[1]] if br else None,'runs_monitor':snapshot},'bloco_monitor_confere':snapshot==p['runs'],'tipo_candidato':reason,'ano_confere':year==TARGET[n],'grafia_documentada':m['grafia']=='Constitucional' or (m['grafia']=='Constituição Constitucional' and n==58 and year==2009)})
 # Notas fora de parágrafos: examina separadamente sem atribuí-las ao artigo vizinho.
 for bi,rs in enumerate(mon['document']['blocks']):
  if bi+1 in represented:continue
  s=''.join(r['text'] for r in rs)
  for m in REF.finditer(s):
   n=int(m['n'])
   if n in TARGET:out.append({'ec':n,'artigo_id':None,'scope':None,'unidade':None,'texto_bloco_literal':s,'referencia_literal':m[0],'tipo_candidato':'nota_estrutural_ou_fora_de_artigo','origem':{'monitor_index_base_0':bi,'sourceBlock_base_1':bi+1},'bloco_monitor_confere':True})
 return out


def generate(cf,mon,records):
 global TARGET
 TARGET={int(r['fonte']['identidade']['numero']):int(re.search(r'\d{4}',r['fonte']['identidade']['cabecalho'])[0]) for r in records}
 inventories={n:inventory(next(r for r in records if r['fonte']['identidade']['numero']==n)) for n in TARGET}
 occurrences=scan(cf,mon);confirmed=[];uncertain=[];excluded=[]
 for i,x in enumerate(occurrences):
  x['id']=f'ec-note-{i+1}';n=x['ec']
  if x['tipo_candidato']!='nota_modificadora':x['classificacao']='referencia_excluida';excluded.append(x);continue
  evidence=[b for b in inventories[n] if b['scope']==x['scope'] and b['artigo']==x['artigo_numero'] and b['unidade']==x['unidade']]
  x['evidencias_ec']=evidence
  x['classificacao']='confirmado' if evidence and x['bloco_monitor_confere'] and x['ano_confere'] and x.get('grafia_documentada',False) and x['estado_documental']!='marcacao_mista' else 'conferencia_humana'
  (confirmed if x['classificacao']=='confirmado' else uncertain).append(x)
 # No unsupported syntax disappears from the audit just because it did not match the strict grammar.
 seen={(x['origem']['monitor_index_base_0'],x['referencia_literal']) for x in occurrences}
 unknown=[]
 for bi,runs in enumerate(mon['document']['blocks']):
  s=''.join(r['text'] for r in runs)
  if re.search(r'Emenda\s+Constitu',s,re.I) and not any(index==bi for index,_ in seen):
   if re.search(r'(?:Redação|Incluíd|Acrescid|Revogad|Renumerad|Transformad)',s,re.I):unknown.append({'monitor_index_base_0':bi,'texto_literal':s,'motivo':'Sintaxe modificadora fora da gramática estrita ou EC não disponível; nenhuma associação automática.'})
 missing=[]
 for n,items in inventories.items():
  keys={(x['scope'],x['artigo_numero'],x['unidade']) for x in confirmed if x['ec']==n}
  missing.extend({'ec':n,**r} for r in items if (r['scope'],r['artigo'],r['unidade']) not in keys)
 return {'scope':sorted(TARGET),'confirmed':confirmed,'uncertain':uncertain,'excluded':excluded,'unrecognized':unknown,'historicalNotConfirmed':missing,'summary':{'amendments':len(records),'confirmed':len(confirmed),'uncertain':len(uncertain),'excluded':len(excluded),'unrecognized':len(unknown),'articlePairs':len({(x['artigo_id'],x['ec']) for x in confirmed}),'historicalNotConfirmed':len(missing)},'limit':'Índice documental por notas, não histórico completo, consolidação ou certificação de vigência.','homologated':False}
