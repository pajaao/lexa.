// Norm identity is lexical and catalog-based. Never select by nearest law in prose.
export const normalize=value=>value.normalize('NFD').replace(/\p{M}/gu,'').toLowerCase().replace(/\s+/g,' ').trim();
const LAW=String.raw`(decreto[-\s]lei|lei(?:\s+complementar)?)\s+n\s*[.º°o]*\s*([\d.]+)\s*(?:\/\s*(\d{4})|,?\s*de\s+(?:\d{1,2}(?:\s*[º°o])?\s+de\s+\p{L}+\s+de\s+)?(\d{4}))`;
const lawAt=new RegExp('^'+LAW,'iu'),lawAnywhere=new RegExp(LAW,'iu');
export function lawIdentity(value){
 const m=value.match(lawAnywhere);return m?{kind:normalize(m[1]).replace('decreto lei','decreto-lei'),number:m[2].replace(/\./g,''),year:m[3]||m[4],raw:m[0]}:null;
}
export const lawKey=law=>law?[law.kind,law.number,law.year].join(':'):null;
export function normCatalog(corpus){
 const byLaw=new Map(),byName=[];
 for(const {code} of corpus.collections){
  if(code.id==='sv')continue;
  const law=lawIdentity(code.law);if(law)byLaw.set(lawKey(law),code.id);
  byName.push([normalize(code.name),code.id]);
 }
 byName.push(['codigo civil','civil'],['codigo penal','penal'],['codigo de processo civil','cpc'],['codigo de processo penal','cpp'],['codigo de defesa do consumidor','cdc'],['codigo tributario nacional','ctn'],['consolidacao das leis do trabalho','clt']);
 return {byLaw,byName:byName.sort((a,b)=>b[0].length-a[0].length)};
}
export function attachedNorm(text,start,source,catalog,{allowSuas=false}={}){
 // Skip only punctuation and explicit grammatical connectors, not intervening prose.
 let pos=start;const gap=text.slice(pos).match(/^[\s,]*(?:\.\s*(?=d[ao]\s))?(?:[-–]\s*)?(?:(?:ambos|ambas)\s+)?(?:(?:do|da|dos|das)\s+)?/iu);pos+=gap?.[0].length||0;
 const tail=text.slice(pos),shared=/\bamb[oa]s\b/iu.test(text.slice(start,pos));let match;
 const make=(length,identity)=>({...identity,start,end:pos+length,shared});
 const law=tail.match(lawAt);
 if(law){
  const identity=lawIdentity(law[0]),codeId=catalog.byLaw.get(lawKey(identity));
  const named=tail.slice(law[0].length).match(/^\s*\(([^)]+)\)/u);
  const namedCode=named&&catalog.byName.find(([name])=>normalize(named[1])===name)?.[1];
  const conflict=codeId&&namedCode&&codeId!==namedCode;
  return make(law[0].length+(namedCode?named[0].length:0),{status:conflict?'unresolved':codeId?'resolved':'external',codeId,scope:'main',law:identity,reason:conflict?'conflicting-norm-identities':'explicit-law'});
 }
 if((match=tail.match(/^(?:c[oó]digo\s+civil\s+anterior)\b/iu))){
  const explicit=tail.slice(match[0].length).match(/^\s*,\s*/u),old=explicit&&tail.slice(match[0].length+explicit[0].length).match(lawAt);
  return make(match[0].length+(old?explicit[0].length+old[0].length:0),{status:old?'external':'unresolved',law:old?lawIdentity(old[0]):null,reason:old?'previous-code-explicit-law':'previous-code-identity-incomplete'});
 }
 if((match=tail.match(/^(?:deste\s+Ato(?:\s+das\s+Disposi[çc][oõ]es\s+Constitucionais\s+Transit[oó]rias)?|Ato\s+das\s+Disposi[çc][oõ]es\s+Constitucionais\s+Transit[oó]rias|ADCT)\b/iu)))return make(match[0].length,{status:'resolved',codeId:'cf',scope:'adct',reason:'explicit-adct'});
 if((match=tail.match(/^suas\s+Disposi[çc][oõ]es\s+Transit[oó]rias\b/iu)))return make(match[0].length,{status:allowSuas?'resolved':'unresolved',codeId:allowSuas?'cf':undefined,scope:'adct',reason:allowSuas?'coordinated-constitution-adct':'scope-pronoun-without-antecedent'});
 if((match=tail.match(/^(?:desta\s+)?(?:Constitui[çc][aã]o(?:\s+Federal|\s+da\s+Rep[úu]blica)?|CF(?:\/88)?)\b/iu)))return make(match[0].length,{status:'resolved',codeId:'cf',scope:'main',reason:'explicit-constitution'});
 if((match=tail.match(/^dest[ea]\s+(?:Lei|C[oó]digo|Consolida[çc][aã]o)\b/iu)))return make(match[0].length,{status:'resolved',codeId:source.codeId,scope:source.scope,reason:'explicit-self'});
 // Named codes are explicit identities, not topic aliases. A contradictory law
 // or former edition immediately after the name must not be discarded.
 for(const [name,codeId] of catalog.byName){
  const value=normalize(tail.slice(0,name.length));
  if(value!==name||/[\p{L}\d]/u.test(tail[name.length]||''))continue;
  const after=tail.slice(name.length);
  if(/^\s+(?:anterior|revogado)|^\s*[,(/]\s*(?:19\d{2}|de\s+19\d{2})/iu.test(after))return make(name.length,{status:'unresolved',reason:'named-code-edition-not-supported'});
  const appended=after.match(/^\s*,\s*/u),explicit=appended&&after.slice(appended[0].length).match(lawAt);
  if(explicit){const identity=lawIdentity(explicit[0]),actual=catalog.byLaw.get(lawKey(identity));return make(name.length+appended[0].length+explicit[0].length,{status:actual===codeId?'resolved':actual?'unresolved':'external',codeId:actual,scope:'main',law:identity,reason:actual===codeId?'named-and-numbered-code':actual?'conflicting-norm-identities':'external-code-edition'});}
  return make(name.length,{status:'resolved',codeId,scope:'main',reason:'explicit-code-name'});
 }
 if(/^(?:leis?|decreto|emenda|medida|resolu[çc][aã]o|c[oó]digos?|referid[oa]|mesm[oa]|diploma|tratado|conven[çc][aã]o)\b/iu.test(tail))return make((tail.match(/^[^;().]{1,120}/u)||[''])[0].length,{status:'unresolved',reason:'norm-identity-not-supported'});
 return null;
}
export function precedingNorm(text,start,source,catalog){
 // A preceding identity is supported only in a parenthetical "(Code, art...)".
 const prefix=text.slice(0,start),open=prefix.lastIndexOf('(');
 if(open<0||prefix.slice(open).includes(')'))return null;
 const candidate=attachedNorm(text,open+1,source,catalog);
 return candidate&&/^\s*,\s*$/u.test(text.slice(candidate.end,start))?candidate:null;
}
