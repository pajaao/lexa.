# Histórico legislativo — estrutura inicial

O Histórico legislativo apresenta trechos integrais de partes dos artigos em ordem documental. Não depende de datas de vigência e não substitui o Histórico de versões. A base local contém os três caputs do art. 215, incorporados após confirmação humana expressa do usuário sobre textos, notas, fontes e sequência. Essa autorização não inclui commit, merge ou publicação.

## Prévia local fictícia

Execute `npm run preview:legislative-history` e abra `http://127.0.0.1:3001/#/penal/1`. Se necessário, configure outra porta com `PORT`. A ação “Histórico do artigo” abre os exemplos; o artigo 2 permite verificar o estado sem registros. Os exemplos não correspondem ao conteúdo jurídico do artigo 1, que permanece intacto no leitor. O aviso dentro do painel identifica explicitamente a demonstração fictícia.

O comando gera somente `test-results/legislative-history-demo/`, serve em loopback e desativa o registro de service worker da prévia. Recomenda-se uma porta exclusiva para a prévia, para não compartilhar a origem de outra instalação local. O build normal (`npm run build`) não inclui as fixtures, não pode ser ativado em demonstração por URL ou armazenamento e continua sendo o caminho usado pela publicação. O gerador recusa gravar uma demonstração em `dist/`.

## Contrato mínimo

`src/legislative-history-data.js` exporta `{demo:false, records:[]}`. Cada registro identifica uma parte integralmente documentada:

```js
{
  id: 'identificador-estavel',
  codeId: 'identificador-da-colecao',
  articleId: 'identificador-do-artigo', // mantém namespace, como adct-1
  part: 'caput', // rubric, penalty, paragraph ou article
  text: 'Texto integral do trecho documentado',
  sequence: {order: 1, basis: 'Fundamento documental da posição'},
  reference: null, // referência legislativa opcional
  notes: [], // notas editoriais, separadas do texto
  source: {label: 'Fonte', location: 'Página e localização', url: 'https://…'},
  review: {status: 'pending'} // approved, rejected ou demonstration
}
```

Fonte e referência podem estar ausentes: o painel informa a ausência sem inventar uma origem. Isso é tolerância de apresentação, não aprovação de publicação sem proveniência suficiente. Datas não são exigidas. O modelo rejeita partes desconhecidas, texto vazio e ordem sem fundamentação; filtra pelo ID da coleção e do artigo. A edição normal apresenta somente `approved`; a prévia apresenta somente `demonstration`. A marcação técnica `approved` deve decorrer de homologação humana independente registrada, nunca de aprovação automática ou apenas de Produto.

Os três caputs reais foram transcritos sem alteração do complemento documental aprovado. Cada registro preserva o ID do piloto, referência, notas, coordenadas no CP.pdf, hash e evidência da confirmação humana na conversa. O PDF histórico local não foi incluído no pacote; o painel oferece referências oficiais complementares e informa sua localização documental. Os demais artigos continuam sem registros. Não há importador, editor administrativo ou reconstrução automática neste incremento. Novos conteúdos dependem de homologação e autorização próprias.

## Comportamento e validação

Painel modal à direita no desktop e em tela inteira no celular, com rolagem própria. Botão Fechar e Escape restauram posição e foco sem mudar rota ou seleção. Tab permanece no painel; mudanças de rota liberam o bloqueio de rolagem. Fontes HTTP(S) abrem em nova aba; textos e notas são escapados. O estado vazio afirma somente indisponibilidade de registros homologados, sem inferir ausência de alterações.

Validação: `npm test`; `.venv/Scripts/python.exe tests/browser/legislative_history.py` no ambiente local com Playwright, ou `python scripts/run_browser_tests.py --suite essential`. O teste específico verifica 320, 390 e 1280 px, teclado, leitura, notas opcionais, ausência de fontes/referências e troca de rota. Fixtures estão em `tests/fixtures/`, fora da lista de módulos publicada.
