export const normalize = value => String(value).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
const searchTexts=new WeakMap(),articleTexts=new WeakMap();
export function prepareCollection(collection){
 const sections=new Map(collection.sections.map(section=>[section.id,section.title])),isSumula=collection.kind==='sumulas';
 return {...collection,articleCount:collection.articles.length,loaded:true,articles:collection.articles.map(original=>{
  const paragraphs=original.paragraphs,sourceText=original.text;
  const article={...original,section:sections.get(original.sectionId)};
  Object.defineProperty(article,'text',{enumerable:true,get(){
   if(!articleTexts.has(article))articleTexts.set(article,sourceText??paragraphs.map(p=>{const value=p.runs.map(r=>r.text).join('');return isSumula?value:value.replace(/\s+/g,' ').trim();}).join('\n'));
   return articleTexts.get(article);
  }});
  Object.defineProperty(article,'searchText',{enumerable:false,get(){
   if(!searchTexts.has(article))searchTexts.set(article,normalize((article.title||'')+' '+article.text+' '+(article.notes||[]).map(p=>p.runs.map(r=>r.text).join('')).join('\n')));
   return searchTexts.get(article);
  }});
  return article;
 })};
}
