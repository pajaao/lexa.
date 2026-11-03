import {createHash} from 'node:crypto';
import {buildPackage,sha256} from './build.mjs';
import {cp, mkdir, readFile, rm, writeFile} from 'node:fs/promises';
import {resolve, dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
const root=fileURLToPath(new URL('../',import.meta.url));

export async function stagePages(destination=resolve(root,'dist'),options={}) {
 if((options.legislativeHistoryDemo||options.legislativeHistoryPilot||options.legislativeHistorySimple||options.previousWordingsCandidate||options.amendmentsCandidate)&&resolve(destination)===resolve(root,'dist'))throw new Error('Demonstração não pode substituir o pacote de publicação.');
 const archive=JSON.parse(await readFile(resolve(root,'sources/manifest.json'),'utf8'));
 const sumulas=JSON.parse(await readFile(resolve(root,'sources/sumulas-manifest.json'),'utf8'));
 const documents=[...Object.values(archive),sumulas];
 // Publish an explicit allowlist, never the checkout, automation or raw captures.
 for(const source of documents){
  if(!/^sources\/[A-Za-z0-9_.-]+\.pdf$/.test(source.pdf))throw new Error('Caminho de PDF inválido');
 }
 const {html,files:dataFiles,manifest}=await buildPackage(options);
 await rm(destination,{recursive:true,force:true});
 await mkdir(destination,{recursive:true});
 await writeFile(resolve(destination,'index.html'),html);
 const files=['favicon.svg','favicon.ico','apple-touch-icon.png','manifest.webmanifest','icon-192.png','icon-512.png','icon-maskable-512.png'];
 const worker=await readFile(resolve(root,'src/sw.js'),'utf8');
 const roles=new Map([[manifest.history.file,{role:'history'}],...manifest.collections.flatMap(code=>[[code.file,{role:'collection',codeId:code.id}],[code.search.file,{role:'search',codeId:code.id}]])]);
 const integrity=[{file:'index.html',sha256:sha256(html)}];
 const hash=createHash('sha256').update(html).update(worker);
 for(const [file,bytes] of dataFiles){await mkdir(dirname(resolve(destination,file)),{recursive:true});await writeFile(resolve(destination,file),bytes);integrity.push({file,sha256:sha256(bytes),...(roles.get(file)||(manifest.amendments&&/^data\/ec-(\d+)\./.test(file)?{role:'amendment',codeId:'ec-'+/^data\/ec-(\d+)\./.exec(file)[1]}:manifest.amendments&&/^data\/ec-(index|links)\./.test(file)?{role:'amendment-index'}:null))});hash.update(file).update(bytes);}
 for(const file of files){const bytes=await readFile(resolve(root,'public',file));hash.update(file).update(bytes);integrity.push({file,sha256:sha256(bytes)});await writeFile(resolve(destination,file),bytes);}
 await writeFile(resolve(destination,'sw.js'),worker.replace('__LEXA_VERSION__',hash.digest('hex')).replace('__LEXA_INTEGRITY_MANIFEST__',JSON.stringify(integrity)).replace('__LEXA_COLLECTION_FILES__',JSON.stringify(manifest.collections.map(code=>({id:code.id,name:code.name,file:code.file,search:code.search.file})))));
 await writeFile(resolve(destination,'.nojekyll'),'');
 for(const {pdf} of documents){
  const target=resolve(destination,pdf);
  await mkdir(dirname(target),{recursive:true});
  await cp(resolve(root,pdf),target);
 }
 console.log(`Pacote do GitHub Pages: shell, ${dataFiles.size} arquivos de dados e ${documents.length} PDFs.`);
}

if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 await stagePages();
}
