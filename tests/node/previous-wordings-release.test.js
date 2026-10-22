import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {buildPackage} from '../../scripts/build.mjs';
import {checkRelease} from '../../scripts/previous-wordings-release.mjs';
import {previousRecords,readingArticle} from '../../src/legislative-history-model.js';
import {officialImported} from '../../data/official/legislation.js';
import {legislativeHistoryData as publishedPilot} from '../../src/legislative-history-data.js';
import {legislativeHistoryData as originalPilot} from '../fixtures/legislative-history-pilot.js';

const root=new URL('../../',import.meta.url);
async function inputs(){
 const manifest=JSON.parse(await readFile(new URL('data/previous-wordings/release.json',root),'utf8'));
 return [manifest,await readFile(new URL('data/previous-wordings/candidate.json',root)),await readFile(new URL('data/official/legislation.js',root)),await readFile(new URL(manifest.validationReport,root))];
}

test('bloqueio do novo lote preserva os dois caputs anteriores já publicados sem mudar aprovação',()=>{
 assert.equal(publishedPilot.records.length,3);
 assert.ok(publishedPilot.records.every(r=>r.review.status==='approved'));
 assert.deepEqual(previousRecords(publishedPilot,'penal','215').map(r=>r.id),['penal-215-caput-01','penal-215-caput-02']);
 assert.ok(!publishedPilot.records.some(r=>r.review.status==='pending'));
 for(const record of publishedPilot.records){
  const original=originalPilot.records.find(r=>r.id===record.id);
  for(const key of ['text','notes','reference','source','review'])assert.deepEqual(record[key],original[key]);
 }
});

test('publicação fica bloqueada sem decisões expressas e não transforma pending em homologado',async()=>{
 const args=await inputs();
 assert.deepEqual(checkRelease({...args[0],publicationAuthorized:false},...args.slice(1)).records,[]);
 assert.throws(()=>checkRelease({...args[0],publicationAuthorized:true},...args.slice(1)),/decisões expressas/);
 const candidate=checkRelease(...args,{candidate:true});
 assert.equal(candidate.records.length,1679);
 assert.ok(candidate.records.every(r=>r.review.status==='pending'));
 const authorized=checkRelease({...args[0],publicationAuthorized:true,governanceDecision:'decision:test-governance',riskReviewDecision:'decision:test-risk',publicationDecision:'decision:test-launch'},...args.slice(1));
 assert.equal(previousRecords(authorized,'penal','215').length,5);
 assert.ok(authorized.records.every(r=>r.review.status==='pending'));
 assert.equal(previousRecords({records:candidate.records},'penal','215').length,0);
});

test('manifesto rejeita adulteração e exclusões CPP não entram na candidata',async()=>{
 const args=await inputs();
 assert.throws(()=>checkRelease(args[0],Buffer.from('{}'),args[2],args[3]),/Integridade/);
 assert.throws(()=>checkRelease({...args[0],recordCount:1},...args.slice(1)),/Seleção/);
 const data=checkRelease(...args,{candidate:true});
 assert.ok(!data.records.some(r=>r.codeId==='cpp'&&r.evidence.block>=1559&&r.evidence.block<1812));
});

test('candidata conserva a PWA e todos os arquivos legislativos do build normal',async()=>{
 const candidate=await buildPackage({previousWordingsCandidate:true});
 const normal=await buildPackage();
 assert.deepEqual(candidate.manifest,normal.manifest);
 for(const [path,bytes] of normal.files)if(path.startsWith('data/')||path==='catalog.json')assert.equal(candidate.files.get(path),bytes);
 const moduleFor=(bundle,name)=>[...bundle.files].find(([p])=>p.endsWith('/'+name))[1];
 assert.ok(moduleFor(candidate,'pwa.js').includes('navigator'));
 assert.ok(!moduleFor(candidate,'pwa.js').includes('export function setupPwa(){}'));
 assert.ok(moduleFor(candidate,'legislative-history-data.js').includes('cpp-simple-'));
 const release=(await inputs())[0];
 assert.equal(moduleFor(normal,'legislative-history-data.js').includes('cpp-simple-'),release.publicationAuthorized);
 await assert.rejects(buildPackage({previousWordingsCandidate:true,legislativeHistorySimple:true}),/não pode misturar/);
});

test('leitor não altera fontes ou parágrafos sem risco e separa risco independentemente da disponibilidade do painel',async()=>{
 const candidate=checkRelease(...await inputs(),{candidate:true});
 const snapshot=JSON.stringify(officialImported);
 let removed=0;
 for(const [codeId,code] of Object.entries(officialImported))for(const article of code.articles){
  const displayed=readingArticle(candidate,codeId,article);
  for(const paragraph of article.paragraphs){
   if(paragraph.runs.every(r=>!r.deleted))assert.ok(displayed.paragraphs.includes(paragraph));
   if(!displayed.paragraphs.includes(paragraph)){
    removed++;
    assert.ok(paragraph.runs.some(r=>r.deleted));
    assert.ok(displayed.paragraphs.every(p=>p.runs.every(r=>!r.deleted)));
   }
  }
 }
 assert.ok(removed>0);
 assert.equal(JSON.stringify(officialImported),snapshot);
});
