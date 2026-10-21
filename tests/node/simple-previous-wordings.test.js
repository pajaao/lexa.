import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {buildPackage} from '../../scripts/build.mjs';
import {stagePages} from '../../scripts/build-pages.mjs';

test('prévia HTML simples contém somente a nova fixture pending e produção permanece vazia',async()=>{
 const fixture=JSON.parse(await readFile(new URL('../fixtures/previous-wordings-simple.json',import.meta.url),'utf8'));
 assert.ok(fixture.records.length>0);
 assert.ok(fixture.records.every(r=>r.review.status==='pending'&&r.wording.status==='previous'));
 const experimental=await buildPackage({legislativeHistorySimple:true});
 const normal=await buildPackage();
 const moduleFor=result=>[...result.files].find(([name])=>name.endsWith('/legislative-history-data.js'))[1];
 assert.ok(moduleFor(experimental).includes(fixture.records[0].id));
 const release=JSON.parse(await readFile(new URL('../../data/previous-wordings/release.json',import.meta.url),'utf8'));
 assert.equal(moduleFor(normal).includes(fixture.records[0].id),release.publicationAuthorized);
 assert.ok(!moduleFor(experimental).includes('penal-215-caput-01'));
 assert.match([...experimental.files].find(([name])=>name.endsWith('/pwa.js'))[1],/setupPwa\(\)\{\}/);
});

test('prévia HTML simples não pode substituir dist nem misturar os pilotos anteriores',async()=>{
 await assert.rejects(stagePages(undefined,{legislativeHistorySimple:true}),/não pode substituir/);
 await assert.rejects(buildPackage({legislativeHistorySimple:true,legislativeHistoryPilot:true}),/apenas uma/);
});
