const lookups=new WeakMap();
export function articleLookup(articles){
 if(!lookups.has(articles)){
  const ids=new Map(),scopes=new Map(),ranges=[];
  for(const article of articles){
   ids.set(article.id,article);
   if(!scopes.has(article.scope))scopes.set(article.scope,[]);
   scopes.get(article.scope).push(article);
   if(article.rangeEnd)ranges.push(article);
  }
  lookups.set(articles,{ids,scopes,ranges});
 }
 return lookups.get(articles);
}
