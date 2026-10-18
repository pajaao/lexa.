// Independent eligibility gate. A is necessary, never sufficient. No article-number allowlist.
import {readFileSync} from 'node:fs';
import {sha256} from './extract.mjs';
import {lexArticles} from './grammar.mjs';
import {lawIdentity,lawKey,attachedNorm,normCatalog} from './norms.mjs';
import {reproductionContext} from './context.mjs';
export const POLICY_VERSION='1a.1';
export const POLICY_CLASSES=Object.freeze(['parenthetical-article-list','self-qualified-article-list','adct-self-article','numbered-law-article-list']);
export const POLICY=Object.freeze({version:POLICY_VERSION,sha256:sha256(readFileSync(new URL('eligibility.mjs',import.meta.url))),mode:'experimental-only',independentReview:'pending',classes:POLICY_CLASSES});
const NUM=String.raw`\d+(?:\.\d{3})*(?:[º°o])?(?:-[A-Z]{1,2})*`;
const CORE=new RegExp(String.raw`^(?:arts?\.\s*|artigos?\s+)${NUM}(?:\s*(?:,\s*(?:e\s+)?|e\s+)${NUM})*$`,'iu');
const SELF=/^\s*,?\s*dest[ea]\s+(?:Lei|Código|Consolidação)\s*$/iu;
const ADCT_SELF=/^\s*,?\s*deste\s+Ato(?:\s+das\s+Disposições\s+Constitucionais\s+Transitórias)?\s*$/iu;
function reject(reason){return {eligible:false,reason};}
function safeSpan(span,text,runs){
 if(!span||!Number.isSafeInteger(span.start)||!Number.isSafeInteger(span.end)||span.start<0||span.end<=span.start||span.end>text.length||text.slice(span.start,span.end)!==span.text)return false;
 let offset=0;
 for(const run of runs){const end=offset+run.text.length;if(run.deleted&&span.start<end&&span.end>offset&&text.slice(Math.max(offset,span.start),Math.min(end,span.end)).trim())return false;offset=end;}
 return true;
}
export function applyEligibility(corpus,extraction,{policy=POLICY}={}){
 const inventory=new Map(corpus.collections.filter(c=>c.code.id!=='sv').map(c=>[c.code.id,{...c,articles:new Map(c.code.articles.map(a=>[a.id,a]))}]));
 const decisions=[],accepted=[],rejections={},catalog=normCatalog(corpus);
 for(const o of extraction.occurrences){
  let verdict;
  const source=inventory.get(o.source.codeId),a=source?.articles.get(o.source.articleId),p=a?.paragraphs[o.location.paragraph],text=p?.runs.map(r=>r.text).join('')||'';
  const spans=[o.location,...o.qualifiers,...(o.normEvidence?[o.normEvidence]:[])];
  if(o.classification!=='A')verdict=reject('classification-'+o.classification);
  else if(o.resolution.status!=='resolved'||!o.resolution.targets.length)verdict=reject('resolution-not-confirmed');
  else if(o.historical.state!=='clear'||Object.values(o.historical).some(v=>v!=='clear'))verdict=reject('historical-evidence');
  else if(o.location.field!=='paragraphs'||o.location.offsetUnit!=='utf16'||!source||source.sha256!==o.source.editionSha256||!p||!spans.every(s=>safeSpan(s,text,p.runs)))verdict=reject('invalid-or-deleted-provenance');
  else if(o.resolution.targets.some(t=>{const entry=inventory.get(t.codeId),dest=entry?.articles.get(t.articleId);return !dest||dest.rangeEnd||entry.sha256!==t.editionSha256||dest.scope!==t.scope;}))verdict=reject('missing-grouped-or-stale-target');
  else if(reproductionContext(a))verdict=reject('amendment-reproduction-context');
  else if(!['internal-explicit','cross-norm-explicit'].includes(o.kind)||/\b(?:Vide|Ver)\s*$/iu.test(text.slice(0,o.location.start)))verdict=reject('editorial-or-implicit-not-authorized');
  else if(!CORE.test(o.location.text)||o.resolution.targets.length>8)verdict=reject('list-range-or-complex-syntax-not-authorized');
  else {
   let syntax=null;
   const norm=o.normEvidence,reason=o.resolution.reason;
   const attached=attachedNorm(text,o.location.end,o.source,catalog);
   const identitySafe=!norm||attached&&attached.status==='resolved'&&attached.start===norm.start&&attached.end===norm.end&&attached.codeId===o.norm.codeId&&attached.scope===o.norm.scope;
   if(o.qualifiers.length===0&&reason==='unqualified-local'&&text[o.location.start-1]==='('&&text[o.location.end]===')')syntax='parenthetical-article-list';
   else if(o.qualifiers.length===0&&reason==='explicit-self'&&norm?.start===o.location.end&&SELF.test(norm.text)&&o.source.codeId!=='cf'&&(/Código/iu.test(norm.text)?source.code.name.startsWith('Código'):/Consolidação/iu.test(norm.text)?o.source.codeId==='clt':/^Lei /u.test(source.code.law)))syntax='self-qualified-article-list';
   else if(o.qualifiers.length===0&&reason==='explicit-adct'&&o.source.codeId==='cf'&&o.source.scope==='adct'&&norm?.start===o.location.end&&ADCT_SELF.test(norm.text)&&o.resolution.targets.length===1)syntax='adct-self-article';
   else if(reason==='explicit-law'&&norm?.start===o.location.end&&o.norm.identity&&o.qualifiers.length<=1&&o.qualifiers.every(q=>q.kind==='paragraph'&&q.end===o.location.start&&/^§\s*\d+[º°o]?\s+do\s*$/iu.test(q.text)))syntax='numbered-law-article-list';
   if(syntax==='parenthetical-article-list'){
    const prior=a.paragraphs.slice(0,o.location.paragraph).map(p=>p.runs.map(r=>r.text).join('')).join('\n')+'\n'+text.slice(0,o.location.start);
    const after=text.slice(o.location.end+1);
    if(/\b(?:Lei(?:\s+Complementar)?\s+n|Código\s+(?:Civil|Penal|de\s+Processo)|Constituição)\b/iu.test(prior)||/^\s*,?\s*d[ao]\s+(?:Lei|Código|Constituição)\b/iu.test(after))syntax=null;
   }
   if(!identitySafe)verdict=reject('norm-identity-not-verified');
   else if(!syntax||!policy.classes.includes(syntax))verdict=reject('syntax-class-not-authorized');
   else {
    const members=lexArticles(o.location.text)[0]?.members.map(m=>m.number)||[];
    let code=o.source.codeId,scope=o.source.scope;
    if(syntax==='numbered-law-article-list'){
     const matches=[...inventory].filter(([,v])=>lawKey(lawIdentity(v.code.law))===lawKey(o.norm.identity));
     code=matches.length===1?matches[0][0]:null;scope='main';
    }else if(syntax.startsWith('adct-')){code='cf';scope='adct';}
    const expected=[...new Set(members.map(n=>code+'/'+(scope==='adct'?'adct-':'')+n))].sort();
    const targets=[...new Set(o.resolution.targets.map(t=>t.codeId+'/'+t.articleId))].sort();
    verdict=code&&JSON.stringify(expected)===JSON.stringify(targets)?{eligible:true,syntaxClass:syntax}:reject('target-not-justified-by-authorized-syntax');
   }
  }
  decisions.push({occurrenceId:o.id,...verdict});
  if(verdict.eligible)accepted.push({...o,syntaxClass:verdict.syntaxClass});else rejections[verdict.reason]=(rejections[verdict.reason]||0)+1;
 }
 return {policy,accepted,decisions,rejections};
}
