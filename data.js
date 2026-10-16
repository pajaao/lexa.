import { imported } from './content.js';
import { officialImported } from './official-content.js';

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
export function articleLabel(article) {
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
export function searchArticles(code, query, scope = 'main') {
 const q = normalize(query.trim());
 let pool = code.articles.filter(article=>scope==='all'||article.scope===scope);
 if(!q) return pool;
 const match = q.match(/^(adct\s*)?(?:arts?\.?\s*)?(\d+(?:\.\d{3})*)(?:[º°])?\s*((?:-\s*[a-z]+)*)\.?$/);
 if(match) {
  if(match[1]) pool=code.articles.filter(article=>article.scope==='adct');
  const n=match[2].replace(/\./g,'')+match[3].replace(/\s/g,'').toUpperCase();
  return pool.filter(article=>article.number===n||(!match[3] && article.rangeEnd && Number(n)>=Number(article.number) && Number(n)<=article.rangeEnd));
 }
 return pool.filter(article=>article.searchText.includes(q));
}
