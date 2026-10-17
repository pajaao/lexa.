import test from 'node:test';
import assert from 'node:assert/strict';
import {collections} from '../../src/data.js';
import {buildSectionTree,sectionPath,unitKind} from '../../src/structure.js';

test('árvore preserva todas as divisões e artigos, em ordem e com CF/ADCT separados',()=>{
 for(const code of collections)for(const scope of ['main','adct']){
  const {roots,nodes}=buildSectionTree(code.sections,code.articles,scope);
  assert.deepEqual(roots.flatMap(node=>node.articles.map(a=>a.id)),code.articles.filter(a=>a.scope===scope).map(a=>a.id));
  const walk=node=>node.items.flatMap(item=>item.kind==='section'?[item.id]:walk(item.node));
  const direct=roots.flatMap(walk);
  assert.deepEqual(direct,code.sections.filter(s=>s.scope===scope).map(s=>s.id));
  for(const node of nodes.values()){
   assert.ok(node.articles.every(a=>a.scope===scope&&node.sectionIds.includes(a.sectionId)));
   for(const child of node.children)assert.ok(child.sectionIds.every(id=>node.sectionIds.includes(id)));
  }
 }
});

test('capítulos com o mesmo número em livros diferentes mantêm identidades próprias',()=>{
 const sections=[{id:'a',scope:'main',title:'LIVRO I › CAPÍTULO I'},{id:'b',scope:'main',title:'LIVRO II › CAPÍTULO I'}];
 const articles=sections.map((section,index)=>({id:String(index+1),sectionId:section.id,scope:'main'}));
 const tree=buildSectionTree(sections,articles,'main');
 assert.equal(tree.roots.length,2);
 assert.notEqual(tree.roots[0].children[0].id,tree.roots[1].children[0].id);
 assert.deepEqual(tree.roots[0].sectionIds,['a']);assert.deepEqual(tree.roots[1].sectionIds,['b']);
 assert.deepEqual(sectionPath(sections[0]),['LIVRO I','CAPÍTULO I']);
});

test('recuos reconhecem marcadores sem alterar palavras, números ou riscados',()=>{
 for(const [text,kind] of [['Art. 5º Todos','caput'],['§ 1º Exemplo','paragraph'],['Parágrafo único. Exemplo','paragraph'],['XXIV – Exemplo','inciso'],['a) Exemplo','alinea'],['1. Exemplo','item'],['Texto de continuação','continuation']]){
  const p={runs:[{text,deleted:true}]};const original=JSON.stringify(p);
  assert.equal(unitKind(p,kind==='caput'?0:1),kind);assert.equal(JSON.stringify(p),original);
 }
});

test('modelo do leitor reaproveita mapas/árvores sem misturar dados de outra edição',async()=>{
 const {readerModel}=await import('../../src/reader-model.js');
 const code=collections.find(code=>code.id==='civil');
 const first=readerModel(code),again=readerModel(code);
 assert.equal(first,again);
 assert.deepEqual([...first.bySection.values()].flat().map(a=>a.id),code.articles.map(a=>a.id));
 const replacement={...code,articles:[...code.articles],sections:[...code.sections]};
 assert.notEqual(readerModel(replacement),first);
 const paragraph={runs:[{text:'Texto sem marcador'}]};
 assert.equal(unitKind(paragraph,0),'caput');assert.equal(unitKind(paragraph,1),'continuation');
});
