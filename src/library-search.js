import {collections,normalize,searchLibraryReferences} from './data.js';

import {createSearchIndex,searchArticle,fieldRuns} from './search-index.js';
const localIndexes=new WeakMap(),normalizedFields=new WeakMap();
function searchIndex(code){
 if(code.searchIndex)return code.searchIndex;
 if(!localIndexes.has(code))localIndexes.set(code,createSearchIndex(code));
 return localIndexes.get(code);
}
function normalizedField(field){
 if(!normalizedFields.has(field))normalizedFields.set(field,normalize(field[1]));
 return normalizedFields.get(field);
}
export function searchLibraryText(query,area='Todas as áreas'){
 const q=normalize(query.trim());
 if(q.length<2||searchLibraryReferences(q)!==null)return [];
 return collections.filter(code=>area==='Todas as áreas'||code.area.includes(area)).map(code=>{
  const matches=[];
  const index=searchIndex(code);
  for(const entry of index.articles){
   const field=entry.fields.find(field=>normalizedField(field).includes(q));
   if(field)matches.push({article:searchArticle(entry,index),match:{kind:field[0],runs:fieldRuns(field),text:field[1],index:normalizedField(field).indexOf(q),query:q}});
  }
  return {code,matches};
 }).filter(group=>group.matches.length);
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
