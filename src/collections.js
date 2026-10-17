import {imported} from '../data/archive/legislation.js';
import {officialImported} from '../data/official/legislation.js';
import {sumulas} from '../data/archive/sumulas.js';
import {officialSumulas} from '../data/official/sumulas.js';
import {catalog} from './catalog.js';
import {prepareCollection} from './collection-model.js';
export const codes=catalog.map(code=>prepareCollection({...code,...(officialImported[code.id]||imported[code.id])}));
export const collections=[...codes,...(officialSumulas.length?officialSumulas:sumulas).map(prepareCollection)];

// Browser builds replace this Node-only adapter with the versioned catalog.
export const initialCatalog=null;
