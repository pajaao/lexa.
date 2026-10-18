# Parecer técnico — Engenharia | Lexa

## 1. Identificação

- **Frente:** Engenharia (arquitetura, desempenho, geração e distribuição de remissões expressas).
- **Data do registro:** 18/10/2026.
- **Repositório:** [pajaao/lexa.](https://github.com/pajaao/lexa.).
- **Base verificada:** `main` no commit [`84c5bb5c5e28c08376e0bf40cf3f3f4b4fd783cf`](https://github.com/pajaao/lexa./commit/84c5bb5c5e28c08376e0bf40cf3f3f4b4fd783cf).
- **Investigação analisada:** `investigacao/remissoes-fase-0-5`, commit [`b414204aadf24d0a0d213365060bc347b3f3847d`](https://github.com/pajaao/lexa./commit/b414204aadf24d0a0d213365060bc347b3f3847d) (6 commits à frente de `main`).
- **Integração analisada:** `funcionalidade/remissoes-fase-1a`, commit [`3bb3c412e06f23a7be27458669ddd1448f35a130`](https://github.com/pajaao/lexa./commit/3bb3c412e06f23a7be27458669ddd1448f35a130) (9 commits à frente de `main`; 3 à frente da investigação).
- **Versões declaradas:** extrator 0.5.1, SHA-256 das regras `6cf232f85d242a28dd81ff654811106327f13948948b884afe8b7d289d3ae434`; política de elegibilidade 1a.0, modo `experimental-only`.
- **Natureza da verificação:** leitura do código, relatórios, métricas e testes registrados no GitHub, além de conferência dos refs e comparação de branches. **Não** foram reexecutadas suítes de teste, nem feita revisão jurídica humana independente.

## 2. Escopo

Avaliar a arquitetura e o desempenho do extrator **determinístico e executado no build**, a separação entre extração, elegibilidade e apresentação, a vinculação por SHA-256 às edições jurídicas, a integração ESM, o carregamento sob demanda, o service worker e a consistência offline. Não houve modificação de código ou de textos legislativos. A análise não propõe IA em produção, inferências temáticas ou remissões interpretativas.

## 3. Evidências verificadas

1. **Isolamento e progresso das fases.** A Fase 0.5 contém o extrator Node com gramática, resolução de identidade normativa, proveniência UTF-16 e condição de tachado, sem integração à PWA. A Fase 1A acrescenta `build-resource.mjs`, `eligibility.mjs`, módulos opcionais de consulta e testes de integração, preservando o extrator 0.5.1. A `main` verificada ainda não incorpora as branches. Referências: [relatório 0.5](https://github.com/pajaao/lexa./blob/b414204aadf24d0a0d213365060bc347b3f3847d/docs/remissoes/fase-0-5.md), [relatório 1A](https://github.com/pajaao/lexa./blob/3bb3c412e06f23a7be27458669ddd1448f35a130/docs/remissoes/fase-1a.md), [extrator](https://github.com/pajaao/lexa./blob/b414204aadf24d0a0d213365060bc347b3f3847d/scripts/remissions/extract.mjs).

2. **Pipeline e política.** `buildPackage({remissions:false})` é o padrão. A opção experimental gera o índice após definir as edições, usando os mesmos objetos jurídicos, sem mutá-los; o gerador rejeita modo de política diferente de `experimental-only`. A elegibilidade exige classificação A **mais** escopo, spans, hashes, destinos individuais, condição histórica e uma das quatro classes sintáticas autorizadas. Referências: [build.mjs](https://github.com/pajaao/lexa./blob/3bb3c412e06f23a7be27458669ddd1448f35a130/scripts/build.mjs), [build-resource.mjs](https://github.com/pajaao/lexa./blob/3bb3c412e06f23a7be27458669ddd1448f35a130/scripts/remissions/build-resource.mjs), [eligibility.mjs](https://github.com/pajaao/lexa./blob/3bb3c412e06f23a7be27458669ddd1448f35a130/scripts/remissions/eligibility.mjs).

3. **Inventário e contenção.** A varredura 0.5 documenta 7.110 entradas de 13 legislações e 4.896 candidatas; seus 2.326 vínculos A candidatos **não** foram autorizados para publicação. Na Fase 1A, a política aceita **272 ocorrências / 329 arestas únicas**, rejeitando 4.624 candidatas. A pequena amostra adicional indicou **7/7 destinos emitidos corretos**, com cobertura **7/25 (28%)** dos destinos esperados: métricas amostrais do próprio agente, sem validação jurídica independente. Referências: [fase-0-5.md](https://github.com/pajaao/lexa./blob/b414204aadf24d0a0d213365060bc347b3f3847d/docs/remissoes/fase-0-5.md), [metrics.json](https://github.com/pajaao/lexa./blob/3bb3c412e06f23a7be27458669ddd1448f35a130/docs/remissoes/fase-1a/metrics.json).

4. **Contrato SHA, ESM e grafo.** O índice JSON, sem cópia integral dos textos legais, contém edições e hashes de todas as normas, versão/hash do extrator e da política, SHA da geração, ocorrências com offsets UTF-16, arestas canônicas e adjacência inversa derivada. `fetchVerifiedJson` confere o SHA dos bytes. O módulo opcional valida o contrato integralmente antes de expor o grafo; a factory compartilha chamadas simultâneas e permite tentar novamente após erro. O índice é lazy, e os módulos usam ESM nativo. Referências: [remissions-contract.js](https://github.com/pajaao/lexa./blob/3bb3c412e06f23a7be27458669ddd1448f35a130/src/optional/remissions-contract.js), [remissions.js](https://github.com/pajaao/lexa./blob/3bb3c412e06f23a7be27458669ddd1448f35a130/src/optional/remissions.js), [loading.js](https://github.com/pajaao/lexa./blob/3bb3c412e06f23a7be27458669ddd1448f35a130/src/loading.js), [build-pages.mjs](https://github.com/pajaao/lexa./blob/3bb3c412e06f23a7be27458669ddd1448f35a130/scripts/build-pages.mjs).

5. **Custos e PWA (valores reportados, não reexecutados).** Medianas em Node 22.23.3: extração **465,65 ms**, elegibilidade **16,22 ms**, grafo/serialização **2,01 ms**. Índice: **54.795 bytes** (gzip local **18.728 bytes**); módulos opcionais **4.891 bytes**. Chromium com CPU limitada 4×: carregamento explícito da API **66,2 ms** e heap retido adicional **198.004 bytes**; sem dispositivo físico. Build padrão: mesma quantidade de requisições iniciais, **+21 bytes** de corpo em relação à base medida. O service worker trata manifestos de integridade, lazy resources, cache de edições e preparação completa explícita. O índice offline não garante que o texto do destino esteja offline. Referências: [fase-1a.md](https://github.com/pajaao/lexa./blob/3bb3c412e06f23a7be27458669ddd1448f35a130/docs/remissoes/fase-1a.md), [browser-metrics.json](https://github.com/pajaao/lexa./blob/3bb3c412e06f23a7be27458669ddd1448f35a130/docs/remissoes/fase-1a/browser-metrics.json), [sw.js](https://github.com/pajaao/lexa./blob/3bb3c412e06f23a7be27458669ddd1448f35a130/src/sw.js).

6. **Testes existentes.** O relatório 1A registra 109 testes Node, 46 Python e 12 verificações essenciais Chromium, além de testes específicos de determinismo, imutabilidade, alterações de edição, SHA, lazy loading, erro de rede, offline parcial/completo e duas abas em edições distintas. Não foram reexecutados nesta frente; não foram encontradas execuções de GitHub Actions para o commit final 1A na consulta realizada. Referências: [testes Node](https://github.com/pajaao/lexa./blob/3bb3c412e06f23a7be27458669ddd1448f35a130/tests/node/remissions-integration.test.js), [testes navegador](https://github.com/pajaao/lexa./blob/3bb3c412e06f23a7be27458669ddd1448f35a130/tests/browser/remissions_integration.py).

## 4. Problemas confirmados

| ID | Gravidade / natureza | Reprodução documentada | Impacto |
|---|---|---|---|
| **ENG-01** | **Alta no extrator bruto; atualmente contida pelo gate experimental.** A remissão `art. 158` no CPP, art. 13-A, é classificada como A com alvo `cpp:158`, embora a enumeração corresponda ao Código Penal (`penal:158`). | Na branch 1A, executar `node --test tests/node/remissions-integration.test.js` e inspecionar o teste **“caso novo CPP13-A revela A contextual incorreto...”**, ou os erros em `docs/remissoes/fase-1a/metrics.json`. | Se a sintaxe atualmente excluída fosse liberada sem correção, criaria vínculo normativo incorreto. A política atual bloqueia essa aresta: **não há indicação de que esse erro entre no índice 1A**. |
| **ENG-02** | **Alta como pendência de liberação, não como bug de código.** A amostra adicional e a política não foram revistas por pessoa especialista independente; aprovação documental permanece pendente. | Conferir `independentHumanReview: false` e `publicationApproval: "pending"` em `metrics.json`, e o limite explícito em `fase-1a.md`. | As métricas não autorizam inferir precisão jurídica global nem aprovar a interface/produção. |
| **ENG-03** | **Baixa no tamanho atual; limitação algorítmica confirmada.** `relationStore().outgoing()` executa `index.edges.filter(...)` a cada chamada, percorrendo as arestas. | Inspecionar `src/optional/remissions-contract.js` na função `relationStore`. | Custo linear por consulta; **não** foi demonstrada lentidão perceptível com as 329 arestas atuais. Escalabilidade é risco, não defeito de desempenho comprovado. |

A ausência de texto jurídico do destino no cache offline parcial é um **estado previsto e testado**, não um defeito confirmado. Também não é defeito o fato de a funcionalidade permanecer desligada na `main`.

## 5. Hipóteses e riscos ainda não comprovados

- **Escopo/contexto:** qualificadores compartilhados, anáforas e contextos normativos externos podem originar outros erros análogos ao ENG-01. Ainda não existe demonstração de uma taxa de falsos positivos no acervo completo; em dúvida, manter a classe excluída.
- **Retenção da PWA:** o mecanismo de reinstalação de recursos por `role` no [service worker](https://github.com/pajaao/lexa./blob/3bb3c412e06f23a7be27458669ddd1448f35a130/src/sw.js) pode antecipar a obtenção de um índice experimental em atualização após uso anterior. É **hipótese a testar**, não transferência excessiva constatada.
- **Desempenho real:** medições de Chromium desktop e Node não representam bateria, RAM total ou latência de aparelhos Android de entrada; mudanças no tempo de biblioteca pronta entre builds não são prova de ganho causal.
- **Validação em camadas:** o contrato no navegador verifica estrutura/geração e hashes da edição, mas não reinterpreta a lei nem substitui o gate do build ou uma revisão jurídica; SHA íntegro não é sinônimo de destino correto.
- **Publicação:** sem evidência de execução de CI para o commit final, os números dos relatórios continuam resultados declarados pelo trabalho anterior, ainda que os scripts e os registros estejam disponíveis para reprodução.

## 6. Recomendações priorizadas

1. **P0 — Obrigatória para ampliar classes ou ativar navegação:** corrigir a atribuição de escopo em grupos sintáticos **com referência normativa expressa**, ou manter esses grupos inelegíveis. Não usar identidade pelo artigo numericamente existente, proximidade temática ou inferência de contexto distante. Incluir regressões com CPP 13-A, CF/ADCT, reprodução legislativa, tachados e lei de edição anterior. Proprietários sugeridos: Engenharia (parser e testes), Integridade Jurídica (aprovação da política).
2. **P0 — Obrigatória antes de publicar relações:** formalizar gate de CI com reconstruções determinísticas, SHA de origem/destino, integridade textual, deduplicação, falha fechada e política de classes aprovadas. Somar **revisão jurídica humana independente**, que o CI não substitui. Nenhum aumento automático de cobertura por simples alteração de flag.
3. **P1 — Validação necessária antes da UX de produção; otimização condicionada à medida:** testar carregamento, atualização, duas edições e offline parcial/completo em aparelhos Android físicos, coletando p50/p95 e heap/transferências. **Opcional:** indexar `outgoing` em memória por origem, ou particionar o JSON, **somente** se a medição de escala justificar. Manter o índice global, ESM e lazy load enquanto atendem ao orçamento.

## 7. Critérios objetivos de aceite

- **ENG-01:** em fixture real do CPP 13-A, `art. 158` jamais produz `cpp:158`; somente `penal:158` se a identidade sintática estiver demonstrada e a classe for aprovada. Sem evidência suficiente, retornar rejeição sem aresta. Exercitar também listas compostas, CF versus ADCT, normas antigas e reprodução riscada. O conjunto de novos casos revisados não pode ter destino incorreto nas classes propostas para habilitação.
- **Integridade de build:** duas execuções com mesmos objetos/versões produzem índice idêntico byte a byte e mesmo SHA; modificar apenas um destino ou os hashes de regras/política muda a geração; remover/renomear destino retira arestas obsoletas; texto, PDFs e históricos jurídicos permanecem inalterados. Corrupção de arquivo, edição incompatível ou contrato inválido impedem todo o carregamento.
- **Distribuição padrão:** build `remissions:false` sem índice, módulos opcionais ou novas requisições de remissões; build experimental mantém manifesto de SHA e exige carregamento explícito. Auditoria B/C/D/E nunca é publicada como recurso do leitor.
- **PWA/ESM:** chamadas simultâneas compartilham carga; falha de rede/SHA permite nova tentativa sem grafo parcial; índice em cache pode ser consultado sem download de todas as normas; ausência offline do destino é identificada; preparação completa inclui índice, módulos e destinos; atualização consentida não mistura grafos e textos de edições diferentes. Testar em dispositivo físico e registrar p50/p95 e memória antes de fixar limites numéricos.
- **Governança:** revisão humana independente documenta as classes e a amostra inédita; aprovação expressa da Coordenação Central antes de retirar `experimental-only`, criar interface de produção ou publicar conexões.

## 8. Pendências para a Coordenação Central

- Aprovar ou rejeitar a **correção restrita de escopo sintático** e definir quais classes podem passar pela nova avaliação; até lá, manter as exclusões da Fase 1A.
- Designar a revisão jurídica humana independente e o critério de aprovação dos destinos. A análise do agente não a substitui.
- Determinar se o gate de CI e as medições Android serão pré-requisitos formais para iniciar/autorizar a Fase 1B; fixar orçamento a partir de evidência móvel.
- Decidir expressamente o destino dos PRs de investigação/integração. A presença de branches à frente da `main` **não** significa merge nem publicação.
- Preservar `docs/coordenacao/decisoes.md` como documento exclusivo da coordenação.

## 9. Parecer final

**Favorável à continuidade da investigação técnica e ao aperfeiçoamento da infraestrutura isolada; não favorável à ativação pública das remissões no estado verificado.** A arquitetura proposta — extração Node determinística no build, elegibilidade conservadora separada, JSON compacto versionado por SHA, ESM lazy e reaproveitamento da PWA — é adequada para o escopo do Lexa. O erro contextual do extrator bruto continua contido, e os custos medidos não justificam reformulação prematura. O avanço depende de tratamento do ENG-01 (ou manutenção do bloqueio), CI reprodutível, revisão jurídica humana independente, validação offline/móvel e aprovação central. Nenhum merge, deploy, alteração legislativa ou de código foi executado para este parecer.
