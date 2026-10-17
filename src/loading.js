import {collections} from './data.js';
import {prepareCollection} from './collection-model.js';

const pendingCollections=new Map(),pendingSearch=new Map();
let pendingHistory;
async function fetchVerifiedJson(spec){
 const response=await fetch(new URL(spec.file,document.baseURI),{cache:'default'});
 if(!response.ok)throw new Error('Não foi possível carregar esta edição.');
 const bytes=await response.arrayBuffer();
 const hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),byte=>byte.toString(16).padStart(2,'0')).join('');
 if(hash!==spec.sha256)throw new Error('O arquivo não corresponde à edição publicada.');
 return JSON.parse(new TextDecoder().decode(bytes));
}
export function loadCollection(code){
 if(code.loaded)return Promise.resolve(code);
 if(!pendingCollections.has(code.id)){
  const task=fetchVerifiedJson(code).then(content=>{
   if(content.id!==code.id||content.articles.length!==code.articleCount)throw new Error('Coleção incompleta.');
   Object.assign(code,prepareCollection(content));return code;
  }).catch(error=>{pendingCollections.delete(code.id);throw error;});
  pendingCollections.set(code.id,task);
 }
 return pendingCollections.get(code.id);
}
export async function loadCollections(selected=collections){
 // Limit downloads and parsing so search does not monopolize the browser.
 let next=0;
 await Promise.all(Array.from({length:Math.min(3,selected.length)},async()=>{
  while(next<selected.length)await loadCollection(selected[next++]);
 }));
}
export function loadHistory(){
 if(!pendingHistory)pendingHistory=fetchVerifiedJson(initialCatalog.history).catch(error=>{pendingHistory=undefined;throw error;});
 return pendingHistory;
}

export function loadSearchIndex(code){
 if(code.searchIndex)return Promise.resolve(code.searchIndex);
 if(!pendingSearch.has(code.id))pendingSearch.set(code.id,fetchVerifiedJson(code.search).then(index=>{
  if(index.id!==code.id||index.articles.length!==code.articleCount)throw new Error('Índice incompleto.');
  code.searchIndex=index;return index;
 }).catch(error=>{pendingSearch.delete(code.id);throw error;}));
 return pendingSearch.get(code.id);
}
export async function loadSearchIndexes(selected=collections){
 let next=0;
 await Promise.all(Array.from({length:Math.min(3,selected.length)},async()=>{
  while(next<selected.length)await loadSearchIndex(selected[next++]);
 }));
}
