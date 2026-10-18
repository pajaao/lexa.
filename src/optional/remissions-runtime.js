// Internal opt-in API; no reader/app call site, no automatic download.
import {initialCatalog} from '../collections.js';
import {fetchVerifiedJson} from '../loading.js';
import {createRemissionsLoader} from './remissions.js';
export const loadRemissions=createRemissionsLoader({catalog:initialCatalog,fetchJSON:fetchVerifiedJson});
