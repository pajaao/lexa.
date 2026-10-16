import {collections,normalize,searchLibraryReferences} from './data.js';

const libraryIndexes=new WeakMap();
function indexedArticles(code){
 if(!libraryIndexes.has(code))libraryIndexes.set(code,code.articles.map(article=>{
  const fields=[
   ...article.paragraphs.map(p=>({kind:'text',runs:p.runs})),
   ...(article.title?[{kind:'title',runs:[{text:article.title,deleted:false}]}]:[]),
   ...(article.notes||[]).map(p=>({kind:'notes',runs:p.runs}))
  ].map(field=>({...field,text:field.runs.map(run=>run.text).join('')}));
  return {article,fields:fields.map(field=>({...field,normalized:normalize(field.text)}))};
 }));
 return libraryIndexes.get(code);
}

export function searchLibraryText(query,area='Todas as áreas'){
 const q=normalize(query.trim());
 if(q.length<2||searchLibraryReferences(q)!==null)return [];
 return collections.filter(code=>area==='Todas as áreas'||code.area.includes(area)).map(code=>{
  const matches=[];
  for(const {article,fields} of indexedArticles(code)){
   const field=fields.find(field=>field.normalized.includes(q));
   if(field)matches.push({article,match:{kind:field.kind,runs:field.runs,text:field.text,index:field.normalized.indexOf(q),query:q}});
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
