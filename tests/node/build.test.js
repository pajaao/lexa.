import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
import {collections} from '../../src/data.js';

test('HTML autocontido inicializa a biblioteca completa, inclusive súmulas, sem importar arquivos',()=>{
 const html=readFileSync(new URL('../../dist/index.html',import.meta.url),'utf8');
 assert.match(html,/<style>/);
 assert.doesNotMatch(html,/<script[^>]+src=/);
 const script=html.match(/<script>([\s\S]*?)<\/script>/)[1];
 const nodes=new Map();
 const node=selector=>{
  if(!nodes.has(selector))nodes.set(selector,{innerHTML:'',value:'',classList:{toggle(){}},addEventListener(){}});
  return nodes.get(selector);
 };
 vm.runInNewContext(script,{
  document:{querySelector:node,querySelectorAll:()=>[],documentElement:{classList:{toggle(){}}},addEventListener(){}},
  window:{addEventListener(){},scrollTo(){}},location:{hash:''},Intl,URLSearchParams,
 },{timeout:5000});
 assert.equal((node('#cards').innerHTML.match(/class="code-card"/g)||[]).length,collections.length);
 assert.match(node('#cards').innerHTML,/href="#\/sv"/);
 assert.match(node('#app').innerHTML,new RegExp(collections.find(c=>c.id==='sv').articles.length+' súmulas vinculantes'));
});
