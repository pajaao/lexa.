# Lexa — Parecer de Engenharia | Fase O1: auditoria estrutural e inventário

**Data:** 18/10/2026 · **Frente:** Engenharia · **Natureza:** auditoria estrutural assistida por IA, não revisão jurídica humana.  
**Base deste parecer:** `main` @ [`84c5bb5c5e28c08376e0bf40cf3f3f4b4fd783cf`](https://github.com/pajaao/lexa./commit/84c5bb5c5e28c08376e0bf40cf3f3f4b4fd783cf). **Só este documento** foi criado na branch documental O1.  
**Escopo de leitura:** árvores Git completas, metadados e diffs de PR, workflows, scripts, documentação operacional, relatórios de remissões e pareceres. Não houve reexecução de suítes, download/revisão de PDFs nem navegação funcional de uma edição implantada.

## 1. Resumo executivo e veredito

**Veredito: organização atual sustentável, com saneamento incremental recomendado; nenhuma limpeza destrutiva autorizável neste momento.**

- `main` tem **144 blobs** em 12 grupos de topo, aproximadamente **69,01 MB de bytes registrados nas entradas da árvore**. Possui PWA estática, catálogo, dados jurídicos, monitoramento, build Node/ESM, testes, fontes e documentação operacional. **Não** possui os módulos/índices de remissões experimentais.
- A branch `validacao/remissoes-fase-1a-2-fechamento` tem **211 blobs**, aproximadamente **80,92 MB**, incluindo **35** arquivos em `docs/`; a evolução foi acrescentando extrator, testes e evidências, e **não** representa automaticamente código incorporado ou publicado.
- Foram encontradas **21 branches** listadas pelo GitHub e **16 PRs** numerados (#1–#16), dos quais **10 abertos (#7–#16)**, todos com diff exclusivamente documental em relação às respectivas bases. Os seis PRs anteriores (#1–#6) estão **mesclados**, conforme campos `merged_at`; branches remanescentes não provam falta ou presença de integração por si sós.
- A cadeia **0.5 → 1A → 1A.1 → 1A.2 → fechamento** tem ancestralidade Git linear, confirmada por comparação entre os heads. PRs #11–#16 estão **sobre bases experimentais**, e a simples mudança do destino para `main` **arrastaria código/dados experimentais**, contrariando a governança.
- **Único defeito de referência demonstrado nesta inspeção (ORG-A01):** link para fixture `phase 0.json` no relatório 0.5, quando o arquivo real é `phase0.json`. Não há defeito comprovado no build de produção decorrente disso.
- Fontes, históricos, manifestos, artefatos jurídicos e evidências não são “lixo”; a reorganização deve privilegiar índices de navegação, contratos de imutabilidade e procedimentos de promoção de branches.

**Não foi verificado o commit efetivamente servido pelo GitHub Pages**: o workflow de `main` foi inspecionado, mas a API de deployments e a leitura direta do site não forneceram comprovação da versão atualmente online. Assim, `main` significa **código de publicação configurado**, não atestado de implantação concluída.

## 2. Refs, commits e método

### 2.1 Refs de desenvolvimento examinadas

| Etapa | Branch | Commit verificado | Situação relativa |
|---|---|---|---|
| Base / publicação configurada | `main` | `84c5bb5c5e28c08376e0bf40cf3f3f4b4fd783cf` | referência-base |
| 0.5 | `investigacao/remissoes-fase-0-5` | `b414204aadf24d0a0d213365060bc347b3f3847d` | +6 commits vs. `main` |
| 1A | `funcionalidade/remissoes-fase-1a` | `3bb3c412e06f23a7be27458669ddd1448f35a130` | +3 vs. 0.5 |
| 1A.1 | `correcao/remissoes-fase-1a-1` | `5b218d9dc38c94194e0a13c51984d2b6d14c2f14` | +2 vs. 1A |
| 1A.2 | `validacao/remissoes-fase-1a-2` | `316a979e32ef35ebc3d385b9e9a73e368806e1cf` | +1 vs. 1A.1 |
| Fechamento 1A.2 | `validacao/remissoes-fase-1a-2-fechamento` | `64862b4b47811ab886396b9b22d4888af49aa4db` | +1 vs. 1A.2 |
| Deliberação 1A.3 (documental) | `docs/coordenacao-decisoes-fase-1a-3` | `4b4b4be93fdf3538e17b10f6cb19afb51338f248` | +1 vs. fechamento |

Head de outros PRs documentais: #7 `67a2de4a6a46a13634e3129a7a7c0030e7923f44`; #8 `0f84f8ebd6111b5140ed2b7e58d2a68778f0a9c7`; #9 `60b67a63a93f9340e310446e4f92d04f23cfb52d`; #10 `d11823f6faddd286fd94cf4c6c3260f851fe61b8`; #11 `9b296a43c2bfd44d1c303f647a877007818f79b1`; #12 `93557c005b38cc646fd2ec1e8863c88ca5e6abaf`; #13 `d9c5a1f5f5d85d990904450532b5f0903ce46507`; #14 `c3a4e7e3d0b1acbad3d4538d64fdbb6119d80e50`; #15 `a2ef2d3e7849a551b7924b5ff514d89b2e46842b`; #16 `4b4b4be93fdf3538e17b10f6cb19afb51338f248`.

**Rastreabilidade do inventário:** [árvore `main` fixa](https://github.com/pajaao/lexa./tree/84c5bb5c5e28c08376e0bf40cf3f3f4b4fd783cf), [árvore do fechamento fixa](https://github.com/pajaao/lexa./tree/64862b4b47811ab886396b9b22d4888af49aa4db), [comparação `main...fechamento`](https://github.com/pajaao/lexa./compare/84c5bb5c5e28c08376e0bf40cf3f3f4b4fd783cf...64862b4b47811ab886396b9b22d4888af49aa4db). A árvore do fechamento contém **67 blobs a mais** que `main`, mas isso **não** é contagem de mudanças funcionais nem uma razão para deletá-los.

### 2.2 Natureza das verificações

Foram lidos HEADs, árvores recursivas e o conjunto de arquivos de cada PR. Comparações `compare` provaram ancestralidade sem divergência de commits entre os estágios listados. Conteúdos foram verificados por leitura de documentos e fontes relevantes, não por execução das suas afirmações. As métricas e os testes descritos nos relatórios são **resultados relatados**, exceto a verificação independente *relatada no PR #13*, feita por outra frente/Coordenação; Engenharia não a repetiu. URLs de cada evidência apontam ao arquivo e, sempre que possível, ao commit estudado.

## 3. Inventário estrutural

### 3.1 `main`: todos os grupos de topo (blobs; tamanhos do GitHub)

| Conjunto | Arquivos | Bytes | Função e dependências | Manutenção / classificação |
|---|---:|---:|---|---|
| `.github/` | 5 | 9.331 | `verify.yml`, `deploy-pages.yml`, dois monitores e `actions/setup-browser/action.yml`; chamam Node, Python e Chromium | **Alta; D** (infraestrutura ativa, fluxo STF manual) |
| `src/` | 22 | 147.980 | HTML, CSS, ESM do leitor, busca, catálogo, cache, histórico, PWA, service worker | **Alta; D** |
| `public/` | 7 | 31.862 | ícones, favicon e manifesto instalável copiados pelo publicador | **Alta; D** |
| `data/` | 6 | 16.691.617 | `archive/{legislation,sumulas}.js`, `official/{legislation,sumulas}.js`, `history/{legislation,sumulas}.js` | **Crítica/jurídica; D** |
| `sources/` | 18 | 43.087.766 | 14 PDFs, `manifest.json`, `official-manifest.json`, `sumulas-manifest.json`, `import-report.json` | **Crítica/jurídica; D** |
| `monitor/` | 16 | 8.458.084 | `sources.json`, 13 snapshots `official/*.json`, `README.md`, `stf/README.md`; captura transitória fica ignorada em `monitor/run/` | **Alta/proveniência; D** |
| `scripts/` | 15 | 91.931 | build, pages, servidor, importadores e verificadores de fontes; requirements Python e runner browser | **Alta; D** |
| `tests/` | 41 | 169.793 | 13 testes Node, 19 scripts browser, 7 testes Python e suporte/fixture; qualidade do app/monitor | **Alta; D** |
| `docs/` | 11 | 308.613 | estrutura/manutenção, otimização/UX e baselines/medições históricas | **Média-alta; C/D** |
| `README.md` | 1 | 12.187 | orientação do usuário e desenvolvedor; links para docs | **Alta; D** |
| `package.json` | 1 | 453 | Node ESM `>=22`; build, dev, testes Node/Python; sem dependências npm declaradas | **Alta; D** |
| `.gitignore` | 1 | 185 | exclui `dist/`, `test-results/`, `monitor/run/` e caches | **Alta; D** |
| **Total** | **144** | **69.009.802** | bytes de blobs somados, não tamanho de checkout/caches nem bytes transferidos | — |

**Inventário por responsabilidade:**

- **Código de produto:** `src/app.js`, `reader.js`, `reader-model.js`, `presentation.js`, `structure.js`, `data.js`, `article-lookup.js`, `catalog.js`, `collections.js`, `collection-model.js`, `loading.js`, `collection-cache.js`, `search-index.js`, `library-search.js`, `history.js`, `history-store.js`, `copy.js`, `clipboard.js`, `pwa.js`, `sw.js`, `index.html`, `styles.css`. O build transforma `collections.js`/`catalog.js` para o adaptador do navegador; o código-fonte tem função própria nos testes/Node.
- **Build e manutenção:** `scripts/{build,build-pages,server,recent-updates}.mjs`; `{import_pdfs,import_official,import_sumulas,check_official_sources,check_stf_sources,official_http,stf_browser,run_browser_tests}.py`; `requirements-{browser,import,stf}.txt`.
- **Testes:** `tests/node/*.test.js` (13 arquivos); `tests/browser/*.py` (19); `tests/python/test_*.py` (7); `tests/python/__init__.py` e `tests/fixtures/dignidade-results.json` compõem os 41 blobs. Preservar os testes do monitor apesar de não fazerem parte do app no navegador.
- **Fontes e eventos:** `sources/*.pdf`, manifests e `monitor/official/*.json` são insumos/versionamentos; `data/{archive,official,history}` não são versões redundantes automaticamente.
- **Documentação base:** `docs/{ESTRUTURA,MANUTENCAO,BASELINE-DESEMPENHO,OTIMIZACAO-ETAPAS-2-6,REVISAO-DESEMPENHO,UX-REFINAMENTOS-ETAPA-1,UX-REFINAMENTOS-ETAPA-2}.md`, três JSONs em `docs/baselines/` e um em `docs/medicoes/`.

### 3.2 Inventário incremental das remissões, em relação à `main`

| Branch (head acima) | Total de blobs | Conteúdo incremental identificável | Estado |
|---|---:|---|---|
| 0.5 | 166 | `scripts/remissions/{grammar,norms,extract,graph,corpus,evaluate,analyze,simulate,select-sample,phase0-baseline}.mjs/.py`, README, fixtures, testes, `docs/remissoes/fase-0-5.md` e relatórios | somente investigação |
| 1A | 182 | `scripts/remissions/{eligibility,build-resource,measure-integration}.mjs`, `scripts/build-remissions-experiment.mjs`, `src/optional/remissions*.js`, hooks no build/worker/loading, novos testes e medições | infraestrutura experimental desabilitada no build padrão |
| 1A.1 | 193 | `scripts/remissions/{context,adversarial,compare-robustness}.mjs`, correções em `extract/norms/eligibility`, testes e relatórios adversariais | correções experimentais, sem UI |
| 1A.2 | 203 | `scripts/audit-remissions/{run,checks}.mjs`, `tests/node/remissions-audit.test.js`, seis arquivos em `docs/remissoes/fase-1a-2/` e relatório | auditoria documental, não homologação |
| Fechamento | 211 | `scripts/{document_parenthetical_closure.py,verify_remissions_closure.py,reproduce_remissions_closure.mjs}`, `tests/test_remissions_closure.py`, quatro arquivos de fechamento | verificação/reprodução de artefatos, sem ativação |
| Deliberação 1A.3 | 212 | `docs/coordenacao/00-decisoes-fase-1a-3.md` apenas | proposta/registro documental no PR #16, não em `main` |

No fechamento, `docs/` soma **11.916.938 bytes**; `docs/remissoes/` soma **11.608.325 bytes**. Contribuintes grandes e **protegidos**: `fase-1a-2/arestas.json` (4.454.575 B), `rejeicoes-amostra.json` (3.796.955 B), `revisao-humana.csv` (1.848.156 B), `arestas.csv` (1.179.060 B). Não recomendar exclusão/compressão substitutiva nem Git LFS retroativo sem deliberar impactos nos hashes, leitores e links.

`docs/coordenacao/` **não existe na `main` de referência**; aparece nos PRs documentais e, em particular, o arquivo de deliberação 1A.3 está no head #16 sobre o fechamento, sem integrar a `main`. É intencional que esse histórico seja distribuído por branches enquanto não deliberada a promoção.

## 4. Matriz completa dos Pull Requests

**Leitura:** colunas “arquivos” descrevem o diff real do PR contra seu destino, não todos os arquivos presentes em sua branch. **Todos #7–#16 estão abertos e não mesclados.** “Doc. isolada” indica se o *diff* é documental; não significa que a *ancestralidade* é segura para um merge na `main`.

| PR | Finalidade / head → base | Head commit (prefixo) | Arquivos modificados no PR | Dependência e risco | Recomendação |
|---|---|---|---|---|---|
| [#7](https://github.com/pajaao/lexa./pull/7) | Qualidade Fase 1A; `docs/parecer-qualidade` → `main` | `67a2de4` | só `docs/coordenacao/04-qualidade-testes.md` | 1 doc adicionado; parecer menciona 1A não incorporada | **Integrar depois de revisão** isoladamente |
| [#8](https://github.com/pajaao/lexa./pull/8) | Integridade; `docs/parecer-integridade` → `main` | `0f84f8e` | só `02-integridade-juridica.md` | 3 commits no mesmo arquivo e adendos posteriores; congelar versão antes do aceite | **Integrar depois de revisão**, preservando adendos |
| [#9](https://github.com/pajaao/lexa./pull/9) | Engenharia; `docs/parecer-engenharia` → `main` | `60b67a6` | só `01-engenharia.md` | base limpa, não incorpora código de remissões | **Integrar depois de revisão** |
| [#10](https://github.com/pajaao/lexa./pull/10) | UX e Produto; `docs/parecer-ux` → `main` | `d11823f` | só `03-ux-produto.md` | PR **draft**, requer revisão/aceite antes da integração | **Manter aberto** até pronto; integrar depois |
| [#11](https://github.com/pajaao/lexa./pull/11) | Qualidade 1A.1; `docs/parecer-qualidade-fase-1a-1` → `correcao/remissoes-fase-1a-1` | `9b296a4` | só `04-qualidade-testes-fase-1a-1.md` | destino inclui cadeia 0.5/1A/1A.1 | **Manter aberto** na base; se quiser na main, PR documental novo |
| [#12](https://github.com/pajaao/lexa./pull/12) | Qualidade 1A.2; `docs/parecer-qualidade-fase-1a-2` → `validacao/remissoes-fase-1a-2` | `93557c0` | só `04-qualidade-testes-fase-1a-2.md` | foi usado como insumo do fechamento, sem ser mergeado | **Manter aberto**, integrar na base apenas após avaliação |
| [#13](https://github.com/pajaao/lexa./pull/13) | execução independente relatada; `docs/verificacao-independente-fechamento-1a-2` → `validacao/remissoes-fase-1a-2-fechamento` | `d9c5a1f` | só `05-execucao-independente-fechamento-1a-2.md` | suporte probatório ao parecer #14; relatório declara 3 comandos aprovados | **Integrar depois de revisão** na base de fechamento; não retargetar |
| [#14](https://github.com/pajaao/lexa./pull/14) | Qualidade fechamento; `docs/parecer-qualidade-fechamento-1a-2` → fechamento | `c3a4e7e` | só `04-qualidade-testes-fechamento-1a-2.md` | depende logicamente da evidência #13; aceita *somente* fechamento técnico com ressalvas | **Integrar depois de #13** na mesma base, se aprovado |
| [#15](https://github.com/pajaao/lexa./pull/15) | Integridade 1A.3; `docs/parecer-integridade-fase-1a-3` → fechamento | `a2ef2d3` | só `02-integridade-juridica-fase-1a-3.md` | propostas P1-r–P5-r e 30 parentéticas; não é revisão humana | **Integrar depois de revisão** na base, mantendo caráter consultivo |
| [#16](https://github.com/pajaao/lexa./pull/16) | deliberação da Coordenação 1A.3; `docs/coordenacao-decisoes-fase-1a-3` → fechamento | `4b4b4be` | só `00-decisoes-fase-1a-3.md` | referências #13/#14/#15 e dependência de sua leitura; nenhum código; decisão documental ainda fora da main | **Manter aberto** até conferência central e consolidação, depois integrar na base |
 
**Commits dos PRs:** #7 `67a2de4`; #8 `ea1eecf`, `5503920`, `0f84f8e`; #9 `60b67a6`; #10 `d11823f`; #11 `9b296a4`; #12 `93557c0`; #13 `d9c5a1f`; #14 `c3a4e7e`; #15 `a2ef2d3`; #16 `4b4b4be`. SHA completos dos heads constam na seção 2; os commits intermediários do #8 são `ea1eecf2b773354d25e650e70b5bf0566e88bc3c` e `55039203a75c8663514c4ef6512f35bbf898b15e`. Bases exatas: #7–#10 → `84c5bb5...`; #11 → `5b218d9...`; #12 → `316a979...`; #13–#16 → `64862b4...`. Os PRs #1–#6 estão mesclados (2/3 fontes oficiais, 4 otimização, 5/6 UX, 1 referência inicial), sem ação de saneamento recomendada; conservar histórico.

**Risco de incorporação:** PRs #7–#10 permitem integração **documental isolada em `main`**, por diff. #11–#16 podem ser integrados **documentalmente em suas bases originais**; **não** são equivalentes a PRs de documentação sobre `main`. Para dar visibilidade central na `main` antes da aprovação das branches técnicas, criar **novos PRs apenas com cópias documentais identificadas e seus links de origem**, sem manipular/encerrar os PRs atuais. Eventuais conflitos só podem ser qualificados após nova checagem no momento da integração; hoje os caminhos novos são distintos.

## 5. Mapa de dependências e fronteiras de publicação

```text
sources/*.pdf + sources/{manifest,official-manifest,sumulas-manifest}.json
   ↕  scripts/{import_pdfs,check_official_sources,import_official,
                check_stf_sources,import_sumulas,official_http,stf_browser}.py
monitor/sources.json + monitor/official/*.json → data/official/*.js
data/archive/*.js + data/official/*.js + data/history/*.js
   + src/catalog.js + src/search-index.js
   └→ scripts/build.mjs (seleção de edições; JSON por norma + SHA)
          └→ scripts/build-pages.mjs (allowlist; src/index.html/styles.css;
             src/*.js ESM; public/*; PDFs de sources/; src/sw.js)
                └→ dist/ (IGNORADO; catálogo, app/<sha>/, data/<sha>.json, PDFs)
                      └→ GitHub Actions deploy-pages.yml em push na main
tests/node/*.test.js + tests/python/test_*.py + tests/browser/*.py
   ↔ package.json / scripts/run_browser_tests.py / .github/workflows/verify.yml

APENAS NO RAMO EXPERIMENTAL:
mesmo corpus jurídico do build
   → scripts/remissions/{grammar,norms,context,extract}.mjs
   → scripts/remissions/eligibility.mjs (quatro classes; experimental-only)
   → scripts/remissions/{graph,build-resource}.mjs
   → índice JSON imutável, descriptor/hash → src/optional/remissions*.js
   → scripts/audit-remissions/{run,checks}.mjs
   → docs/remissoes/fase-1a-2/* + fechamento/* (artefatos de auditoria)
   → scripts/{reproduce_remissions_closure.mjs,verify_remissions_closure.py}
      + tests/test_remissions_closure.py (reprodução/verificação)
```

- **ESM e caminhos:** `scripts/build.mjs` descobre os `src/*.js` de raiz e gera um namespace `app/<sha>/` com imports relativos preservados. Na branch 1A, acrescenta opcionalmente `src/optional/*.js` e exclui `optional/` do `modulepreload`. Mover `src/`, módulos ou adaptadores altera resolução de imports, pré-carregamento e hash do pacote.
- **PWA e offline:** `src/sw.js` valida manifestos SHA, mantém caches versionados e downloads parciais/completos. Alterar caminhos dos recursos afeta instalação, fallback de edições e coabitação de abas; testa-se antes/depois, inclusive sem rede. Nenhum índice de remissões é publicado no build padrão verificado.
- **Fontes e hashes:** `scripts/build-pages.mjs` publica PDFs por lista explícita derivada dos manifests; a ausência de importação direta não elimina a dependência. O histórico `data/history/` também é parte da interface de atualizações.
- **Testes/CI:** `package.json` executa `npm test` (com build) e Python; `verify.yml` inclui Chromium essencial. `deploy-pages.yml` é disparado por `push` em `main`, roda testes e publica `dist/`. `monitor-legislation.yml` agenda coleta e propõe PR em draft; `monitor-sumulas.yml` está manual/pausado. Mover scripts requer editar workflows, docs, fixtures e qualquer invocação por caminho literal.
- **Auditoria independente com limites:** `verify_remissions_closure.py` não importa a lógica de extração; o snapshot completo para seleção vem do pipeline por `reproduce_remissions_closure.mjs`. Preservar ambas as trilhas e a indicação de independência **computacional**, não jurídica.

## 6. Remissões: invariantes, problemas e oportunidades (A–D)

### 6.1 Invariantes observadas e decisões ainda não incorporadas à main

O extrator 0.5.1 foi separado do leitor; a Fase 1A.1 registrou 0.5.2 e política 1a.1, mantendo as classes `parenthetical-article-list`, `self-qualified-article-list`, `adct-self-article` e `numbered-law-article-list`, todas sob `experimental-only`. Fase 1A.2 e fechamento preservaram o inventário: **329 arestas**, **272 ocorrências**, **353 participações ocorrência–aresta**; **4.624 rejeições** no pipeline, **354** amostradas em **203 estratos**, **683** linhas no CSV de revisão humana **sem decisões preenchidas**. Os cinco arquivos auditados foram relatados reproduzidos byte a byte; [PR #13](https://github.com/pajaao/lexa./pull/13) documenta execução separada de três comandos (10 testes; zero divergências); [PR #14](https://github.com/pajaao/lexa./pull/14) aprova com ressalvas **apenas** o fechamento técnico-documental.

As **30 arestas parentéticas/26 ocorrências** continuam documentadas em `parenteticas.csv`: 0 promovidas, 0 bloqueadas por contradição positiva, 30 pendentes. [PR #15](https://github.com/pajaao/lexa./pull/15) propõe P1-r–P5-r; [PR #16](https://github.com/pajaao/lexa./pull/16) **registra deliberação central documental** que adota esses critérios apenas para futura investigação e exclui as 30 da primeira liberação pública, sem retirá-las do inventário. **O PR #16 está aberto:** registrar sua existência e conteúdo não significa que esteja integrado na `main` ou tenha modificado a política executável.

Preservar os IDs de arestas/ocorrências, hashes, offsets UTF-16, referências ao texto jurídico, separação CF/ADCT, identificação explícita de edição e condições históricas. Não usar semelhança temática, proximidade numérica ou IA para estabelecer links. Qualquer interface futura depende de revisão jurídica humana e autorização central expressa.

### 6.2 Classificação com evidência

| Código | Classe | Evidência observada | Consequência e encaminhamento |
|---|---|---|---|
| **ORG-A01** | **A — defeito demonstrado, documental** | No [relatório 0.5](https://github.com/pajaao/lexa./blob/b414204aadf24d0a0d213365060bc347b3f3847d/docs/remissoes/fase-0-5.md), o link “Amostra de desenvolvimento” usa `../../tests/fixtures/remissions/phase 0.json`; essa rota dá 404, enquanto `phase0.json` existe. | Corrigir **apenas link em futuro PR documental**, mantendo arquivo e hash do fixture; sem impacto demonstrado no build. |
| **ORG-B01** | **B — risco de integração confirmado pela topologia** | PRs #11–#16 baseados em branches descendentes do código experimental; `main` não contém esses ancestrais. | Não alterar base para `main`, não mesclar cadeia por conveniência documental. Separar publicação de pareceres de promoção de código. |
| **ORG-B02** | **B — risco de reprodução/imutabilidade** | Artefatos 1A.2 somam >11 MB em `docs/remissoes/`; `manifesto.json`, hashes e verificadores dependem de caminhos/bytes; relatórios trazem comandos com caminhos literais. | Não mover, converter CSV/JSON, normalizar quebras de linha nem aplicar LFS retroativo sem estudo e novo aceite. |
| **ORG-B03** | **B — risco de manutenção documentacional** | `scripts/remissions/README.md` ainda descreve a investigação 0.5, apesar das fases seguintes terem infraestrutura de build e auditoria; documentos de fases diferentes ficam lado a lado. | Criar índice por fase/status. **Não** sobrescrever relatório histórico com resumo contemporâneo. |
| **ORG-B04** | **B — risco de atualização PWA/integração** | `build.mjs` usa descoberta de arquivos e namespace ESM derivado de SHA; `build-pages.mjs` usa allowlist de PDFs/ícones; `sw.js` vincula URLs a manifesto de integridade e cache. | Renomes só com atualização sincronizada de imports, build, CI, manifesto e testes online/offline; manter rollback de versão. |
| **ORG-B05** | **B — limitação de prova de produção** | Existe deploy workflow `push: main`, mas não foi obtido registro do último deploy/commit servido. | Verificar deployment real antes de afirmar que `main` atual está online; não induzir “publicado” a partir de branch/PR. |
| **ORG-C01** | **C — melhoria, sem defeito** | Documentação operacional, baselines, UX e evidência experimental espalhadas sem índice transversal. | Criar `docs/INDEX.md`, `docs/remissoes/INDEX.md` e `docs/coordenacao/INDEX.md` com status/commit/PR. |
| **ORG-C02** | **C — melhoria, sem defeito** | Python de coleta/importação e JS do build ficam ambos na raiz de `scripts/`; testes também são distribuídos por linguagens. | Agrupar **somente por conveniência comprovada**; primeiro wrappers/índices, depois movimentações em PRs individuais. |
| **ORG-D01** | **D — estrutura intencional** | `data/archive/`, `data/official/`, `data/history/` e `sources/` atendem a funções distintas; os PDFs, HTMLs coletados e históricos preservam proveniência. | **Permanecem**; aparente repetição é parte do contrato jurídico-editorial. |
| **ORG-D02** | **D — estrutura intencional** | `docs/remissoes/` e `tests/fixtures/remissions*/` contêm gold, holdouts, rejeições e reprodução de resultados; script de fechamento isola verificação de pipeline. | **Permanecem intactos** nos commits de origem; novos pareceres devem ser adendos. |
| **ORG-D03** | **D — estrutura intencional** | `dist/`, `test-results/`, `monitor/run/` ignorados; STF está em workflow manual e Planalto em rotina de propostas sem automerge. | Não versionar outputs transitórios nem reativar monitor STF como “limpeza”. |

**Identificadores jurídicos preexistentes (não renumerar):** [Fase 1A.1](https://github.com/pajaao/lexa./blob/5b218d9dc38c94194e0a13c51984d2b6d14c2f14/docs/remissoes/fase-1a-1.md) registra **A01** (Lei 8.666 x “desta Lei”), **B01** (ADCT de 1967 x 1988), **B02** (antecedente riscado) e **C01** (reprodução após segundo parágrafo), além de CPP13-A e outros casos. Foram relatados corrigidos/convertidos em abstenção **na 1A.1**, mantendo **329** arestas. Esses IDs **não** são ORG-A01/ORG-B01 etc.; não são novos defeitos confirmados em `main`.

## 7. Estrutura futura e mapa atual → proposto

### 7.1 Proposta conservadora

```text
.github/workflows/                  [mantém]
src/, src/optional/                 [mantêm, apenas após aprovação da integração]
public/                             [mantém]
data/{archive,official,history}/    [mantém]
sources/, monitor/                  [mantêm]
scripts/                            [mantém contrato principal]
  remissions/                       [mantém na branch experimental]
  audit-remissions/                 [mantém na branch experimental]
tests/{node,browser,python,fixtures}/ [mantêm]
docs/
  INDEX.md                          [NOVO: navegação, proveniência e estados]
  operacao/                         [OPCIONAL: documentação viva; após revisar links]
  coordenacao/
    INDEX.md                        [NOVO: painel de pareceres e PRs; sem decisão automática]
    00-decisoes-fase-1a-3.md        [somente quando a base for homologada]
    01-engenharia-organizacao-o1.md [este registro, sem editar pareceres anteriores]
  remissoes/
    INDEX.md                        [NOVO: mapa 0.5–1A.3, hashes, reprodutores]
    fase-0-5.md, fase-1a*.md, fase-1a-*/ [PRESERVADOS]
  baselines/, medicoes/             [PRESERVADOS]
```

| Caminho atual | Caminho futuro recomendado | Tipo / dependências |
|---|---|---|
| `src/*`, `src/optional/*`, `public/*` | **mesmo caminho** | Contrato de build, ESM/PWA; não movimentar sem necessidade |
| `data/archive/*`, `data/official/*`, `data/history/*` | **mesmo caminho** | Protegidos; seleção de edição e histórico |
| `sources/*`, `monitor/official/*`, `monitor/sources.json` | **mesmo caminho** | Protegidos; fontes e procedência |
| `docs/remissoes/fase-1a-2/*`, `fase-1a-2-fechamento/*` | **mesmo caminho** | Protegidos byte a byte; CSV/JSON/IDs/SHA/caminhos de reprodução |
| `docs/remissoes/fase-0-5.md` | **mesmo caminho**; corrigir um link em O2 | Corrige ORG-A01 sem mover fixture |
| `docs/ESTRUTURA.md`, `docs/MANUTENCAO.md` | **mesmo caminho em O2**; *opção futura*: `docs/operacao/estrutura.md`, `docs/operacao/manutencao.md` | C; exigir revisão de links relativos, README e monitor |
| `docs/BASELINE-DESEMPENHO.md`, `docs/baselines/*` | **mesmo caminho**; opcional índice `docs/operacao/desempenho.md` | Manter baselines congeladas, sem sobrescrever números |
| `docs/UX-REFINAMENTOS-ETAPA-*.md` | **mesmo caminho**, referenciar via `docs/INDEX.md` | Histórico de UX protegido por rastreabilidade |
| `scripts/remissions/*`, `scripts/audit-remissions/*`, `scripts/verify_remissions_closure.py` | **mesmo caminho**; opcional `scripts/README.md` | Reprodutores e dependências literais; não mover na reorganização documental |
| `scripts/check_official_sources.py`, `import_official.py`, `official_http.py` | **mesmo caminho em O2/O3**; *opção O4*: `scripts/monitoramento/` | Movimento comportamental: imports Python, CI, monitor, testes e docs |
| `tests/test_remissions_closure.py` | **mesmo caminho**; *opção O4*: `tests/python/test_remissions_closure.py` somente após prova de equivalência | Requer conferência de descoberta, comandos históricos e fixture; preservar testes originais |
| `docs/coordenacao/*.md` em branches documentais | Conservar documentos originais; criar índices/PRs documentais específicos na base desejada | **Nunca** incorporar ancestrais experimentais por retarget de PR |

**Separação de mudanças:** criar índices, explicitar status, corrigir links e atualizar README é **documental**. Mover scripts, módulos, fontes, testes ou artifacts hashados é **técnico/arquitetural**, mesmo sem alterar algoritmos. Não misturar os dois tipos no mesmo PR.

**Política para artefatos grandes:** preservar binários e CSV/JSON auditados em seus commits e hashes originais. Registrar manifesto de tamanhos/SHA-256/versão/URL/commit, cópia externa de segurança somente se aprovada e testada. Avaliar armazenamento alternativo apenas para **novos artefatos derivados**, nunca para substituir retroativamente os arquivos protegidos; verificar políticas de retenção do Actions (14/30 dias), GitHub Pages e disponibilidade de reprodução sem depender de artefatos expirados.

## 8. Plano O2–O4 — execução futura, não realizada

| Fase | Base recomendada e dependências | Escopo / risco | Testes e aceite objetivos | Reversão |
|---|---|---|---|---|
| **O2 — higiene documental** | `main` **do head aprovado pela Coordenação** após decidir o PR O1; PRs #7–#10 revistos separadamente | Adicionar `docs/INDEX.md` e índices de `coordenacao/remissoes` apenas se suas fontes estiverem presentes; corrigir ORG-A01, anotar estados, referências entre branches e comandos. **Não copiar inadvertidamente código de #11–#16.** Risco baixo: links errados/proveniência perdida. | Diff somente Markdown e índice; todos os links internos resolvem na branch de destino ou apontam explicitamente para URL/commit da branch histórica; contagem e SHA dos protegidos idênticos; `npm test`, Python e Chromium essenciais como regressão antes de qualquer merge para `main`. | Reverter commit documental/PR individual; restaurar links antigos conforme revisão, sem reescrever histórico. |
| **O3 — preservação e saneamento experimental** | `validacao/remissoes-fase-1a-2-fechamento` @ `64862b4...`, ou sucessora deliberadamente aprovada; requer triagem #11–#16 | Indexar evidências, formalizar manifests SHA e matriz de reprodução; resolver documentação/adendos e avaliar agrupamento de helpers **sem mudar bytes de corpus/arestas/regras**. Risco médio: imports/caminhos literais e alterações de geração. | Comparar SHA-256 **byte a byte** dos 5 artefatos, parentéticas e fixtures; contagens 329/272/353/354/683/203; manter quatro classes e `experimental-only`; executar reprodutor/10 testes e verificadores, `npm test`, Python e Chromium quando houver qualquer mudança técnica. Se movimento alterar hash de extrator/política, **não aceitar como organização pura**: tarefa separada. | Reverter PR de saneamento isolado; apontar para SHA original imutável de fechamento; não regravar dados auditados. |
| **O4 — consolidação operacional e eventual promoção autorizada** | Para código de produção: `main` atualizado **somente após autorização expressa**; para refinamento experimental: base O3 aprovada | Eventual reorganização de `scripts/`, `tests/`, docs operacionais, CI e hooks; integração técnica de remissões só em PR distinto, após aprovação jurídica e de produto. Risco alto: build, ESM, integridade, deploy PWA e edições offline. | Paridade de recursos jurídicos/artigos/PDFs e hashes de fontes; verificação de imports e caminhos executáveis; Node/Python/Chromium; comparação de manifestos e bundles; instalar e testar PWA fria, parcial, completa, duas abas, atualização consentida e falhas offline/SHA; orçamento p50/p95 Android físico antes de alterar caches. **Zero mudança jurídica/links liberados sem autorização.** | Revert de PR atômico e recuperação do commit/bundle anterior; validar service worker/cache antigo antes de republicar; não usar force-push nem limpar caches do usuário como “correção”. |

**Ordem de saneamento de PRs sugerida:** (a) revisar e decidir #7–#10 documentalmente sobre `main`, com #10 ainda em draft; (b) preservar a cadeia de versões e conferir #11/#12 nas bases 1A.1/1A.2; (c) revisar #13 → #14 → #15 → #16 como documentos do fechamento, deixando claro que abertos ≠ aprovados; (d) se necessário, fazer novos PRs *documentais de origem limpa* em `main` para levar pareceres à Coordenação sem transferir código experimental; (e) só em fase autônoma e autorizada avaliar promoção de implementação. **Não** executar rebase, cherry-pick, merge ou fechamento agora.

## 9. Gate de segurança, riscos e pendências centrais

### Gate antes de qualquer execução posterior

1. Fixar HEAD de origem/destino e um manifesto SHA-256 de arquivos protegidos; comprovar que não houve alterações de textos, PDFs, `data/history`, snapshots jurídicos, `arestas.*`, `revisao-humana.csv`, `rejeicoes-amostra.json`, `manifesto.json`, `parenteticas.csv` ou fixtures congeladas.
2. Conferir `git diff --name-status`, `git diff --check`, paths de links e imports, hashes de arquivos e inexistência de alterações ao registro histórico; revisar PR por **um único propósito**.
3. Rodar comandos existentes conforme escopo: `npm test`, `npm run test:python`, `python scripts/run_browser_tests.py --suite essential`; em O3 incluir verificador e reprodução de fechamento, sem sobrescrever artefatos originais. Registrar versões e resultados **efetivamente executados**, nunca substituir por relatos.
4. Fazer teste local PWA no build resultante, inclusive offline parcial/completo, atualização e integridade; confirmar que `remissions:false` mantém 0 índice/requests; não confundir presença em branch com publicação.
5. Exigir revisão jurídica humana independente dos destinos, edição, escopo CF/ADCT, autoria histórica e origem da fonte **antes de qualquer interface com links**; no caso de dúvida, omitir.
6. Escolher rollback via revert de commit pequeno/PR, manter SHA anterior e validar navegação offline após nova versão do service worker; não forçar sincronização de dados antigos com grafo novo.

### Decisões pendentes para a Coordenação Central

- Confirmar a **base organizacional**: `main` para O2 e análise separada da branch de fechamento para O3; não mesclar experimental por atalho.
- Escolher destino e sequência dos pareceres abertos, especialmente status draft #10 e deliberação documental #16; decidir se haverá espelhos documentais em `main` antes da integração técnica.
- Ratificar a lista de **arquivos protegidos byte a byte** e a política de armazenamento/backup de evidências grandes (sem eliminação ou sobrescrita).
- Aprovar apenas correção documental ORG-A01 e índices no próximo escopo; qualquer refatoração de caminhos fica para tarefa independente.
- Definir quem atesta a versão efetivamente publicada no GitHub Pages e o orçamento de testes móveis/PWA.
- Preservar a deliberação documental proposta em #16: P1-r–P5-r apenas como protocolo, 30 parentéticas não liberadas, `experimental-only`, quatro classes e ausência de homologação jurídica humana. Sem decisão expressa, nenhuma remissão vai para o leitor.

**Conclusão:** Fase O1 encerra-se como diagnóstico rastreável. A ordem mais segura é **O2 documentação → O3 evidência experimental → O4 alterações técnicas estritamente autorizadas**. A contagem de arquivos não evidencia desorganização por si mesma. Nenhum arquivo do repositório foi reorganizado, deletado, renomeado ou alterado além deste novo parecer Markdown; nenhum merge, rebase, cherry-pick, deploy ou mudança de elegibilidade foi realizado.
