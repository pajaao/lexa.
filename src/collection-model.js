export const normalize = value => String(value).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
const searchTexts=new WeakMap();
export function prepareCollection(collection){
 const sections=new Map(collection.sections.map(section=>[section.id,section.title]));
 return {...collection,articleCount:collection.articles.length,loaded:true,articles:collection.articles.map(original=>{
  const text=original.text??original.paragraphs.map(p=>{const value=p.runs.map(r=>r.text).join('');return collection.kind==='sumulas'?value:value.replace(/\s+/g,' ').trim();}).join('\n');
  const article={...original,text,section:sections.get(original.sectionId)};
  Object.defineProperty(article,'searchText',{enumerable:false,get(){
   if(!searchTexts.has(article))searchTexts.set(article,normalize((article.title||'')+' '+text+' '+(article.notes||[]).map(p=>p.runs.map(r=>r.text).join('')).join('\n')));
   return searchTexts.get(article);
  }});
  return article;
 })};
}
