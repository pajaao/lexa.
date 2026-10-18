// Declared adversarial expectations, never inferred from extractor output.
import {readFile,writeFile} from 'node:fs/promises';
import {pathToFileURL} from 'node:url';
import {resolve} from 'node:path';
import {buildPackage} from '../build.mjs';
import {extractRemissions,sha256} from './extract.mjs';
import {applyEligibility} from './eligibility.mjs';
export const cases=JSON.parse(await readFile(new URL('../../tests/fixtures/remissions-1a-1/adversarial.json',import.meta.url)));
export async function corpusFromBuild(){const b=await buildPackage();return {collections:b.manifest.collections.map(c=>({code:JSON.parse(b.files.get(c.file)),sha256:c.sha256}))};}
export function caseCorpus(corpus,c){
 const copy=structuredClone(corpus),entry=copy.collections.find(v=>v.code.id===c.code),article=entry.code.articles.find(a=>a.id===c.article);
 if(!c.real)article.paragraphs=c.paragraphs.map(p=>({runs:typeof p==='string'?[{text:p,deleted:false}]:structuredClone(p)}));
 entry.sha256=sha256(JSON.stringify(entry.code));return copy;
}
const targets=rows=>[...new Set(rows.flatMap(o=>o.resolution.status==='resolved'&&o.classification==='A'?o.resolution.targets.map(t=>t.codeId+'/'+t.articleId):[]))].sort();
export function runCase(corpus,c,{extract=extractRemissions,eligible=applyEligibility}={}){
 const copy=caseCorpus(corpus,c),extraction=extract(copy,{selected:[c.code]}),occurrences=extraction.occurrences.filter(o=>o.source.articleId===c.article&&(!c.literal||o.location.text===c.literal));
 const gate=eligible(copy,{occurrences}),article=copy.collections.find(v=>v.code.id===c.code).code.articles.find(a=>a.id===c.article);
 return {id:c.id,source:{code:c.code,article:c.article,synthetic:!c.real},paragraphs:article.paragraphs,expected:c.expected,justification:c.justification,rawTargets:targets(occurrences),eligibleTargets:targets(gate.accepted),occurrences,decisions:gate.decisions};
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href){
 let implementation={};
 if(process.argv[3]){
  const base=pathToFileURL(resolve(process.argv[3])+'/');
  const {extractRemissions:extract}=await import(new URL('scripts/remissions/extract.mjs',base));
  const {applyEligibility:eligible}=await import(new URL('scripts/remissions/eligibility.mjs',base));implementation={extract,eligible};
 }
 const corpus=await corpusFromBuild(),rows=cases.map(c=>runCase(corpus,c,implementation));
 await writeFile(process.argv[2]||'test-results/remissions-adversarial.json',JSON.stringify(rows,null,2));
 console.log(JSON.stringify(rows.map(r=>({id:r.id,raw:r.rawTargets,eligible:r.eligibleTargets,expected:r.expected})),null,2));
}
