"""Original-publication parser reused from the independently validated EC experiment.
New documents remain proposals; uncertain structures block technical inclusion.
"""
import re,json,hashlib,codecs,unicodedata
from pathlib import Path
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parent;BASE=ROOT.parent
MONTHS={'janeiro':1,'fevereiro':2,'março':3,'abril':4,'maio':5,'junho':6,'julho':7,'agosto':8,'setembro':9,'outubro':10,'novembro':11,'dezembro':12}
ART=re.compile(r'^(?P<quote>[“"«]?)\s*(?:Art\.?\s*(?P<num>\d+)(?:[.º°o]*)(?P<suffix>-[A-Z])?(?=[.\s-]|$)|Artigo\s+(?P<unique>[úu]nico)\b)',re.I)
load=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def clean(s): return re.sub(r'\s+',' ',s).strip()
class Node:
 def __init__(self,tag,attrs,start,parent): self.tag=tag;self.attrs=dict(attrs);self.start=start;self.end=None;self.parent=parent;self.children=[]
 def text(self): return ''.join(c.text() if isinstance(c,Node) else c[0] for c in self.children)
 def all(self,tag):
  for c in self.children:
   if isinstance(c,Node):
    if c.tag==tag: yield c
    yield from c.all(tag)
class Parser(HTMLParser):
 def __init__(self,s):
  super().__init__(convert_charrefs=True);self.s=s;self.lines=[0]+[m.end() for m in re.finditer('\n',s)];self.root=Node('root',[],0,None);self.stack=[self.root];self.feed(s);self.close()
  for n in self.stack: n.end=len(s)
 def source_offset(self): line,col=self.getpos();return self.lines[line-1]+col
 def handle_starttag(self,tag,attrs):
  if tag in ('p','tr','td','th'):
   for i in range(len(self.stack)-1,0,-1):
    if self.stack[i].tag==tag:
     for n in self.stack[i:]: n.end=self.source_offset()
     self.stack=self.stack[:i];break
  n=Node(tag,attrs,self.source_offset(),self.stack[-1]);self.stack[-1].children.append(n)
  if tag not in ('br','hr','img','meta','link','input','wbr','area','base','embed','source'): self.stack.append(n)
  else:
   n.end=self.source_offset()+len(self.get_starttag_text())
   if tag=='br': n.children.append(('\n',n.start))
 def handle_endtag(self,tag):
  for i in range(len(self.stack)-1,0,-1):
   if self.stack[i].tag==tag:
    end=self.s.find('>',self.source_offset())+1
    for n in self.stack[i:]: n.end=end
    self.stack=self.stack[:i];break
 def handle_data(self,data): self.stack[-1].children.append((data,self.source_offset()))
def decode(b,http=''):
 declared=re.search(br'charset\s*=\s*["\x27]?\s*([\w-]+)',b[:10000],re.I)
 names=[]
 if b.startswith(codecs.BOM_UTF8): names.append(('utf-8-sig','BOM'))
 if 'charset=' in http.lower(): names.append((http.lower().split('charset=')[1].split(';')[0].strip(' "'),'HTTP'))
 if declared: names.append((declared[1].decode('ascii'),'meta'))
 names += [('utf-8','tentativa estrita'),('cp1252','fallback Windows-1252')]
 errors=[]
 for enc,reason in names:
  try: return b.decode(enc),{'encoding':enc,'criterio':reason,'declaracao_meta':declared[1].decode('ascii') if declared else None,'tentativas_invalidas':errors}
  except (UnicodeError,LookupError) as e: errors.append(enc)
 return b.decode('latin1'),{'encoding':'latin1','criterio':'fallback sem substituicao','alerta':'codificacao incerta','tentativas_invalidas':errors}

def classes(n):return n.attrs.get('class','').split()
def lineage(n):
 out=[]
 while n:out.append(n);n=n.parent
 return out
def date_iso(s):
 m=re.search(r'\b(\d{1,2})[./](\d{1,2})[./](\d{4})\b',s)
 if m:return f'{m[3]}-{int(m[2]):02d}-{int(m[1]):02d}'
 m=re.search(r'\b(\d{1,2})[.º°o]*\s+de\s+(\w+)\s+de\s+(\d{4})',s,re.I)
 if m and m[2].lower() in MONTHS:return f'{m[3]}-{MONTHS[m[2].lower()]:02d}-{int(m[1]):02d}'
 return None

