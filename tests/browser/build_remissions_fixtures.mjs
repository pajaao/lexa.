// Test-only copies of editions; no writes to legal source files.
import {stagePages} from '../../scripts/build-pages.mjs';
import {buildPackage} from '../../scripts/build.mjs';
import {writeFile,rm} from 'node:fs/promises';import {join} from 'node:path';
const destination=process.argv[2];if(!destination)throw Error('Missing temporary output directory');
const p=await buildPackage(),norms=p.manifest.collections.map(c=>JSON.parse(p.files.get(c.file)));
const v1=await stagePages(join(destination,'v1'),{remissions:true});
const copy=structuredClone(norms);copy.find(c=>c.id==='civil').articles.find(a=>a.id==='397').paragraphs[0].runs[0].text+=' (fixture de edição; não publicado)';
const v2=await stagePages(join(destination,'v2'),{remissions:true,norms:copy});
await stagePages(join(destination,'disabled'));
for(const name of ['v1','v2','disabled'])await rm(join(destination,name,'sources'),{recursive:true,force:true});
await writeFile(join(destination,'meta.json'),JSON.stringify({v1:v1.manifest,v2:v2.manifest}));
