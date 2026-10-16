import { imported } from '../data/archive/legislation.js';
import { officialImported } from '../data/official/legislation.js';
import { sumulas } from '../data/archive/sumulas.js';
import { officialSumulas } from '../data/official/sumulas.js';

const catalog = [
 {id:'cf',short:'CF',name:'Constituição Federal',area:'Direito Constitucional',law:'Constituição da República de 1988',description:'Direitos fundamentais e a organização do Estado brasileiro.',icon:'◇',url:'https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm'},
 {id:'civil',short:'CC',name:'Código Civil',area:'Direito Civil',law:'Lei nº 10.406/2002',description:'Pessoas, bens, contratos e as relações da vida civil.',icon:'⚖',url:'https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm'},
 {id:'penal',short:'CP',name:'Código Penal',area:'Direito Penal',law:'Decreto-Lei nº 2.848/1940',description:'Crimes, penas e os limites do poder de punir.',icon:'⌘',url:'https://www.planalto.gov.br/ccivil_03/decreto-lei/del2848compilado.htm'},
 {id:'cpc',short:'CPC',name:'Código de Processo Civil',area:'Direito Processual',law:'Lei nº 13.105/2015',description:'As regras e os caminhos do processo civil brasileiro.',icon:'▤',url:'https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13105.htm'},
 {id:'cdc',short:'CDC',name:'Código de Defesa do Consumidor',area:'Direito do Consumidor',law:'Lei nº 8.078/1990',description:'Direitos e proteção nas relações de consumo.',icon:'♧',url:'https://www.planalto.gov.br/ccivil_03/leis/l8078compilado.htm'},
 {id:'ctn',short:'CTN',name:'Código Tributário Nacional',area:'Direito Tributário',law:'Lei nº 5.172/1966',description:'Tributos, obrigações e relações com o fisco.',icon:'▥',url:'https://www.planalto.gov.br/ccivil_03/leis/l5172compilado.htm'}
];
export const normalize = value => String(value).normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
export const codes = catalog.map(code => {
 const content = officialImported[code.id] || imported[code.id];
 const bySection = new Map(content.sections.map(section=>[section.id,section.title]));
 return {...code,...content,articles:content.articles.map(article=>{
  const text=article.text ?? article.paragraphs.map(p=>p.runs.map(r=>r.text).join('').replace(/\s+/g,' ').trim()).join('\n');
  return {...article,text,section:bySection.get(article.sectionId),searchText:normalize((article.title||'')+' '+text)};
 })};
});
export const collections = [...codes, ...(officialSumulas.length?officialSumulas:sumulas).map(collection=>({...collection,articles:collection.articles.map(article=>{
 const text=article.paragraphs.map(p=>p.runs.map(r=>r.text).join('')).join('\n');
 const notes=(article.notes||[]).map(p=>p.runs.map(r=>r.text).join('')).join('\n');
 return {...article,text,section:collection.sections.find(s=>s.id===article.sectionId)?.title,searchText:normalize(text+' '+notes)};
})}))];
export function articleLabel(article) {
 if(article.kind==='vinculante')return `Súmula Vinculante ${article.number}`;
 const format = n => String(n).replace(/^(\d+)(.*)$/,(_,base,suffix)=>Number(base).toLocaleString('pt-BR')+suffix);
 return `${article.scope==='adct'?'ADCT · ':''}${article.rangeEnd?'Arts.':'Art.'} ${format(article.number)}${article.rangeEnd?' a '+format(article.rangeEnd):''}`;
}
export function articleById(code, id) {
 const exact = code.articles.find(article=>article.id===id);
 if(exact) return exact;
 const scope = id.startsWith('adct-') ? 'adct' : 'main';
 const n = Number(id.replace('adct-',''));
 return code.articles.find(article=>article.scope===scope && article.rangeEnd && n>=Number(article.number) && n<=article.rangeEnd);
}
const referenceAliases = [
 ...catalog.flatMap(code=>[code.short,code.name].map(alias=>({alias:normalize(alias),codeId:code.id}))),
 {alias:'cf/88',codeId:'cf'}, {alias:'cf88',codeId:'cf'}, {alias:'constituição',codeId:'cf'},
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
 let pool=code.articles.filter(article=>scope==='all'||article.scope===scope);
 if(!q)return pool;
 if(ref){
  if(ref.codeId&&ref.codeId!==code.id||ref.kind==='article'&&code.kind==='sumulas')return [];
  if(ref.scope)pool=code.articles.filter(article=>article.scope===ref.scope);
  return pool.filter(article=>article.number===ref.number||(!ref.number.includes('-')&&article.rangeEnd&&Number(ref.number)>=Number(article.number)&&Number(ref.number)<=article.rangeEnd));
 }
 return pool.filter(article=>article.searchText.includes(q));
}
