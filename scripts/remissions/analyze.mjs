#!/usr/bin/env node
// Explicit, opt-in experiment. Not imported by either production build script.
import {readFile,writeFile,mkdir} from 'node:fs/promises';
import {resolve,relative} from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {performance} from 'node:perf_hooks';
import {gzipSync} from 'node:zlib';
import {cpus,platform,arch} from 'node:os';
import {loadCorpus} from './corpus.mjs';
import {extractRemissions,sha256,RULES_SHA256} from './extract.mjs';
import {compactBundle,relationGraph} from './graph.mjs';
import {evaluateSample} from './evaluate.mjs';
import {simulateEditions} from './simulate.mjs';
const root=new URL('../../',import.meta.url),rootPath=fileURLToPath(root),args=process.argv.slice(2);
const outputFlag=args.indexOf('--output'),output=resolve(outputFlag>=0?args[outputFlag+1]:'test-results/remissions');
const inside=relative(rootPath,output).replaceAll('\\','/');
if(['src','data','public','sources','dist','monitor'].some(name=>inside===name||inside.startsWith(name+'/')))throw Error('Analysis output must not write legal or published files.');
const baselineFlag=args.indexOf('--baseline');
const baseline=baselineFlag>=0?JSON.parse(await readFile(args[baselineFlag+1],'utf8')):null;
const corpus=await loadCorpus(),before=sha256(JSON.stringify(corpus));
const primary=['civil','cf','cpc','licitacoes'],timings={primary:[],all:[]};
let all;
for(const [name,selected] of [['primary',primary],['all',undefined]])for(let i=0;i<5;i++){
 const start=performance.now(),data=extractRemissions(corpus,{selected});timings[name].push(performance.now()-start);if(name==='all')all=data;
}
const rebuilt=extractRemissions(corpus);
if(JSON.stringify(rebuilt)!==JSON.stringify(all))throw Error('Nondeterministic extraction.');
if(sha256(JSON.stringify(corpus))!==before)throw Error('Extraction mutated the legal corpus.');
const fixtureRoot=new URL('../../tests/fixtures/remissions/',import.meta.url),sampling=JSON.parse(await readFile(new URL('sampling.json',fixtureRoot),'utf8'));
const evaluations={};
for(const name of ['phase0','holdout']){
 const bytes=await readFile(new URL(name+'.json',fixtureRoot));
 const expectedHash=name==='phase0'?sampling.trainingSha256:sampling.evaluationSha256;
 if(sha256(bytes)!==expectedHash)throw Error('Frozen sample changed.');
 const sample=JSON.parse(bytes);
 evaluations[name]={phase05:evaluateSample(sample,all.occurrences),...(baseline?{phase0:evaluateSample(sample,baseline.occurrences,{legacy:true})}:{})};
}
const counts=occurrences=>Object.fromEntries('ABCDE'.split('').map(status=>[status,occurrences.filter(o=>o.classification===status).length]));
const bundle=compactBundle(all),bytes=JSON.stringify(bundle),primaryData=extractRemissions(corpus,{selected:primary}),primaryBytes=JSON.stringify(compactBundle(primaryData));
const graph=relationGraph(all),statutory=corpus.collections.filter(c=>c.code.id!=='sv');
const summary={baseCommit:sampling.baseCommit,phase0BaseCommit:'84c5bb5c5e28c08376e0bf40cf3f3f4b4fd783cf',differencesSincePhase0:'none on main at start',implementationCommit:execFileSync('git',['rev-parse','HEAD'],{cwd:rootPath,encoding:'utf8'}).trim(),rulesVersion:all.rules.version,rulesSha256:RULES_SHA256,editionSetSha256:all.editionSetSha256,
 corpus:{sha256:before,collections:statutory.length,entries:statutory.reduce((n,c)=>n+c.code.articles.length,0),primaryEntries:primaryData.diagnostics.scannedArticles,adctEntries:statutory.find(c=>c.code.id==='cf').code.articles.filter(a=>a.scope==='adct').length},
 scan:{classifications:counts(all.occurrences),occurrences:all.occurrences.length,uniqueConnections:graph.edges.length,ownHeadingsRejected:all.diagnostics.ownHeadings,primaryClassifications:counts(primaryData.occurrences),...(baseline?{phase0:{classifications:baseline.classifications,uniqueConnections:baseline.uniqueConnections}}:{})},
 evaluations,simulations:simulateEditions(corpus),determinism:{identicalRebuild:true,corpusUnchanged:true,bundleSha256:sha256(bytes)},
 processing:{node:process.version,platform:platform()+' '+arch(),cpu:cpus()[0]?.model,runs:5,primaryMs:timings.primary,allMs:timings.all,primaryMedianMs:[...timings.primary].sort((a,b)=>a-b)[2],allMedianMs:[...timings.all].sort((a,b)=>a-b)[2],conditions:'In-memory corpus; sequential runs; no CPU throttling; extraction includes SHA256 validation, lexer, resolution, provenance and occurrence IDs. Excludes corpus build, graph, serialization and compression. Not a browser or phone benchmark.',memory:'Not measured: process/heap figures would include the test harness and source corpus; no reliable mobile estimate.'},
 storage:{compactAll:{jsonBytes:Buffer.byteLength(bytes),gzipBytes:gzipSync(bytes).byteLength},compactPrimary:{jsonBytes:Buffer.byteLength(primaryBytes),gzipBytes:gzipSync(primaryBytes).byteLength},conditions:'Compact self-contained provenance/graph bundle; gzip is local Node zlib default, not observed HTTP transfer. Raw legal texts are not duplicated.'}};
await mkdir(output,{recursive:true});
for(const [name,value] of [['results.json',summary],['bundle.json',bundle],['occurrences.json',all],['corpus.json',corpus]])await writeFile(resolve(output,name),JSON.stringify(value,null,name==='results.json'?2:0)+'\n');
console.log(JSON.stringify({output,corpus:summary.corpus,scan:summary.scan,development:summary.evaluations.phase0.phase05,evaluation:summary.evaluations.holdout.phase05,processing:summary.processing,storage:summary.storage},null,2));
