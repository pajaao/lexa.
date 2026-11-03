import {amendmentAssets} from './amendments.mjs';
import {releaseData} from './previous-wordings-release.mjs';
import {readFile,readdir} from 'node:fs/promises';
import {recentTextUpdates} from './recent-updates.mjs';
import {createHash} from 'node:crypto';
import {catalog} from '../src/catalog.js';
import {createSearchIndex} from '../src/search-index.js';
import {imported} from '../data/archive/legislation.js';
import {officialImported} from '../data/official/legislation.js';
import {sumulas} from '../data/archive/sumulas.js';
import {officialSumulas} from '../data/official/sumulas.js';
import {updateHistory} from '../data/history/legislation.js';
import {sumulaUpdates} from '../data/history/sumulas.js';
const root=new URL('../',import.meta.url);
export const sha256=bytes=>createHash('sha256').update(bytes).digest('hex');
export async function buildPackage({css:cssOverride,history:historyOverride,legislativeHistoryDemo=false,legislativeHistoryPilot=false,legislativeHistorySimple=false,previousWordingsCandidate=false,amendmentsCandidate=false,amendmentsDirectory}={}){
 const files=new Map();
 function asset(id,value){
  const bytes=JSON.stringify(value),sha=sha256(bytes),file=`data/${id}.${sha}.json`;
  files.set(file,bytes);return {file,sha256:sha,bytes:Buffer.byteLength(bytes)};
 }
 const history=historyOverride??[...updateHistory,...sumulaUpdates];
 const norms=[...catalog.map(code=>({...code,...(officialImported[code.id]||imported[code.id])})),...(officialSumulas.length?officialSumulas:sumulas)];
 const metadata=norms.map(norm=>{
  const {articles,sections,introductions,...fields}=norm;
  return {...fields,articleCount:articles.length,...asset(norm.id,norm),search:asset('search-'+norm.id,createSearchIndex(norm)),changedArticleIds:[...new Set(history.filter(event=>event.codeId===norm.id).flatMap(event=>event.changes.map(change=>change.articleId)))]};
 });
 const recentUpdates=recentTextUpdates(history.filter(event=>metadata.some(code=>code.id===event.codeId)));
 const manifest={collections:metadata,history:asset('history',history),recentUpdates};
 manifest.offlineBytes=metadata.reduce((sum,code)=>sum+code.bytes+code.search.bytes,manifest.history.bytes);
 const amendments=await amendmentAssets({candidate:amendmentsCandidate,asset,directory:amendmentsDirectory});
 if(amendments){manifest.amendments=amendments;manifest.offlineBytes+=[...files].filter(([name])=>name.startsWith('data/ec-')).reduce((sum,[,bytes])=>sum+Buffer.byteLength(bytes),0);}
 files.set('catalog.json',JSON.stringify(manifest));
 const [template,originalCss]=await Promise.all(['index.html','styles.css'].map(path=>readFile(new URL('src/'+path,root),'utf8')));
 const css=cssOverride??originalCss;
 const names=(await readdir(new URL('src/',root))).filter(name=>name.endsWith('.js')&&name!=='sw.js').sort();
 const modules=new Map(await Promise.all(names.map(async name=>[name,await readFile(new URL('src/'+name,root),'utf8')])));
 // Native ESM keeps imports, exports, comments and string literals intact. Only
 // the Node data adapter is generated for the browser; no JS source rewriting.
 modules.set('collections.js',`export const initialCatalog=${JSON.stringify(manifest)};
export const collections=initialCatalog.collections.map(code=>({...code,articles:[],sections:[],loaded:false}));
export const codes=collections.filter(code=>code.kind!=='sumulas');`);
 modules.set('catalog.js',"export {codes as catalog} from './collections.js';");
 if(previousWordingsCandidate&&(legislativeHistoryDemo||legislativeHistoryPilot||legislativeHistorySimple))throw new Error('Candidata não pode misturar dados experimentais.');
 const released=await releaseData({candidate:previousWordingsCandidate});
 if(released.records.length||previousWordingsCandidate)modules.set('legislative-history-data.js','export const legislativeHistoryData='+JSON.stringify(released)+';');
 if(legislativeHistorySimple&&(legislativeHistoryDemo||legislativeHistoryPilot))throw new Error('Escolha apenas uma prévia.');
 if(legislativeHistorySimple){
  const fixture=JSON.parse(await readFile(new URL('tests/fixtures/previous-wordings-simple.json',root),'utf8'));
  if(!fixture.preview||fixture.records.some(r=>r.review?.status!=='pending'||r.wording?.status!=='previous'))throw new Error('Prévia HTML inválida.');
  modules.set('legislative-history-data.js','export const legislativeHistoryData='+JSON.stringify(fixture)+';');
  modules.set('pwa.js',"export function setupPwa(){}");
 }
 if(legislativeHistoryDemo&&legislativeHistoryPilot)throw new Error("Escolha apenas uma prévia.");
 if(legislativeHistoryDemo||legislativeHistoryPilot){
  modules.set('legislative-history-data.js',await readFile(new URL(legislativeHistoryPilot?'tests/fixtures/legislative-history-pilot.js':'tests/fixtures/legislative-history-demo.js',root),'utf8'));
  if(legislativeHistoryPilot){
   const batch=JSON.parse(await readFile(new URL('tests/fixtures/legislative-history-batch.json',root),'utf8'));
   modules.set('legislative-history-data.js',modules.get('legislative-history-data.js')+'\nlegislativeHistoryData.records.push(...'+JSON.stringify(batch.records)+');');
   const previous=JSON.parse(await readFile(new URL('tests/fixtures/previous-wordings-html.json',root),'utf8'));
   modules.set('legislative-history-data.js',modules.get('legislative-history-data.js')+'\nlegislativeHistoryData.records.push(...'+JSON.stringify(previous.records)+');');
   const html=JSON.parse(await readFile(new URL('tests/fixtures/legislative-history-html.json',root),'utf8'));
   modules.set('legislative-history-data.js',modules.get('legislative-history-data.js')+'\nlegislativeHistoryData.records.push(...'+JSON.stringify(html.records)+');');
  }
  modules.set('pwa.js',"export function setupPwa(){}");
 }
 const moduleHash=createHash('sha256');
 for(const [name,source] of modules)moduleHash.update(name+'\0').update(source+'\0');
 const namespace='app/'+moduleHash.digest('hex')+'/';
 for(const [name,source] of modules)files.set(namespace+name,source);
 function slot(text,needle,value){
  if(text.split(needle).length!==2)throw new Error('Marcador de template ausente ou repetido: '+needle);
  return text.replace(needle,()=>value);
 }
 if(css.toLowerCase().includes('</style'))throw new Error('Estilo incompatível com incorporação HTML');
 let html=slot(template,'<link rel="stylesheet" href="./styles.css">',`<style>${css}</style>`);
 const preloads=[...modules.keys()].filter(name=>!['amendments.js','amendment-reading.js'].includes(name)).map(name=>`<link rel="modulepreload" href="./${namespace+name}">`).join('');
 html=slot(html,'<script type="module" src="./app.js"></script>',preloads+`<script type="module" src="./${namespace}app.js"></script>`);
 return {html,files,manifest};
}
export async function buildHtml(){return (await buildPackage()).html;}
