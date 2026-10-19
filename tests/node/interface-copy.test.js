import test from 'node:test';import assert from 'node:assert/strict';
import {loadFailureText,offlineStatusText} from '../../src/interface-copy.js';
test('falhas conhecidas de integridade e dados incompletos não culpam a conexão',()=>{
 assert.match(loadFailureText(new Error('O arquivo não corresponde à edição publicada.')),/não corresponde à edição publicada/);
 for(const message of ['Coleção incompleta.','Índice incompleto.'])assert.match(loadFailureText(new Error(message)),/incompletos/);
 assert.doesNotMatch(loadFailureText(new TypeError('Failed to fetch')),/Verifique a conexão/);
 assert.match(loadFailureText(new Error('unknown')),/depende dos conteúdos já armazenados/);
});
test('mensagem offline parcial nunca declara a biblioteca completa disponível',()=>{
 assert.match(offlineStatusText(false,true),/limitado aos conteúdos armazenados/);
 assert.match(offlineStatusText(false,false),/^Você está offline/);
 assert.doesNotMatch(offlineStatusText(false,true),/Biblioteca completa desta edição disponível/);
 assert.match(offlineStatusText(true,false),/Biblioteca completa desta edição disponível offline/);
});