def source(path,provider,url):
 b=Path(path).read_bytes();html,encoding=decode(b);tree=Parser(html)
 body=next(tree.root.all('body'),tree.root)
 if provider=='camara':
  candidates=[n for n in tree.root.all('div') if 'textoNorma' in classes(n)]
  if not candidates:raise ValueError('Publicação original sem contêiner textoNorma; não usar navegação como norma')
  content=candidates[0]
 else:content=body
 css_struck=set(re.findall(r'\.([\w-]+)\s*\{[^}]*text-decoration\s*:[^}]*line-through',html,re.I))
 lines=[];runs=[]
 def flush():
  nonlocal runs
  if runs and clean(''.join(r['texto'] for r in runs)):
   text=''.join(r['texto'] for r in runs);ances=runs[0]['ancestrais'];offset=runs[0]['offset']
   lines.append({'id':len(lines),'texto':text,'comparacao':clean(text),'runs':runs,'offset':offset,'linha':html.count('\n',0,offset)+1,'profundidade_citacao':sum(a['tag'] in ('dir','blockquote') for a in ances),'marcacoes_riscadas':any(r['riscado'] for r in runs),'riscado_integral':all(r['riscado'] for r in runs if r['texto'].strip()),'referencias':[{'texto':r['texto'],'href':r['link']} for r in runs if r.get('link')]})
  runs=[]
 bounds={'p','div','blockquote','dir','td','th','tr','li','h1','h2','h3','h4','br','hr'}
 def walk(n):
  if n.tag in ('script','style','head'):return
  if n.tag in bounds:flush()
  for c in n.children:
   if isinstance(c,Node):walk(c)
   else:
    text,offset=c
    if n.tag=='br':continue
    ancestry=lineage(n)
    runs.append({'texto':text,'offset':offset,'riscado':any(a.tag in ('s','strike','del') or 'line-through' in a.attrs.get('style','').lower() or bool(set(classes(a))&css_struck) for a in ancestry),'link':next((a.attrs['href'] for a in ancestry if a.tag=='a' and 'href' in a.attrs),None),'ancestrais':[{'tag':a.tag,'attrs':a.attrs} for a in ancestry]})
  if n.tag in bounds:flush()
 walk(content);flush()
 # H1 da Câmara fica fora de textoNorma: identidade retirada do elemento real, nunca do slug.
 headings=[clean(n.text()) for n in tree.root.all('h1') if re.match(r'EMENDA CONSTITUCIONAL',clean(n.text()),re.I)]
 ident=next((l['comparacao'] for l in lines if re.match(r'^EMENDA CONSTITUCIONAL',l['comparacao'],re.I)),headings[0] if headings else '')
 m=re.search(r'EMENDA\s+CONSTITUCIONAL\s+N[.º°o\s]*\s*(\d+)',ident,re.I)
 # Datas de cabeçalho e fecho são registradas separadamente.
 closing=next((l['comparacao'] for l in lines if re.match(r'^Brasília\b',l['comparacao'],re.I)),None)
 first=next((i for i,l in enumerate(lines) if ART.match(l['comparacao'])),None)
 last=next((i for i,l in enumerate(lines) if first is not None and i>first and re.match(r'^Brasília\b',l['comparacao'],re.I)),None)
 norm=lines[first:last] if first is not None else []
 plain=Parser(re.sub(r'<(?:script|style)\b[^>]*>[\s\S]*?</(?:script|style)\s*>','',html,flags=re.I));entire=clean(plain.root.text())
 pub_matches=re.findall(r'(?:publicado|publiacado|publicação)[^\n]{0,200}?D\.?\s*O\.?\s*U\.?[^\n]{0,80}',entire,re.I)
 # A referência é capturada até sua primeira data, preservando também o texto completo encontrado.
 publication=[]
 for pm in pub_matches:
  d=date_iso(pm)
  if d and d not in [x['data'] for x in publication]:publication.append({'data':d,'texto':pm})
 if provider=='camara':
  for m2 in re.finditer(r'Diário Oficial da União\s*[-–]\s*Seção\s*1\s*(?:[-–]|de)\s*(\d{1,2}/\d{1,2}/\d{4})([^\n]{0,130})',entire,re.I):
   d=date_iso(m2[1]);publication.append({'data':d,'texto':m2[0]})
 preamble=next((l['comparacao'] for l in lines if re.search(r'\b(?:As Mesas|A Mesa)\b',l['comparacao'],re.I)),None)
 if provider=='camara':
  ems=[clean(n.text()) for n in content.all('p') if 'ementa' in classes(n) and clean(n.text())]
  if not ems:
   for match in re.finditer(r'<p\b[^>]*class=[\"\']ementa[\"\'][^>]*>(.*?)</p>',html,re.I|re.S):
    candidate=clean(Parser(match[1]).root.text())
    if candidate:ems.append(candidate)
 else:
  cutoff=next((i for i,l in enumerate(lines) if l['comparacao']==preamble),first or 0)
  ems=[l['comparacao'] for l in lines[:cutoff] if re.match(r'^(Altera|Acrescenta|Dá nova|Institui|Modifica|Dispõe|Estabelece|Prorroga|Autoriza|Desvincula|Revoga|Impõe|Define|Fixa|Inclui|Cria)\b',l['comparacao'],re.I)]
 classify(norm,Path(path))
 correct_classification(norm,Path(path))
 signatures=[]
 if last is not None:
  for line in lines[last:]:
   if re.match(r'^Este texto',line['comparacao'],re.I) or line['comparacao']=='*':break
   signatures.append(line)
 return {'provedor':provider,'url':url,'arquivo':str(Path(path).resolve()).replace('\\','/'),'sha256':hashlib.sha256(b).hexdigest(),'codificacao':encoding,'identidade':{'numero':int(m[1]) if m else None,'cabecalho':ident,'data_cabecalho':date_iso(ident),'data_fecho':date_iso(closing or ''),'fecho':closing,'ementas':ems,'publicacoes':publication},'preambulo':preamble,'assinaturas_e_fecho':signatures,'linhas':lines,'norma':norm,'artigos_proprios':[l['artigo'] for l in norm if l['classe']=='artigo_proprio' and not l['riscado_integral']],'texto_normativo_comparacao':clean(' '.join(l['texto'] for l in norm)),'delimitacao':{'primeiro_artigo_encontrado':first is not None,'fecho_encontrado':last is not None},'editorial':[l for l in lines if l['marcacoes_riscadas'] or re.search(r'\b(?:Redação dada|Incluído pela|Revogado pela|Vide|Vigência)\b',l['comparacao'],re.I)]}

