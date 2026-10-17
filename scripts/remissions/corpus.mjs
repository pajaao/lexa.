// Uses exactly the build's chosen legal editions, without staging/publishing files.
import {buildPackage} from '../build.mjs';
export async function loadCorpus(){
 const {manifest,files}=await buildPackage();
 return {collections:manifest.collections.map(spec=>({sha256:spec.sha256,code:JSON.parse(files.get(spec.file))}))};
}
