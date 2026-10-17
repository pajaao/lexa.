// Compact search data is derived from the original runs, never an alternative
// legal edition. The reader and copy functions always use the original norm.
export function compactField(kind,runs){
 const text=runs.map(run=>run.text).join(''),deleted=[];let offset=0;
 for(const run of runs){if(run.deleted&&run.text.length)deleted.push([offset,offset+run.text.length]);offset+=run.text.length;}
 return deleted.length?[kind,text,deleted]:[kind,text];
}
export function fieldRuns(field){
 const text=field[1],runs=[];let offset=0;
 for(const [start,end] of field[2]||[]){
  if(start>offset)runs.push({text:text.slice(offset,start),deleted:false});
  runs.push({text:text.slice(start,end),deleted:true});offset=end;
 }
 if(offset<text.length||!runs.length)runs.push({text:text.slice(offset),deleted:false});
 return runs;
}
export function createSearchIndex(code){
 const sections=new Map(code.sections.map((section,index)=>[section.id,index]));
 return {id:code.id,sections:code.sections.map(section=>section.title),articles:code.articles.map(article=>({
  id:article.id,number:article.number,scope:article.scope,kind:article.kind,
  rangeEnd:article.rangeEnd,status:article.status,section:sections.get(article.sectionId),
  fields:[...article.paragraphs.map(p=>compactField('text',p.runs)),
   ...(article.title?[compactField('title',[{text:article.title}])]:[]),
   ...(article.notes||[]).map(p=>compactField('notes',p.runs))]
 }))};
}
export function searchArticle(entry,index){
 const {fields,...article}=entry;
 article.section=index.sections[entry.section];
 // References need a preview; textual search only needs metadata and the hit.
 Object.defineProperty(article,'paragraphs',{get:()=>fields.filter(f=>f[0]==='text').map(f=>({runs:fieldRuns(f)}))});
 Object.defineProperty(article,'text',{get:()=>fields.filter(f=>f[0]==='text').map(f=>f[1]).join('\n')});
 return article;
}
