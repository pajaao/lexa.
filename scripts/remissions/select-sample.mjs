// Reproduce selection of sources only. Does not create expected relations or
// invoke the extractor. Labels remain declarative, frozen review fixtures.
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {resolve} from 'node:path';
import {readFile} from 'node:fs/promises';
import {loadCorpus} from './corpus.mjs';
const digest=key=>createHash('sha256').update('lexa-fase05-holdout-v1:'+key.join(':')).digest('hex');
export function selectEvaluationSources(corpus,development){
 const excluded=new Set(development.map(g=>g.code+'/'+g.article)),selected=[];
 for(const {code} of corpus.collections){
  if(code.id==='sv')continue;
  const candidates=[],negative=[];
  for(const a of code.articles){
   if(excluded.has(code.id+'/'+a.id))continue;
   for(const [pi,p] of a.paragraphs.entries()){
    const text=p.runs.map(r=>r.text).join(''),matches=[...text.matchAll(/\b(?:arts?\.|artigos?)\s*\d/giu)],key=[code.id,a.id,pi],length=[...text].length;
    if(length>35&&length<850&&matches.some(m=>m.index>0))candidates.push({hash:digest(key),key});
    if(pi===0&&matches.length===1&&matches[0].index===0&&length>70&&length<450)negative.push({hash:digest(key),key});
   }
  }
  candidates.sort((a,b)=>a.hash<b.hash?-1:1);negative.sort((a,b)=>a.hash<b.hash?-1:1);
  const picked=[];
  for(const c of candidates){if(picked.some(v=>v[1]===c.key[1]))continue;picked.push(c.key);if(picked.length===3)break;}
  selected.push(...picked);if(negative.length)selected.push(negative[0].key);
  if(code.id==='cf')for(const c of candidates){
   if(!c.key[1].startsWith('adct-')||selected.some(v=>v[0]==='cf'&&v[1]===c.key[1]))continue;
   selected.push(c.key);if(selected.filter(v=>v[0]==='cf'&&v[1].startsWith('adct-')).length>=7)break;
  }
 }
 return [...selected,['ctn','74',3],['ctn','97',3]];
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const development=JSON.parse(await readFile(new URL('../../tests/fixtures/remissions/phase0.json',import.meta.url),'utf8'));
 console.log(JSON.stringify(selectEvaluationSources(await loadCorpus(),development),null,2));
}
