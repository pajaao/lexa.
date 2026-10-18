import {validateRemissions,relationStore} from './remissions-contract.js';
export function createRemissionsLoader({catalog,fetchJSON}){
 let pending;
 return function loadRemissions(){
  if(!catalog?.remissions)return Promise.resolve(null);
  if(!pending)pending=Promise.resolve().then(()=>fetchJSON(catalog.remissions)).then(index=>validateRemissions(index,catalog.remissions,catalog.collections)).then(relationStore).catch(error=>{pending=undefined;throw error;});
  return pending;
 };
}
