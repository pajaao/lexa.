// Presentation only: paths and unit markers come from the recorded legal text.
export const sectionPath=section=>section.title.split(' › ').filter(Boolean);
export function headingKind(text){
 const token=text.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
 return /^(parte|livro|titulo|subtitulo|capitulo|secao|subsecao)\b/.exec(token)?.[1]||'division';
}
export function unitKind(paragraph,index){
 const text=paragraph.runs.map(run=>run.text).join('').trimStart();
 if(/^(?:§\s*\d|Parágrafo\s+único\b)/i.test(text))return 'paragraph';
 if(/^[IVXLCDM]+\s*[-–—]/.test(text))return 'inciso';
 if(/^[a-z]\s*\)/.test(text))return 'alinea';
 if(/^\d+\s*[-–.)]/.test(text))return 'item';
 return index===0?'caput':'continuation';
}
export function buildSectionTree(sections,articles,scope){
 const roots=[],nodes=new Map();let previous=[],stack=[],serial=0;
 const bySection=new Map();
 for(const article of articles){if(!bySection.has(article.sectionId))bySection.set(article.sectionId,[]);bySection.get(article.sectionId).push(article);}
 for(const section of sections.filter(s=>s.scope===scope)){
  const path=sectionPath(section);let common=0;
  while(common<path.length&&previous[common]===path[common])common++;
  stack=stack.slice(0,common);
  for(let depth=common;depth<path.length;depth++){
   const node={id:`${scope}-${serial++}`,label:path[depth],depth,children:[],sectionIds:[],direct:[],items:[],articles:[]};
   (depth?stack[depth-1].children:roots).push(node);
   if(depth)stack[depth-1].items.push({kind:'node',node});
   stack.push(node);nodes.set(node.id,node);
  }
  const entries=bySection.get(section.id)||[];
  for(const node of stack){node.sectionIds.push(section.id);node.articles.push(...entries);}
  if(stack.length){stack.at(-1).direct.push(section.id);stack.at(-1).items.push({kind:'section',id:section.id});}previous=path;
 }
 return {roots,nodes};
}
