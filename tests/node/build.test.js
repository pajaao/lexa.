import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile,mkdtemp,cp,rm,writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join,dirname} from 'node:path';
import {pathToFileURL} from 'node:url';
import {collections} from '../../src/data.js';

async function renderHome(payload){
 const html=await readFile(new URL('../../dist/index.html',import.meta.url),'utf8');
 const entry=html.match(/<script type="module" src="\.\/([^\"]+)"/)[1];
 const folder=await mkdtemp(join(tmpdir(),'lexa-native-modules-'));
 await writeFile(join(folder,'package.json'),'{"type":"module"}');
 await cp(new URL('../../dist/'+dirname(entry)+'/',import.meta.url),join(folder,'app'),{recursive:true});
 if(payload){
  const path=join(folder,'app/collections.js'),original=await readFile(path,'utf8');
  const injected=original.replace('"name":"Constituição Federal"','"name":'+JSON.stringify(payload));
  assert.notEqual(original,injected);await writeFile(path,injected);
 }
 const nodes=new Map();
 const node=selector=>{if(!nodes.has(selector))nodes.set(selector,{innerHTML:'',value:'',classList:{toggle(){}},addEventListener(){}});return nodes.get(selector);};
 const previous={document:globalThis.document,window:globalThis.window,location:globalThis.location};
 globalThis.document={querySelector:node,querySelectorAll:()=>[],documentElement:{classList:{toggle(){}}},addEventListener(){}};
 globalThis.window={addEventListener(){},scrollTo(){}};globalThis.location={hash:''};
 try{await import(pathToFileURL(join(folder,'app/app.js')).href);return {html,nodes};}
 finally{Object.assign(globalThis,previous);await rm(folder,{recursive:true,force:true});}
}
test('shell e módulos nativos inicializam cartões sem carregar textos jurídicos',async()=>{
 const {html,nodes}=await renderHome();
 assert.ok(Buffer.byteLength(html)<300_000);
 assert.doesNotMatch(html,/A Constituição poderá ser emendada/);
 assert.match(html,/<style>/);assert.match(html,/rel="modulepreload"/);
 assert.equal((nodes.get('#cards').innerHTML.match(/class="code-card"/g)||[]).length,collections.length);
 assert.match(nodes.get('#cards').innerHTML,/href="#\/sv"/);
 assert.match(nodes.get('#app').innerHTML,new RegExp(collections.find(c=>c.id==='sv').articles.length+' súmulas vinculantes'));
});
test('campos do catálogo continuam sendo texto escapado em módulos nativos',async()=>{
 const payload='<img src=x onerror="globalThis.pwned=true">';
 const {nodes}=await renderHome(payload);
 assert.ok(nodes.get('#cards').innerHTML.includes('&lt;img src=x onerror=&quot;globalThis.pwned=true&quot;&gt;'));
 assert.ok(!nodes.get('#cards').innerHTML.includes(payload));assert.equal(globalThis.pwned,undefined);
});
