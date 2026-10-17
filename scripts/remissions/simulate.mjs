import assert from 'node:assert/strict';
import {extractRemissions,sha256} from './extract.mjs';
import {relationGraph} from './graph.mjs';
const originEdges=(data,code,id)=>relationGraph(data).edges.filter(e=>e.source[0]===code&&e.source[1]===id).map(e=>e.target.join('/')).sort();
export function simulateEditions(corpus){
 const base=extractRemissions(corpus),results=[];
 const scenarios=[
  {id:'add-reference',source:['civil','927'],edit(code){code.articles.find(a=>a.id==='927').paragraphs[0].runs[0].text=code.articles.find(a=>a.id==='927').paragraphs[0].runs[0].text.replace('arts. 186 e 187','arts. 186, 187 e 188');},expected:['civil/186','civil/187','civil/188']},
  {id:'remove-reference',source:['civil','927'],edit(code){code.articles.find(a=>a.id==='927').paragraphs[0].runs[0].text=code.articles.find(a=>a.id==='927').paragraphs[0].runs[0].text.replace('(arts. 186 e 187)','');},expected:[]},
  {id:'replace-article',source:['civil','927'],edit(code){code.articles.find(a=>a.id==='927').paragraphs[0].runs[0].text=code.articles.find(a=>a.id==='927').paragraphs[0].runs[0].text.replace('arts. 186 e 187','arts. 186 e 188');},expected:['civil/186','civil/188']},
  {id:'remove-target',source:['civil','927'],edit(code){code.articles=code.articles.filter(a=>a.id!=='187');},expected:[]},
  {id:'rename-target',source:['civil','927'],edit(code){code.articles.find(a=>a.id==='187').id='187-X';},expected:[]},
  {id:'change-adct-scope',source:['cf','adct-54-A'],edit(code){const a=code.articles.find(a=>a.id==='adct-54-A');a.paragraphs[0].runs[0].text=a.paragraphs[0].runs[0].text.replace('deste Ato das Disposições Constitucionais Transitórias','desta Constituição Federal');},expected:['cf/54']},
  {id:'strike-reference',source:['civil','927'],edit(code){code.articles.find(a=>a.id==='927').paragraphs[0].runs[0].deleted=true;},expected:[]},
  {id:'change-norm-qualifier',source:['cpc','240'],edit(code){code.articles.find(a=>a.id==='240').paragraphs[0].runs[0].text=code.articles.find(a=>a.id==='240').paragraphs[0].runs[0].text.replace('Lei nº 10.406, de 10 de janeiro de 2002 (Código Civil)','Lei nº 13.105, de 16 de março de 2015 (Código de Processo Civil)');},expected:['cpc/397','cpc/398']},
  {id:'target-only-other-norm',source:['cpc','240'],mutatedCode:'civil',edit(code){code.articles=code.articles.filter(a=>a.id!=='397');},expected:[]}
 ];
 for(const s of scenarios){
  const copy=structuredClone(corpus),changed=copy.collections.find(c=>c.code.id===(s.mutatedCode||s.source[0]));s.edit(changed.code);changed.sha256=sha256(JSON.stringify(changed.code));
  const data=extractRemissions(copy),before=originEdges(base,...s.source),after=originEdges(data,...s.source);
  assert.deepEqual(after,s.expected,s.id);assert.notEqual(data.editionSetSha256,base.editionSetSha256,s.id);
  results.push({scenario:s.id,source:s.source,before,after,removed:before.filter(x=>!after.includes(x)),added:after.filter(x=>!before.includes(x)),sourceEditionChanged:data.editions[s.source[0]]!==base.editions[s.source[0]],editionSetChanged:true,passed:true});
 }
 return results;
}
