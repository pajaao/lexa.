// Investigation only: no import from src/, build.mjs, reader or service worker.
import {createHash} from 'node:crypto';
import {readFileSync} from 'node:fs';
import {lexArticles,implicitExpressions} from './grammar.mjs';
import {normCatalog,attachedNorm,precedingNorm} from './norms.mjs';
import {reproductionContext} from './context.mjs';
export const RULES_VERSION='0.5.2';
export const sha256=value=>createHash('sha256').update(value).digest('hex');
export const RULES_SHA256=sha256(['grammar.mjs','norms.mjs','extract.mjs','graph.mjs','context.mjs'].map(name=>name+'\0'+readFileSync(new URL(name,import.meta.url),'utf8')).join('\0'));
const raw=p=>p.runs.map(r=>r.text).join('');
function inventoryFor(corpus){
 const inventory=new Map();
 for(const {code,sha256:declared} of corpus.collections){
  if(code.id==='sv')continue;
  if(inventory.has(code.id))throw Error('Duplicate norm identity: '+code.id);
  const digest=sha256(JSON.stringify(code));if(declared&&declared!==digest)throw Error('Edition checksum mismatch: '+code.id);
  const articles=new Map();
  for(const a of code.articles){if(articles.has(a.id))throw Error('Duplicate article identity: '+code.id+'/'+a.id);articles.set(a.id,a);}
  inventory.set(code.id,{code,sha256:digest,articles});
 }
 return inventory;
}
function maskFor(p){let offset=0;const mask=new Uint8Array(raw(p).length);for(const run of p.runs){if(run.deleted)mask.fill(1,offset,offset+run.text.length);offset+=run.text.length;}return mask;}
function condition(text,mask,spans){
 let live=0,deleted=0;
 for(const {start,end} of spans)for(let i=start;i<end;i++){if(/\s/u.test(text[i]))continue;if(mask[i])deleted++;else live++;}
 return deleted?(live?'mixed':'deleted'):'clear';
}
function plainSpan(text,span){return {start:span.start,end:span.end,text:text.slice(span.start,span.end)};}
function sentenceStart(text,start){
 // A full stop inside "art." or a thousands number is not a clause boundary.
 for(let i=start-1;i>=0;i--)if(text[i]===';'||text[i]==='\n'||text[i]==='.'&&/[.!?]\s+[A-ZÀ-Ý]/u.test(text.slice(i,i+4)))return i+1;
 return 0;
}
function expandMembers(expression){
 const numbers=expression.members.map(m=>m.number);
 for(const range of expression.ranges){
  if(!/^\d+$/u.test(range.from)||!/^\d+$/u.test(range.to))return {reason:'alphanumeric-range-not-supported'};
  const start=Number(range.from),end=Number(range.to);
  if(!Number.isSafeInteger(start)||!Number.isSafeInteger(end)||end<=start||end-start>500)return {reason:'range-order-or-budget-not-supported'};
  for(let n=start+1;n<end;n++)numbers.push(String(n));
 }
 return {numbers:[...new Set(numbers)].sort((a,b)=>{const na=Number(a),nb=Number(b);return Number.isFinite(na)&&Number.isFinite(nb)?na-nb:a<b?-1:a>b?1:0;})};
}
function normFor(text,expression,source,catalog,previous){
 const candidate=attachedNorm(text,expression.end,source,catalog,{allowSuas:previous?.norm?.codeId==='cf'&&previous.norm.scope==='main'});
 if(candidate){
  if(/^\s*(?:e|ou)\s+d[ao]\s+(?:Lei|C[oó]digo|Constitui[çc][aã]o)\b/iu.test(text.slice(candidate.end)))return {...candidate,status:'unresolved',reason:'multiple-norm-qualifiers-not-supported'};
  return candidate;
 }
 if(/^\s*[-–]\s*\p{L}/u.test(text.slice(expression.end)))return {status:'unresolved',reason:'unrecognized-post-reference-suffix'};
 const preceding=precedingNorm(text,expression.start,source,catalog);if(preceding)return preceding;
 const priorText=text.slice(sentenceStart(text,expression.start),expression.start);
 if(/\b(?:Lei(?:s|\s+Complementar)?\s+n|C[oó]digo\s+(?:Civil|Penal|de\s+Processo)|Constitui[çc][aã]o)\b/iu.test(priorText))return {status:'unresolved',reason:'unattached-prior-norm-context'};
 if(source.scope==='adct')return {status:'unresolved',reason:'adct-scope-not-explicit'};
 return {status:'resolved',codeId:source.codeId,scope:source.scope,reason:'unqualified-local',inferredDefault:true};
}
function resolveTargets(expression,norm,inventory){
 if(expression.implicit)return {status:'unresolved',reason:'implicit-or-relative-article-not-supported',targets:[]};
 if(norm.status!=='resolved')return {status:norm.status,reason:norm.reason,targets:[]};
 const expanded=expandMembers(expression);if(expanded.reason)return {status:'unresolved',reason:expanded.reason,targets:[]};
 const targets=[];
 for(const number of expanded.numbers){
  const articleId=(norm.scope==='adct'?'adct-':'')+number;
  const entry=inventory.get(norm.codeId),article=entry?.articles.get(articleId);
  if(!article)return {status:'unresolved',reason:'target-not-individually-present',targets:[]};
  if(article.rangeEnd)return {status:'unresolved',reason:'grouped-target-not-supported',targets:[]};
  targets.push({codeId:norm.codeId,articleId,scope:article.scope,editionSha256:entry.sha256,resolutionLevel:'article'});
 }
 return {status:'resolved',reason:norm.reason,targets};
}
export function extractRemissions(corpus,{selected,rulesVersion=RULES_VERSION}={}){
 const inventory=inventoryFor(corpus),catalog=normCatalog(corpus),occurrences=[],diagnostics={ownHeadings:0,scannedArticles:0,scannedParagraphs:0};
 const editions=Object.fromEntries([...inventory].sort(([a],[b])=>a<b?-1:1).map(([id,v])=>[id,v.sha256]));
 const editionSetSha256=sha256(JSON.stringify({editions,rulesVersion,rulesSha256:RULES_SHA256,catalog:corpus.collections.filter(c=>c.code.id!=='sv').map(c=>[c.code.id,c.code.name,c.code.law]).sort()}));
 for(const [codeId,entry] of inventory){
  if(selected&&!selected.includes(codeId))continue;
  for(const article of entry.code.articles){
   diagnostics.scannedArticles++;
   const source={codeId,articleId:article.id,scope:article.scope||'main',editionSha256:entry.sha256},amendment=reproductionContext(article);
   for(const [paragraph,p] of article.paragraphs.entries()){
    diagnostics.scannedParagraphs++;
    const text=raw(p),mask=maskFor(p),expressions=lexArticles(text),prepared=[];
    for(const e of expressions){
     if(!text.slice(0,e.start).trim()&&e.members[0].number===article.number.toUpperCase()){diagnostics.ownHeadings++;continue;}
     const prev=prepared.at(-1),norm=normFor(text,e,source,catalog,prev);
     const reproduced=/^[\s“"‘'\d)\-]*$/u.test(text.slice(0,e.start))&&/^\s*[.\u2026]{3,}/u.test(text.slice(e.end));
     const blocked=amendment&&!reproduced;
     if(blocked){norm.status='unresolved';norm.reason='embedded-amendment-scope-not-supported';}
     prepared.push({e,norm,reproduced});
    }
    // Do not guess a shared normative identity across coordinated citations.
    // The following explicit qualifier is evidence against a local default,
    // not permission to propagate a destination through unsupported grammar.
    for(let i=prepared.length-2;i>=0;i--){
     const current=prepared[i],next=prepared[i+1];if(!current.norm.inferredDefault)continue;
     let bridge=text.slice(current.e.end,next.e.start);
     for(const q of next.e.qualifiers)if(q.start>=current.e.end&&q.end===next.e.start)bridge=text.slice(current.e.end,q.start);
     const coordinated=/^\s*,?\s*(?:(?:e|ou)\s+)?(?:(?:no|na|nos|nas|do|da)\s*)?$/iu.test(bridge);
     const uncertain=next.norm.reason==='coordinated-norm-scope-not-supported'||next.norm.start!==undefined&&(next.norm.status!=='resolved'||next.norm.codeId!==source.codeId||next.norm.scope!==source.scope);
     if(coordinated&&uncertain)current.norm={...current.norm,status:'unresolved',reason:'coordinated-norm-scope-not-supported'};
    }
    // "ambos deste Ato" qualifies exactly the current and immediately prior
    // citation in this paragraph; never propagate over an explicitly other norm.
    for(let i=0;i<prepared.length;i++){
     const current=prepared[i];if(!current.norm.shared)continue;
     const prior=prepared[i-1];
     if(!prior||text.slice(prior.e.end,current.e.start).includes(';')){current.norm={...current.norm,status:'unresolved',reason:'shared-qualifier-without-pair'};continue;}
     if(prior.norm.start!==undefined&&(prior.norm.codeId!==current.norm.codeId||prior.norm.scope!==current.norm.scope)){
      prior.norm={...prior.norm,status:'unresolved',reason:'conflicting-shared-qualifier'};current.norm={...current.norm,status:'unresolved',reason:'conflicting-shared-qualifier'};continue;
     }
     prior.norm={...current.norm,reason:'explicit-shared-pair'};
    }
    const covered=prepared.flatMap(v=>[v.e,...v.e.qualifiers,...(v.norm.start===undefined?[]:[v.norm])]);
    for(const e of implicitExpressions(text,covered))prepared.push({e,norm:{status:'unresolved',reason:'implicit-or-relative-article-not-supported'}});
    prepared.sort((a,b)=>a.e.start-b.e.start);
    for(const {e,norm,reproduced} of prepared){
     const resolution=reproduced?{status:'rejected',reason:'reproduced-heading',targets:[]}:resolveTargets(e,norm,inventory);
     const location={field:'paragraphs',paragraph,offsetUnit:'utf16',...plainSpan(text,e)};
     const normEvidence=norm.start===undefined?null:plainSpan(text,norm);
     const qualifiers=e.qualifiers.map(q=>({...plainSpan(text,q),kind:q.kind,...(q.articleNumber?{articleNumber:q.articleNumber}:{})}));
     const core=condition(text,mask,[e]),qualifier=condition(text,mask,[...e.qualifiers,...(normEvidence?[normEvidence]:[])]);
     const beforeStart=sentenceStart(text,e.start),contextText=text.slice(beforeStart,e.start);
     const context=!e.implicit&&contextText.trim()?condition(text,mask,[{start:beforeStart,end:e.start}]):'clear';
     const historical={core,qualifiers:qualifier,context,state:core==='deleted'?'deleted':core==='mixed'||qualifier!=='clear'||context!=='clear'?'mixed':'clear'};
     let classification=resolution.status==='rejected'?'E':core==='deleted'?'D':historical.state!=='clear'?'C':resolution.status==='resolved'?'A':resolution.status==='external'?'B':'C';
     const reason=classification==='C'&&historical.state!=='clear'?'historical-required-evidence':resolution.reason;
     const id=sha256(JSON.stringify([editionSetSha256,source,paragraph,e.start,e.end]));
     occurrences.push({id,source,location,qualifiers,normEvidence,norm:{status:norm.status,codeId:norm.codeId??null,scope:norm.scope??null,identity:norm.law??null},kind:e.implicit?'implicit':/\((?:Vide|Ver)\s*[^)]*$/iu.test(text.slice(0,e.start))?'editorial-explicit':norm.codeId&&norm.codeId!==codeId?'cross-norm-explicit':'internal-explicit',classification,resolution,historical,reason});
    }
   }
  }
 }
 return {schema:1,rules:{version:rulesVersion,sha256:RULES_SHA256},editionSetSha256,editions,occurrences,diagnostics};
}
