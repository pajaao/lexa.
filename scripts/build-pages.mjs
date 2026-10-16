import {buildHtml} from './build.mjs';
import {cp, mkdir, readFile, rm, writeFile} from 'node:fs/promises';
import {resolve, dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
const root=fileURLToPath(new URL('../',import.meta.url));

export async function stagePages(destination=resolve(root,'dist')) {
 const archive=JSON.parse(await readFile(resolve(root,'sources/manifest.json'),'utf8'));
 const sumulas=JSON.parse(await readFile(resolve(root,'sources/sumulas-manifest.json'),'utf8'));
 const documents=[...Object.values(archive),sumulas];
 // Publish an explicit allowlist, never the checkout, automation or raw captures.
 for(const source of documents){
  if(!/^sources\/[A-Za-z0-9_.-]+\.pdf$/.test(source.pdf))throw new Error('Caminho de PDF inválido');
 }
 const html=await buildHtml();
 await rm(destination,{recursive:true,force:true});
 await mkdir(destination,{recursive:true});
 await writeFile(resolve(destination,'index.html'),html);
 for(const file of ['favicon.svg','favicon.ico','apple-touch-icon.png'])await cp(resolve(root,'public',file),resolve(destination,file));
 await writeFile(resolve(destination,'.nojekyll'),'');
 for(const {pdf} of documents){
  const target=resolve(destination,pdf);
  await mkdir(dirname(target),{recursive:true});
  await cp(resolve(root,pdf),target);
 }
 console.log(`Pacote do GitHub Pages: HTML autocontido e ${documents.length} PDFs.`);
}

if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 await stagePages();
}
