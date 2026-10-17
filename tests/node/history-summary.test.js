import test from 'node:test';
import assert from 'node:assert/strict';
import {historySummary} from '../../src/history.js';
test('histórico distingue referências iniciais, normas e versões posteriores',()=>{
 const baseline={codeId:'cf',kind:'baseline',capturedAt:'2026-10-16T12:00:00Z',changes:[]};
 assert.deepEqual(historySummary([baseline]),{since:baseline.capturedAt,norms:1,versions:0,changes:0});
 assert.deepEqual(historySummary([baseline,{...baseline,codeId:'civil',capturedAt:'2026-10-15T12:00:00Z'},{...baseline,kind:'text',changes:[{}]}]),{since:'2026-10-15T12:00:00Z',norms:2,versions:1,changes:1});
 assert.deepEqual(historySummary([]),{since:null,norms:0,versions:0,changes:0});
});
