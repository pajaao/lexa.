import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,readFile,readdir,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {createHash} from 'node:crypto';
import {stagePages} from '../../scripts/build-pages.mjs';
import {collections} from '../../src/data.js';

test('pacote publicado inclui HTML, ícones e PDFs íntegros',async()=>{
 const output=await mkdtemp(join(tmpdir(),'lexa-pages-'));
 try{
  await stagePages(output);
  assert.deepEqual((await readdir(output)).sort(),['.nojekyll','app','apple-touch-icon.png','catalog.json','data','favicon.ico','favicon.svg','icon-192.png','icon-512.png','icon-maskable-512.png','index.html','manifest.webmanifest','sources','sw.js']);
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
  const catalog=JSON.parse(await readFile(join(output,'catalog.json'),'utf8'));
  assert.equal(catalog.collections.length,14);
  for(const spec of [...catalog.collections,catalog.history]){
   const bytes=await readFile(join(output,spec.file));
   assert.equal(createHash('sha256').update(bytes).digest('hex'),spec.sha256);
   assert.ok(spec.file.includes(spec.sha256));
   assert.ok(worker.includes(spec.sha256));
   if(spec.articleCount){
    const payload=JSON.parse(bytes),original=collections.find(code=>code.id===spec.id);
    assert.equal(payload.articles.length,spec.articleCount);
    assert.deepEqual(payload.sections,original.sections);
    const fields=['id','scope','number','rangeEnd','title','status','paragraphs','notes','page','endPage'];
    assert.deepEqual(payload.articles.map(article=>fields.map(key=>article[key])),original.articles.map(article=>fields.map(key=>article[key])));
   }
  }
  const integrity=JSON.parse(worker.match(/const INTEGRITY = ([^;]+);/)[1]);
  for(const spec of integrity)assert.equal(createHash('sha256').update(await readFile(join(output,spec.file))).digest('hex'),spec.sha256);
  const namespace=(await readdir(join(output,'app')))[0];
  for(const file of await readdir(join(output,'app',namespace))){
   if(['catalog.js','collections.js'].includes(file))continue;
   assert.equal(await readFile(join(output,'app',namespace,file),'utf8'),await readFile(new URL('../../src/'+file,import.meta.url),'utf8'));
  }
  assert.match(worker,/const VERSION = '[a-f0-9]{64}'/);
  assert.doesNotMatch(worker,/__LEXA_VERSION__|__LEXA_INTEGRITY_MANIFEST__/);
  assert.ok(worker.includes(createHash('sha256').update(html).digest('hex')));
  assert.match(html,/rel="manifest" href="\.\/manifest.webmanifest"/);
  assert.match(html,/rel="icon" href="\.\/favicon\.svg\?v=1"/);
 }finally{await rm(output,{recursive:true,force:true});}
});

test('alterar só CSS altera o shell e preserva nomes e bytes de todos os JSON',async()=>{
 const {buildPackage,sha256}=await import('../../scripts/build.mjs');
 const before=await buildPackage();
 const after=await buildPackage({css:(await readFile(new URL('../../src/styles.css',import.meta.url),'utf8'))+'\n/* mudança apenas visual */'});
 assert.notEqual(sha256(before.html),sha256(after.html));
 assert.deepEqual([...before.files],[...after.files]);
 assert.deepEqual(before.manifest,after.manifest);
});
