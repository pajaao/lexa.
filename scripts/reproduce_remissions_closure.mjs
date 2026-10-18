// Reproduction only: calls the approved audit unchanged into two external dirs.
// The Python verifier is separate and never imports these pipeline functions.
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import {resolve,join} from 'node:path';import {createHash} from 'node:crypto';
import {generate} from './audit-remissions/run.mjs';
import {buildPackage} from './build.mjs';import {buildRemissions} from './remissions/build-resource.mjs';
const root=resolve(process.argv[2]||'/tmp/lexa-closure-reproduction');
const approved=resolve('docs/remissoes/fase-1a-2');
if(root===approved||root.startsWith(approved+'/'))throw Error('Use external output directories; original inventory is read-only.');
await mkdir(root,{recursive:true});
await generate(join(root,'run-a'));await generate(join(root,'run-b'));
const names=['arestas.json','arestas.csv','rejeicoes-amostra.json','revisao-humana.csv','manifesto.json'];
const digest=b=>createHash('sha256').update(b).digest('hex');
const comparison=[];
for(const name of names){const [a,b,original]=await Promise.all([readFile(join(root,'run-a',name)),readFile(join(root,'run-b',name)),readFile(join(approved,name))]);comparison.push({file:name,sha256:digest(original),runA:digest(a),runB:digest(b),identical:a.equals(b)&&a.equals(original)});}
const pack=await buildPackage(),corpus={collections:pack.manifest.collections.map(c=>({code:JSON.parse(pack.files.get(c.file)),sha256:c.sha256}))},built=buildRemissions(corpus);
// Full rejection population is supplementary pipeline evidence, not independent ground truth.
await writeFile(join(root,'snapshot.json'),JSON.stringify({corpus,audit:built.audit}));
await writeFile(join(root,'reproduction.json'),JSON.stringify({runs:2,files:comparison,ok:comparison.every(r=>r.identical),snapshotDependency:'Universe and metadata supplied by the unchanged pipeline.'},null,2));
if(comparison.some(r=>!r.identical))throw Error('Reproduction differs from approved artifacts');
console.log('Two runs identical to each other and to all five approved artifacts.');
