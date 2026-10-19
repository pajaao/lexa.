# Lote 1 — Sistema visual e UX Writing

## Base e direção

Implementação incremental a partir da `main` em `b19201e11d6bf740fed12ad77c32b5277afdb320`, na branch `melhorias/ux-ui-lote-1`. O commit do PR #21 (`502727419dca7528eebb4fabc9cb62213a8c3a7a`) não é ancestral dessa base; nenhuma branch de remissões foi utilizada.

Referência recebida: `LEXA_UXUI_Lote1_Pacote_Codex.zip`, SHA-256 `7f921c4e1afd463fa77f08002cdb796c8b11f254293f377ee89f45e1ad4d3a3f`. Foram consultados a especificação oficial, os pareceres de UX/Produto, prototipagem, Engenharia e Qualidade, o HTML comparativo e os painéis A/B. O pacote substituiu o acesso indisponível aos documentos online. Exemplos fictícios e controles de remissões do protótipo não foram incorporados.

Direção A: superfícies claras, tipografia editorial, espaçamento e controles consistentes; tema escuro preservado. Direção B: identificação textual da legislação, edição e escopo CF/ADCT, com localização estrutural discreta. A estrutura jurídica exibida continua vindo dos mesmos dados e funções.

## Página inicial consolidada: composição híbrida e geometria editorial

A composição híbrida mantém a busca central com até 760 px, título de 36 px no desktop (30 px até 700 px e 28 px até 400 px), descrição próxima, exemplos e biblioteca logo abaixo. Preserva a paleta e a tipografia existentes. A geometria editorial expressiva foi a alternativa aprovada; não há seletor de variantes.

- **Primitivas:** linhas retas, cantos abertos, interrupções, arcos parciais e pequenos círculos. Coordenadas em grade de oito unidades, arcos de raios 32/48 e círculos de raio 2 no `viewBox` de 160 × 224. Sem símbolos jurídicos, textos, gradientes ou sombras decorativas.
- **Traço e cor:** traço uniforme de 1 px, com `non-scaling-stroke`; cor `--muted` da paleta de cada tema e opacidade de 0,4. Largura de 128 px por SVG, com altura proporcional. `--geometry-size`, `--geometry-stroke` e `--geometry-alpha` registram esses valores, sem ampliar contraste ou escala.
- **Composição:** dois SVGs assimétricos exclusivamente nas laterais da busca, sem ocupar espaço no fluxo. Recuo lateral de 34 px; posições verticais de 56 px à esquerda e 92 px à direita, relativas à região de busca. Manter o centro livre e o ritmo dos segmentos; não espelhar nem criar margens para acomodar os desenhos.
- **Responsividade e acessibilidade:** exibir somente a partir de 1200 px; ocultar em telas menores, alto contraste e impressão. Usar `aria-hidden="true"`, `focusable="false"` e `pointer-events:none`, sem ações, foco ou animações.
- **Escopo e verificação:** implementação em [app.js](../../src/app.js) e [styles.css](../../src/styles.css), restrita à home, sem biblioteca de componentes. [home_geometry.py](../../tests/browser/home_geometry.py), integrado à suíte essencial, verifica os valores aprovados, margens livres, invariância do conteúdo/layout, teclado, temas, alto contraste e impressão.

## Alterações

- `src/styles.css`: refinamento incremental de cabeçalho, busca, cartões, leitor e controles. Grade móvel em uma coluna; índice nativo expansível funcional. Cabeçalho permite quebra de linha em 320 px. Localização estrutural tem espaço reservado e resumo visual limitado, evitando que sua atualização aumente a barra sticky após a rolagem. O texto estrutural completo permanece no DOM.
- `src/app.js`: rótulo global visível; último artigo/súmula consultado com ação “Abrir”, sem promessa de restauração exata; mensagens de erro precisas, preservando recuperação existente.
- `src/reader.js`: rótulo local visível, identificação de edição sem alterar seu valor, escopo CF/ADCT no localizador, filtro “Mostrar só favoritos”/“Mostrar todos”, nome acessível da estrela conforme seu estado. Nenhuma alteração na paginação ou nos handlers de foco/rolagem/rotas.
- `src/interface-copy.js`, `src/pwa.js`, `src/index.html`: microtextos de integridade, dados incompletos e offline parcial/completo. A decisão de disponibilidade continua pertencendo ao mecanismo PWA existente. Não houve alteração no service worker, cache, atualização ou contratos de edição.
- `tests/node/interface-copy.test.js`: regressões das mensagens de erro e disponibilidade.
- `tests/browser/ux_lote1.py`, `scripts/run_browser_tests.py`: teste dirigido integrado à suíte essencial; capturas reproduzíveis e verificação dos principais pares cromáticos.
- `tests/browser/performance.py`: readiness pelo estado `data-offline-mode`, em vez de uma palavra de apresentação. O benchmark e suas medições permanecem preservados.

