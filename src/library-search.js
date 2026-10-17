import {collections,normalize,searchLibraryReferences} from './data.js';

import {createSearchIndex,searchArticle,fieldRuns} from './search-index.js';
const localIndexes=new WeakMap(),normalizedIndexes=new WeakMap();
function searchIndex(code){
 if(code.searchIndex)return code.searchIndex;
 if(!localIndexes.has(code))localIndexes.set(code,createSearchIndex(code));
 return localIndexes.get(code);
}
function normalizedIndex(index){
 if(!normalizedIndexes.has(index))normalizedIndexes.set(index,index.articles.map(entry=>entry.fields.map(field=>normalize(field[1]))));
 return normalizedIndexes.get(index);
}
export function searchLibraryText(query,area='Todas as áreas'){
 const q=normalize(query.trim());
 if(q.length<2||searchLibraryReferences(q)!==null)return [];
 return collections.filter(code=>area==='Todas as áreas'||code.area.includes(area)).map(code=>{
  const matches=[];
  const index=searchIndex(code),normalized=normalizedIndex(index);
  for(let articleIndex=0;articleIndex<index.articles.length;articleIndex++){
   const entry=index.articles[articleIndex],match=selectLibraryMatch(entry.fields,q,normalized[articleIndex]);
   if(match)matches.push({article:searchArticle(entry,index),match});
  }
  return {code,matches};
 }).filter(group=>group.matches.length);
}

// Prefer a hit whose characters are not struck in the source. This does not
// certify legal force; historical-only matches remain in their original order.
export function selectLibraryMatch(fields,query,texts=fields.map(field=>normalize(field[1]))){
 const q=normalize(query.trim());if(!q)return null;
 const present=(field,index,deleted)=>({kind:field[0],runs:fieldRuns(field),text:field[1],index,query:q,deleted});
 let historical=null;
 for(let n=0;n<fields.length;n++){
  const field=fields[n],text=texts[n];let hit=text.indexOf(q);
  if(hit<0)continue;
  // Source offsets are UTF-16; normalization can remove accents/combining marks.
  const ranges=(field[2]||[]).map(([start,end])=>[normalize(field[1].slice(0,start)).length,normalize(field[1].slice(0,end)).length]);
  if(!historical)historical={field,index:hit};
  for(;hit>=0;hit=text.indexOf(q,hit+1)){
   if(!ranges.some(([start,end])=>hit<end&&hit+q.length>start))return present(field,hit,false);
  }
 }
 return historical?present(historical.field,historical.index,true):null;
}

export function libraryExcerpt(match,limit=220){
 // Map normalized positions back to the original characters; do not alter accents
 // or remove the deletion marks that distinguish historical source text.
 const positions=[];let offset=0;
 for(const char of match.text){
  for(let index=0;index<normalize(char).length;index++)positions.push({start:offset,end:offset+char.length});
  offset+=char.length;
 }
 const hit=positions[match.index]?.start||0;
 const hitEnd=positions[match.index+match.query.length-1]?.end||hit;
 const start=Math.max(0,hit-65),end=Math.min(match.text.length,Math.max(start+limit,hitEnd));
 let cursor=0;const runs=[];
 for(const run of match.runs){
  const from=Math.max(0,start-cursor),to=Math.min(run.text.length,end-cursor);
  if(to>from)runs.push({...run,text:run.text.slice(from,to)});
  cursor+=run.text.length;
 }
 return {runs,leading:start>0,trailing:end<match.text.length};
}
