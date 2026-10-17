// Experimental build-time grammar. Offsets are native JavaScript UTF-16 indices.
// A bounded lexer and small list parser, not the user-query parser or a legal interpreter.
const numberSource=String.raw`(?:\d{1,3}(?:\.\d{3})+|\d+)(?:\s*[º°o])?(?:\s*[-–]\s*[A-Za-z]{1,2}(?!\p{L}))?(?![\p{L}\d])`;
const numberAt=new RegExp('^'+numberSource,'u');
const prefixSource=String.raw`\b(?:arts?\.\s*|(?:arts?|artigos?)\s+)`;
const articleHead=new RegExp(prefixSource+'(?='+numberSource+')','giu');
const numeral=String.raw`[IVXLCDM]+`;
const unitNumber=String.raw`\d+(?:\s*[º°o])?(?:\s*[-–]\s*[A-Z]{1,2})?`;
const ordinal=String.raw`\d+\s*[º°o](?:\s*[-–]\s*[A-Z]{1,2})?`;
const quoted=String.raw`[“"'‘]?[a-z][”"'’]`;
const unitList=value=>String.raw`${value}(?:\s*(?:,\s*(?:e\s+)?|\be\s+|\bou\s+|\ba\s+)${value})*`;
// Only an ordinal may extend a § list after its first item: in "§5º, 157",
// 157 belongs to the articles list, not to a guessed paragraph157.
const para=String.raw`§{1,2}\s*${unitNumber}(?:\s*(?:,\s*(?:e\s+)?|\be\s+|\ba\s+)${ordinal})*`;
const qualifierSource=String.raw`(?:${para}|par[áa]grafo\s+[úu]nico|(?:incisos?\s+|n\.\s*)?${unitList(numeral)}(?!\p{L})|(?:al[íi]neas?|letras?)\s+${unitList(quoted)}|${unitList(quoted)}|caput)`;
const qualifierAt=new RegExp('^'+qualifierSource,'iu');
export const canonicalNumber=value=>value.replace(/[.\sº°o]/g,'').replace('–','-').toUpperCase();
const skipSpace=(t,i)=>i+(t.slice(i).match(/^\s*/u)?.[0].length||0);
function readNumber(t,i){const m=t.slice(i).match(numberAt);return m?{number:canonicalNumber(m[0]),start:i,end:i+m[0].length}:null;}
function readQualifier(t,i){
 const m=t.slice(i).match(qualifierAt);if(!m)return null;
 const text=m[0];return {kind:/^§|^par[áa]grafo/iu.test(text)?'paragraph':/al[íi]nea|letra|[“"'‘]/iu.test(text)?'alinea':/^caput/iu.test(text)?'caput':'inciso',start:i,end:i+text.length,text};
}
function suffixQualifiers(t,i){
 const qualifiers=[];let end=i;
 while(true){
  const gap=t.slice(end).match(/^\s*(?:,\s*|(?:do|da|dos|das)\s+)/iu);
  if(!gap)break;
  const start=end+gap[0].length,q=readQualifier(t,start);
  if(!q)break;qualifiers.push(q);end=q.end;
 }
 return {end,qualifiers};
}
function leadingQualifiers(t,start){
 // Require a syntactic bridge immediately before "art.", not an arbitrary
 // qualifier mentioned earlier in the paragraph. Keep the exact raw substring.
 const preceding=t.slice(0,start),bridge=preceding.match(/(?:do|da|dos|das)\s*$/iu);
 if(!bridge)return [];
 const limit=Math.max(0,start-180);let selected=null;
 for(let i=limit;i<start;i++){
  if(i&&/[\p{L}\d]/u.test(t[i-1]))continue;
  const q=readQualifier(t,i);if(!q)continue;
  let end=q.end;
  while(true){const step=t.slice(end,start).match(/^\s+(?:do|da|dos|das)\s+/iu);if(!step)break;const next=readQualifier(t,end+step[0].length);if(!next)break;end=next.end;}
  if(/^\s+(?:do|da|dos|das)\s*$/iu.test(t.slice(end,start))){selected={...q,end:start,text:t.slice(i,start)};break;}
 }
 return selected?[selected]:[];
}
export function lexArticles(text){
 const expressions=[];let consumed=0;
 for(const head of text.matchAll(articleHead)){
  if(head.index<consumed)continue;
  const first=readNumber(text,head.index+head[0].length);if(!first)continue;
  let end=first.end;const members=[first],ranges=[],qualifiers=leadingQualifiers(text,head.index);
  while(true){
   const q=suffixQualifiers(text,end);qualifiers.push(...q.qualifiers.map(v=>({...v,articleNumber:members.at(-1).number})));end=q.end;
   const connector=text.slice(end).match(/^\s*(,\s*(?:e\s+)?|e\s+|a\s+|até\s+)/iu);
   if(!connector)break;
   let cursor=skipSpace(text,end+connector[0].length);
   const repeated=text.slice(cursor).match(new RegExp('^'+prefixSource,'iu'));
   if(repeated)cursor+=repeated[0].length;
   const next=readNumber(text,cursor);if(!next)break;
   const range=/^(?:a|até)\b/iu.test(connector[1].trim());
   if(range)ranges.push({from:members.at(-1).number,to:next.number,start:end,end:next.end});
   members.push(next);end=next.end;
  }
  consumed=end;
  expressions.push({start:head.index,end,members,ranges,qualifiers,raw:text.slice(head.index,end)});
 }
 return expressions;
}
export function implicitExpressions(text,covered){
 const found=[];
 const patterns=[
  /\bartigo\s+(?:anterior|seguinte|precedente)\b/giu,
  new RegExp(String.raw`(?:${para}|par[áa]grafo\s+[úu]nico|incisos?\s+${unitList(numeral)}|al[íi]neas?\s+${unitList(quoted)}|caput)(?:\s+(?:do|da)\s+caput)?\s+dest[ea]\s+(?:artigo|inciso|par[áa]grafo)\b`,'giu'),
  new RegExp(para,'giu')
 ];
 for(const pattern of patterns)for(const m of text.matchAll(pattern)){
  const span={start:m.index,end:m.index+m[0].length};
  if(covered.some(c=>span.start<c.end&&span.end>c.start)||found.some(c=>span.start<c.end&&span.end>c.start))continue;
  if(!text.slice(0,span.start).trim())continue; // the paragraph's own label
  found.push({...span,raw:m[0],members:[],ranges:[],qualifiers:[],implicit:true});
 }
 return found.sort((a,b)=>a.start-b.start);
}