## Reprodução

Node 22, Python 3.12, Playwright e Chromium do ambiente Linux. Os testes usam servidor local; responsividade simulada, não dispositivos físicos.

```sh
npm test
python -m unittest discover -s tests -p 'test_*.py'
python scripts/run_browser_tests.py --suite essential
python tests/browser/ux_lote1.py
```

Capturas e observações dirigidas: `test-results/ux-lote1/`. Para capturar uma versão anterior já compilada sem exigir os novos rótulos:

```sh
python tests/browser/ux_lote1.py --capture-only --site CAMINHO/dist --artifacts CAMINHO/capturas
```

O teste dirigido utiliza 1366 × 768, 390 × 812 e 320 × 700, temas claro/escuro, movimento reduzido, ausência de overflow horizontal, pesquisa por referência, CF/ADCT, índice móvel por teclado, ajustes, modo de foco, favoritos persistidos, retomada, estado vazio e rejeição SHA com recuperação. As verificações PWA/offline reais pertencem às suítes existentes, sem bloquear service workers nesses cenários.

## Limites

Não há remissões, novas dependências, alteração de URLs ou lógica jurídica. Roteamento, gerenciamento estrutural de foco e restauração completa de contexto ficam para os lotes posteriores. Os testes de teclado e contraste são direcionados e não certificam conformidade integral WCAG. Não foi realizada avaliação com leitor de tela, dispositivo físico ou revisão independente de Qualidade. Esta última continua necessária antes de aprovação. Nenhum merge ou deploy está autorizado.

## Medições e verificação de integridade

Medições estáticas reproduzíveis do build (gzip Python, `mtime=0`; não representam negociação HTTP nem latência):

| Recurso | Base | Lote 1 |
| --- | ---: | ---: |
| HTML, bytes | 55.235 | 64.259 |
| HTML, gzip bytes | 12.839 | 14.455 |
| Módulos ESM | 19 | 20 |
| JavaScript total, bytes | 103.178 | 104.945 |

O módulo adicional contém apenas mensagens compartilhadas de interface; há um recurso ESM adicional no carregamento. Não se afirma impacto zero nem ganho de desempenho. Não foi repetida uma auditoria de desempenho. Nenhum índice ou coleção adicional é carregado para orientação contextual.

Comparação byte a byte com o build arquivado da base: **44 arquivos JSON/PDF idênticos**, incluindo catálogo, recursos jurídicos e PDFs. Nenhum arquivo do corpus, fonte, histórico, contrato de edição, service worker ou roteador foi modificado.

Os pares cromáticos medidos e viewports constam em `lote-1-verificacao.json`. Texto principal/superfície: 11,33:1 claro e 11,40:1 escuro; texto secundário/fundo: 5,55:1 e 8,14:1; borda de controle/superfície: 3,41:1 e 3,90:1. Esses pares não substituem avaliação de todos os estados e componentes.

## Regressões encontradas durante a implementação

1. Navegação do cabeçalho transbordava em 320 px: corrigida permitindo quebra dos links, sem esconder ações.
2. Barra móvel ultrapassava o limite compacto do teste de favoritos: corrigidos espaçamentos, mantendo áreas principais de controle de 44 px.
3. O localizador ampliado alterava a altura sticky e, no desktop, podia deixar o artigo fora da linha usada pelo histórico existente: passou a reservar uma linha estrutural resumida. O teste de leitura voltou a passar sem modificar os mecanismos de histórico/foco/rolagem. A regressão dirigida também exige que o link de retomada aponte ao artigo efetivamente consultado e que o cabeçalho do artigo esteja abaixo dos controles.

Os testes preexistentes não tiveram expectativas funcionais relaxadas para acomodar essas falhas.

## Resultado final dos testes

- Linha de base registrada antes da implementação: 52 testes Node e 11 verificações Chromium essenciais aprovados.
- `npm test`: **54/54 Node**, com build de produção aprovado.
- `python -m unittest discover -s tests -p 'test_*.py'`: **46/46**.
- `python scripts/run_browser_tests.py --suite essential`: **12/12**, zero falhas na execução final. Inclui leitura, paginação/índice por teclado com movimento normal e reduzido, busca, favoritos, cópia automática/manual, integridade, PWA, offline e contrato do benchmark, além do novo teste do Lote 1.
- `python tests/browser/ux_lote1.py`: aprovado também isoladamente nas seis combinações de viewport/tema.
- Capturas da base geradas separadamente com `--capture-only`, sem modificar o checkout ou seus dados.
- `git diff --check`: aprovado.

Chromium **154.0.8037.57** em Linux. Capturas antes/depois, logs e diff acompanham o pacote de revisão. A validação realizada aqui não substitui a avaliação independente de Qualidade nem a aprovação da Coordenação.
