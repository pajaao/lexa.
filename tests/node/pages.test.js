import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,readFile,readdir,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {createHash} from 'node:crypto';
import {stagePages} from '../../scripts/build-pages.mjs';

test('pacote publicado inclui HTML, ícones e PDFs íntegros',async()=>{
 const output=await mkdtemp(join(tmpdir(),'lexa-pages-'));
 try{
  await stagePages(output);
  assert.deepEqual((await readdir(output)).sort(),['.nojekyll','apple-touch-icon.png','favicon.ico','favicon.svg','icon-192.png','icon-512.png','icon-maskable-512.png','index.html','manifest.webmanifest','sources','sw.js']);
  const archive=JSON.parse(await readFile(new URL('../../sources/manifest.json',import.meta.url),'utf8'));
  const sumulas=JSON.parse(await readFile(new URL('../../sources/sumulas-manifest.json',import.meta.url),'utf8'));
  assert.equal((await readdir(join(output,'sources'))).length,Object.keys(archive).length+1);
  for(const source of [...Object.values(archive),sumulas]){
   const bytes=await readFile(join(output,source.pdf));
   assert.equal(createHash('sha256').update(bytes).digest('hex'),source.sha256);
  }
  const html=await readFile(join(output,'index.html'),'utf8');
  assert.match(html,/<style>/);
  assert.doesNotMatch(html,/<(?:script|link)[^>]+(?:src|href)="\//);
  assert.match(html,/Confira a edição indicada e a fonte oficial/);
  assert.match(html,/Idealizado por João Antônio, UFRN/);
  for(const file of ['favicon.svg','favicon.ico','apple-touch-icon.png']){
   const bytes=await readFile(join(output,file));
   assert.deepEqual(bytes,await readFile(new URL('../../public/'+file,import.meta.url)));
  }
  const manifest=JSON.parse(await readFile(join(output,'manifest.webmanifest'),'utf8'));
  assert.equal(manifest.scope,'./');assert.equal(manifest.start_url,'./');assert.equal(manifest.display,'standalone');
  for(const icon of manifest.icons){
   const bytes=await readFile(join(output,icon.src));
   assert.equal(bytes.subarray(1,4).toString(),'PNG');
   const [width,height]=icon.sizes.split('x').map(Number);
   assert.equal(bytes.readUInt32BE(16),width);assert.equal(bytes.readUInt32BE(20),height);
  }
  const worker=await readFile(join(output,'sw.js'),'utf8');
  assert.match(worker,/const VERSION = '[a-f0-9]{64}'/);
  assert.doesNotMatch(worker,/__LEXA_VERSION__|__LEXA_HTML_SHA256__/);
  assert.ok(worker.includes(createHash('sha256').update(html).digest('hex')));
  assert.match(html,/rel="manifest" href="\.\/manifest.webmanifest"/);
  assert.match(html,/rel="icon" href="\.\/favicon\.svg\?v=1"/);
 }finally{await rm(output,{recursive:true,force:true});}
});
