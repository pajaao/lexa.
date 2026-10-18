// Audit only: deliberately independent of grammar.mjs, norms.mjs and eligibility.mjs.
import {createHash} from 'node:crypto';
export const hash=x=>createHash('sha256').update(x).digest('hex');
export const plain=p=>p.runs.map(r=>r.text).join('');
export const emptyReview=()=>({decision:'',justification:'',evidenceConsulted:'',needsAdjudication:''});
const number=x=>x.replace(/[.\sº°o]/gu,'').toUpperCase();
export function literalNumbers(text){
 const body=text.replace(/^(?:arts?\.|artigos?)\s*/iu,'');
 const tokens=body.split(/\s*,\s*(?:e\s+)?|\s+e\s+/iu);
 return tokens.length&&tokens.every(t=>/^\d+(?:\.\d{3})*(?:[º°o])?(?:-[A-Z]{1,2})*$/iu.test(t))?tokens.map(number):null;
}
export function identity(text){
 const m=text.match(/\b(Decreto[- ]Lei|Lei(?:\s+Complementar)?)\s+n\s*[º°o.]*\s*([\d.]+)([\s\S]*)/iu);
 if(!m)return null;
 const y=m[3].match(/^(?:\s*\/\s*|\s*,?\s*de\s+(?:\d{1,2}(?:\s*[º°o])?\s+de\s+[^,\d]+?\s+de\s+)?)(\d{4})\b/iu);
 return y?[m[1].toLowerCase().replace(/\s+/g,'-'),m[2].replaceAll('.',''),y[1]].join(':'):null;
}
export function spanCheck(span,paragraph){
 const text=plain(paragraph),ok=span&&Number.isInteger(span.start)&&Number.isInteger(span.end)&&span.start>=0&&span.end>span.start&&span.end<=text.length&&text.slice(span.start,span.end)===span.text;
 let cursor=0;const runs=[];
 for(const [i,r] of paragraph.runs.entries()){const end=cursor+r.text.length;if(span&&cursor<span.end&&end>span.start)runs.push({run:i,start:cursor,end,deleted:!!r.deleted,overlap:text.slice(Math.max(cursor,span.start),Math.min(end,span.end))});cursor=end;}
 return {ok:!!ok,deleted:runs.some(r=>r.deleted&&r.overlap.trim()),runs};
}
const reproduction=/(?:passa(?:m)?\s+a\s+vigorar|seguinte\s+reda[çc][aã]o|d[êe]-se\s+[^\n]{0,100}reda[çc][aã]o|fica[m]?\s+[^\n]{0,80}redigid|trecho\s+reproduzido|acrescenta-se|ficam?\s+acrescid)/iu;
export function inspectOccurrence(corpus,o,syntaxClass,target){
 const errors=[],suspicions=[],unknown=[],checks={};
 const entry=corpus.collections.find(c=>c.code.id===o.source.codeId),dest=corpus.collections.find(c=>c.code.id===target.codeId);
 const a=entry?.code.articles.find(a=>a.id===o.source.articleId),b=dest?.code.articles.find(a=>a.id===target.articleId),p=a?.paragraphs[o.location.paragraph];
 checks.sourceHash=!!entry&&hash(JSON.stringify(entry.code))===entry.sha256&&entry.sha256===o.source.editionSha256;
 checks.destinationHash=!!dest&&hash(JSON.stringify(dest.code))===dest.sha256&&dest.sha256===target.editionSha256;
 checks.individualTarget=!!b&&!b.rangeEnd;
 checks.destinationHasRevocationNotice=!!b&&/\(\s*(?:Revogad[oa]|Vetad[oa])/iu.test(plain(b.paragraphs[0]));
 if(checks.destinationHasRevocationNotice)suspicions.push('Cabeçalho do destino contém nota expressa de revogação/veto; conferir referência histórica, sem inferir vigência.');
 checks.scope=!!a&&!!b&&o.source.scope===(a.scope||'main')&&target.scope===(b.scope||'main')&&(target.articleId.startsWith('adct-')===(target.scope==='adct'));
 if(!p){errors.push('Parágrafo de origem ausente.');return {status:'Erro confirmado',checks,errors,suspicions,unknown};}
 const core=spanCheck(o.location,p),qualifiers=o.qualifiers.map(s=>spanCheck(s,p)),norm=o.normEvidence?spanCheck(o.normEvidence,p):null;
 checks.provenance=o.location.field==='paragraphs'&&o.location.offsetUnit==='utf16'&&core.ok&&qualifiers.every(s=>s.ok)&&(!norm||norm.ok);
 checks.liveEvidence=!core.deleted&&qualifiers.every(s=>!s.deleted)&&(!norm||!norm.deleted);
 checks.recordedHistoricalClear=Object.values(o.historical).every(v=>v==='clear');
 const nums=literalNumbers(o.location.text),wanted=target.articleId.replace(/^adct-/u,'');
 checks.articleLiteral=!!nums&&nums.includes(wanted)&&number(b?.number||'')===wanted;
 const articleText=a.paragraphs.map(plain).join('\n');
 checks.noReproductionMarker=!reproduction.test(articleText);
 if(!checks.noReproductionMarker)suspicions.push('Marcador ampliado de reprodução/alteração no artigo; atribuição exige conferência.');
 const prefix=plain(p).slice(0,o.location.start),contextRuns=spanCheck({start:0,end:o.location.start,text:prefix},p);
 checks.noDeletedPrefix=!contextRuns.deleted;
 if(contextRuns.deleted)suspicions.push('Há texto riscado antes da ocorrência no parágrafo; relevância contextual não decidida automaticamente.');
 const evidence=o.normEvidence?.text||'';
 let expectedCode=null,expectedScope='main',classOK=false;
 if(syntaxClass==='numbered-law-article-list'){
  const key=identity(evidence),matches=corpus.collections.filter(c=>key&&identity(c.code.law)===key);
  classOK=!!key&&o.normEvidence.start===o.location.end&&o.qualifiers.length<=1&&o.qualifiers.every(q=>/^§\s*\d+[º°o]?\s+do\s*$/iu.test(q.text)&&q.end===o.location.start);
  if(matches.length===1)expectedCode=matches[0].code.id;else unknown.push('Identidade numerada não pôde ser confrontada univocamente pelo auditor.');
 }else if(syntaxClass==='adct-self-article'){
  classOK=/^\s*,?\s*deste\s+Ato(?:\s+das\s+Disposições\s+Constitucionais\s+Transitórias)?\s*$/iu.test(evidence)&&o.qualifiers.length===0&&o.normEvidence.start===o.location.end;
  expectedCode='cf';expectedScope='adct';
  if(o.source.codeId!=='cf'||o.source.scope!=='adct')errors.push('Autorreferência a Ato fora do ADCT.');
 }else if(syntaxClass==='self-qualified-article-list'){
  classOK=/^\s*,?\s*desta\s+Lei\s*$|^\s*,?\s*deste\s+Código\s*$|^\s*,?\s*desta\s+Consolidação\s*$/iu.test(evidence)&&o.qualifiers.length===0&&o.normEvidence.start===o.location.end;
  expectedCode=o.source.codeId;expectedScope=o.source.scope;
  classOK=classOK&&o.source.codeId!=='cf'&&(/Código/iu.test(evidence)?entry.code.name.startsWith('Código'):/Consolidação/iu.test(evidence)?o.source.codeId==='clt':/^Lei /u.test(entry.code.law));
  // Warning only: no automatic interpretation of the antecedent of "desta".
  const priorLaw=identity(prefix);
  if(priorLaw&&priorLaw!==identity(entry.code.law))suspicions.push('Identidade normativa diferente anterior à expressão autorreferente no mesmo parágrafo.');
 }else if(syntaxClass==='parenthetical-article-list'){
  classOK=plain(p)[o.location.start-1]==='('&&plain(p)[o.location.end]===')'&&!o.normEvidence&&o.qualifiers.length===0;
  expectedCode=o.source.codeId;expectedScope=o.source.scope;
  unknown.push('Norma não nomeada na expressão parentética: destino local depende da convenção de contexto, a confirmar por revisor.');
 }else errors.push('Classe não reconhecida nesta auditoria.');
 checks.authorizedSyntax=classOK&&!!nums;
 checks.normIdentity=!!expectedCode&&expectedCode===target.codeId&&expectedScope===target.scope;
 for(const k of ['sourceHash','destinationHash','individualTarget','scope','provenance','liveEvidence','recordedHistoricalClear','articleLiteral','authorizedSyntax'])if(!checks[k])errors.push('Falha documental verificável: '+k);
 if(expectedCode&&!checks.normIdentity)errors.push('Identidade/escopo literal não coincide com o destino registrado.');
 const status=errors.length?'Erro confirmado':suspicions.length?'Suspeita':unknown.length?'Inconclusiva':'Consistente na verificação automatizada';
 return {status,checks,errors,suspicions,unknown,runEvidence:{core,qualifiers,norm,prefix:contextRuns},objectiveReason:syntaxClass==='numbered-law-article-list'?'Identidade numérica/ano literal conferida no catálogo e número do artigo conferido no destino.':syntaxClass==='parenthetical-article-list'?'Expressão parentética numerada com destino local da política; identidade contextual permanece pendente.':'Autorreferência literal compatível com a norma e o escopo de origem; número conferido no destino.'};
}
export function sampleRejected(rows,{perStratum=2,seed='lexa-1a2-rejeicoes-v1'}={}){
 const strata=new Map();
 for(const r of rows){const key=[r.source.codeId,r.source.scope,r.classification,r.exclusionReason,r.diagnosticReason,r.facets.historical,r.facets.ambiguity,r.facets.reproduction,r.facets.unauthorizedSyntax].join('|');if(!strata.has(key))strata.set(key,[]);strata.get(key).push(r);}
 const selected=[];
 for(const [stratum,members] of [...strata].sort(([a],[b])=>a.localeCompare(b,'en'))){
  const ordered=members.map(r=>({r,rank:hash(seed+'\0'+r.id)})).sort((a,b)=>a.rank<b.rank?-1:a.rank>b.rank?1:0);
  for(const {r,rank} of ordered.slice(0,perStratum))selected.push({...r,sampling:{stratum,population:members.length,selected:Math.min(perStratum,members.length),rank,seed}});
 }
 return {seed,perStratum,strata:strata.size,population:rows.length,records:selected};
}
export function csv(rows,columns){const q=x=>'"'+String(x??'').replaceAll('"','""')+'"';return '\ufeff'+[columns.map(q).join(','),...rows.map(r=>columns.map(k=>q(typeof r[k]==='object'?JSON.stringify(r[k]):r[k])).join(','))].join('\r\n')+'\r\n';}
