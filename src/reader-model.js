import {buildSectionTree} from './structure.js';
const models=new WeakMap();
export function readerModel(code){
 // Key by the legal data array, not the permanent catalog object: a discarded
 // edition or an evicted collection must not be retained by its view cache.
 if(!models.has(code.articles)){
  const bySection=new Map();
  for(const article of code.articles){
   if(!bySection.has(article.sectionId))bySection.set(article.sectionId,[]);
   bySection.get(article.sectionId).push(article);
  }
  models.set(code.articles,{
   sectionMap:new Map(code.sections.map(section=>[section.id,section])),bySection,
   trees:new Map(['main','adct'].map(scope=>[scope,buildSectionTree(code.sections,code.articles,scope)]))
  });
 }
 return models.get(code.articles);
}
