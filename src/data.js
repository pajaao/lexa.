import {articleLookup} from './article-lookup.js';
import {searchArticle} from './search-index.js';
import {catalog} from './catalog.js';
import {collections,codes} from './collections.js';
import {normalize} from './collection-model.js';
export {collections,codes,normalize};

export function articleLabel(article) {
 if(article.kind==='vinculante')return `Súmula Vinculante ${article.number}`;
 const format = n => String(n).replace(/^(\d+)(.*)$/,(_,base,suffix)=>Number(base).toLocaleString('pt-BR')+suffix);
 return `${article.scope==='adct'?'ADCT · ':''}${article.rangeEnd?'Arts.':'Art.'} ${format(article.number)}${article.rangeEnd?' a '+format(article.rangeEnd):''}`;
}
export function articleById(code, id) {
 const pool=code.loaded?code.articles:(code.searchIndex?.articles||code.articles);
 const present=entry=>code.searchIndex&&!code.loaded?entry&&searchArticle(entry,code.searchIndex):entry;
 const lookup=articleLookup(pool);
 const exact = lookup.ids.get(id);
 if(exact) return present(exact);
 const scope = id.startsWith('adct-') ? 'adct' : 'main';
 const n = Number(id.replace('adct-',''));
 return present(lookup.ranges.find(article=>article.scope===scope && article.rangeEnd && n>=Number(article.number) && n<=article.rangeEnd));
}
const referenceAliases = [
 ...catalog.flatMap(code=>[code.short,code.name].map(alias=>({alias:normalize(alias),codeId:code.id}))),
 ...[['Lei de Licitações','licitacoes'],['licitações','licitacoes'],['Maria da Penha','maria-penha'],['Improbidade','improbidade']].map(([alias,codeId])=>({alias:normalize(alias),codeId})),
 {alias:'cf/88',codeId:'cf'}, {alias:'cf88',codeId:'cf'}, {alias:'constituição',codeId:'cf'},
 {alias:'penal',codeId:'penal'},
 {alias:'adct',codeId:'cf',scope:'adct'},
 ...['súmula vinculante','súmula','sv'].map(alias=>({alias:normalize(alias),codeId:'sv'}))
].map(item=>({...item,alias:normalize(item.alias)})).sort((a,b)=>b.alias.length-a.alias.length);

export function parseReference(query) {
 let rest=normalize(query).trim().replace(/\s+/g,' ').replace(/[–—]/g,'-').replace(/^(sv|adct)(?=\d)/,'$1 ');
 if(/^(?:sv|sumula)\b/.test(rest))rest=rest.replace(/\s+(?:do )?stf$/,'');
 let codeId=null,scope=null;
 for(let pass=0;pass<3;pass++){
  let matched=false;
  for(const item of referenceAliases){
   let next;
   if(rest.startsWith(item.alias+' '))next=rest.slice(item.alias.length).trim();
   else if(rest.endsWith(' '+item.alias))next=rest.slice(0,-item.alias.length).trim().replace(/\s+(?:da|do|de)$/,'');
   else continue;
   if(codeId&&codeId!==item.codeId)return null;
   codeId=item.codeId;scope=item.scope||scope;rest=next;matched=true;break;
  }
  if(!matched)break;
 }
 const isArticle=/^(?:arts?\.?|artigos?)\s*/.test(rest);
 rest=rest.replace(/^(?:artigos?|arts?\.?)\s*/,'').replace(/^n[.º°o]*\s*/,'');
 const number=rest.match(/^(\d+(?:\.\d{3})*)(?:[º°])?\s*((?:-\s*[a-z]+)*)\.?$/);
 if(!number||(isArticle&&codeId==='sv'))return null;
 return {codeId,scope:scope||(codeId?'main':null),number:number[1].replace(/\./g,'')+number[2].replace(/\s/g,'').toUpperCase(),kind:codeId==='sv'?'vinculante':isArticle?'article':null};
}

export function searchLibraryReferences(query) {
 const ref=parseReference(query);
 if(!ref)return null;
 return collections.filter(code=>(!ref.codeId||code.id===ref.codeId)&&!(ref.kind==='article'&&code.kind==='sumulas')).flatMap(code=>{
  const article=articleById(code,(ref.scope==='adct'?'adct-':'')+ref.number);
  return article?[{code,article}]:[];
 });
}

export function searchArticles(code, query, scope = 'main') {
 const q=normalize(query.trim());
 const ref=parseReference(q);
 const lookup=articleLookup(code.articles);
 let pool=scope==='all'?code.articles:(lookup.scopes.get(scope)||[]);
 if(!q)return pool;
 if(ref){
  if(ref.codeId&&ref.codeId!==code.id||ref.kind==='article'&&code.kind==='sumulas')return [];
  if(ref.scope)pool=lookup.scopes.get(ref.scope)||[];
  return pool.filter(article=>article.number===ref.number||(!ref.number.includes('-')&&article.rangeEnd&&Number(ref.number)>=Number(article.number)&&Number(ref.number)<=article.rangeEnd));
 }
 return pool.filter(article=>article.searchText.includes(q));
}