def classify(lines,path=None):
 fixes=set()
 if path is not None and (ROOT/'ajustes-estruturais.json').exists():
  for fix in load(ROOT/'ajustes-estruturais.json'):
   if fix['arquivo']==str(path.relative_to(BASE)).replace('\\','/') and fix['sha256']==sha(path):fixes.add(fix['offset'])
 current=None;quoted=False;baseline=None;sub=[];last_own=0
 for l in lines:
  t=l['comparacao'];m=ART.match(t);depth=l['profundidade_citacao'];l['artigo']=None;l['fundamento']=[]
  if re.match(r'^\(?\s*(Vide|Redação dada|Incluído pela|Revogado pela|Vigência)\b',t,re.I):l['classe']='nota_editorial'
  elif m:
   label='único' if m['unique'] else m['num']+(m['suffix'] or '')
   is_citation=bool(m['quote'] or (baseline is not None and depth>baseline) or (not m['unique'] and int(m['num'])>last_own+1))
   if l['offset'] in fixes:is_citation=False
   if baseline is None and not is_citation:baseline=depth
   if not is_citation:
    l['classe']='artigo_proprio';current=label;quoted=False;sub=[];last_own=int(m['num']) if m['num'] else last_own;l['fundamento']=['marcador no início de unidade HTML','sem abertura de citação','fora de contêiner recuado relativo aos artigos próprios']
   else:
    l['classe']='artigo_citado';quoted=True;sub=[];l['fundamento']=['aspas, sufixo de dispositivo ou contêiner recuado; não é artigo próprio']
   l['artigo']=label
  elif t.startswith(('"','“','«')):l['classe']='dispositivo_citado';quoted=True
  elif quoted or (baseline is not None and depth>baseline):l['classe']='dispositivo_citado'
  else:l['classe']='continuacao_artigo_proprio'
  l['artigo_proprio_contexto']=current
  unit=re.match(r'^(§\s*\d+[º°o.]*(?:-[A-Z])?|Parágrafo\s+[úu]nico\.?|[IVXLCDM]+\s*[-–—]|[a-z]\))',t)
  l['unidade_marcador']=unit[0] if unit else None
  l['citacao_malformada']=False
  if re.search(r'\(NR\)\s*[.;]?\s*$',t,re.I):
   if quoted and not re.search(r'["”»]\s*\(NR\)',t):l['citacao_malformada']=True
   quoted=False
  elif re.search(r'["”»]\s*[.;]?\s*$',t):quoted=False

def correct_classification(lines,path):
 config=ROOT/'ajustes-estruturais.json'
 if not config.exists():return
 relative=str(path.relative_to(BASE)).replace('\\','/')
 for fix in load(config):
  if fix['arquivo']!=relative:continue
  if sha(path)!=fix['sha256']:raise ValueError('Ajuste estrutural não se aplica a hash diferente')
  found=[l for l in lines if l['offset']==fix['offset'] and l['comparacao']==fix['texto_esperado']]
  if len(found)!=1:raise ValueError('Ajuste estrutural sem correspondência única')
  line=found[0];line['classe']=fix['classe_corrigida'];line['fundamento'].append(fix['justificativa']);line['evidencia_classificacao']=fix['evidencia_complementar']
 current=None
 for line in lines:
  if line['classe']=='artigo_proprio':current=line['artigo']
  line['artigo_proprio_contexto']=current
