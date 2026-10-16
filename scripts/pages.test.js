import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,readFile,readdir,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {createHash} from 'node:crypto';
import {stagePages} from './build-pages.mjs';

test('pacote publicado contém apenas HTML, configuração estática e PDFs íntegros',async()=>{
 const output=await mkdtemp(join(tmpdir(),'lexa-pages-'));
 try{
  await stagePages(output);
  assert.deepEqual((await readdir(output)).sort(),['.nojekyll','index.html','sources']);
  const archive=JSON.parse(await readFile(new URL('../sources/manifest.json',import.meta.url),'utf8'));
  const sumulas=JSON.parse(await readFile(new URL('../sources/sumulas-manifest.json',import.meta.url),'utf8'));
  assert.equal((await readdir(join(output,'sources'))).length,7);
  for(const source of [...Object.values(archive),sumulas]){
   const bytes=await readFile(join(output,source.pdf));
   assert.equal(createHash('sha256').update(bytes).digest('hex'),source.sha256);
  }
  const html=await readFile(join(output,'index.html'),'utf8');
  assert.match(html,/<style>/);
  assert.doesNotMatch(html,/<(?:script|link)[^>]+(?:src|href)="\//);
  assert.match(html,/Confira a edição indicada e a fonte oficial/);
 }finally{await rm(output,{recursive:true,force:true});}
});
