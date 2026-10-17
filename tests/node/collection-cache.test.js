import test from 'node:test';
import assert from 'node:assert/strict';
import {createCollectionCache} from '../../src/collection-cache.js';
const norm=id=>({id,articles:[{id:'1'}],sections:[{id:'s'}],source:{edition:'original'},introductions:[{}],loaded:true,searchIndex:{id}});
test('cache limita leitores e preserva metadados, índice e arrays jurídicos originais',()=>{
 const cache=createCollectionCache(3),codes=['a','b','c','d'].map(norm),original=codes[0].articles;
 for(const code of codes){cache.activate(code.id);cache.remember(code);}
 assert.deepEqual(cache.ids(),['b','c','d']);
 assert.equal(codes[0].loaded,false);assert.deepEqual(original,[{id:'1'}]);
 assert.deepEqual(codes[0].source,{edition:'original'});assert.equal(codes[0].searchIndex.id,'a');
 cache.remember(codes[1]);assert.deepEqual(cache.ids(),['c','d','b']);
});
test('respostas tardias não expulsam o leitor ativo',()=>{
 const cache=createCollectionCache(1),active=norm('active'),late=norm('late');
 cache.activate(active.id);cache.remember(active);cache.remember(late);
 assert.deepEqual(cache.ids(),['active']);assert.equal(active.loaded,true);assert.equal(late.loaded,false);
});
