// Explicit local fixture/analysis build. Never the default publication target.
import {mkdir,writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {stagePages} from './build-pages.mjs';
const destination=resolve('test-results/remissions-experiment');
const result=await stagePages(destination,{remissions:true});
await mkdir('test-results',{recursive:true});
await writeFile('test-results/remissions-audit.json',JSON.stringify(result.remissionsAudit,null,2));
console.log(`Build experimental: ${destination}; auditoria fora da pasta publicada.`);
