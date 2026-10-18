# Remissões expressas — Fase 1A

## Resultado e limites de aprovação

Integração técnica experimental, sem interface e **desabilitada no build padrão**. Não há chamada no leitor nem extração no navegador. Não foram modificados textos jurídicos, PDFs, fontes ou históricos. Nenhuma relação foi ativada na aplicação publicada.

Base main: `84c5bb5c5e28c08376e0bf40cf3f3f4b4fd783cf`. Base Fase 0.5: `b414204aadf24d0a0d213365060bc347b3f3847d`. A branch desta fase deriva da segunda; a investigação permanece separada da main. Extrator original 0.5.1, hash `6cf232f85d242a28dd81ff654811106327f13948948b884afe8b7d289d3ae434`, sem reimplementação.

A conferência adicional foi realizada pelo mesmo agente responsável pelo desenvolvimento, sem revisão jurídica humana independente. Portanto, esta fase **não autoriza ativação em produção nem início da apresentação visual da Fase 1B**. Todos os padrões estão restritos ao modo `experimental-only`; o gerador rejeita outro modo. A aprovação independente e a revisão das classes continuam pendentes.

## Arquitetura e arquivos

- `scripts/remissions/eligibility.mjs`: política separada da classificação do extrator, com motivo individual de rejeição.
- `scripts/remissions/build-resource.mjs`: extração, elegibilidade, grafo, serialização, auditoria e vínculos de edição.
- `scripts/build.mjs`: opção explícita `remissions: true`, aplicada após seleção das edições, sobre os mesmos objetos usados nos recursos jurídicos. Não modifica esses objetos.
- `scripts/build-pages.mjs`: inclui o recurso experimental no manifesto SHA-256 e marca os módulos opcionais como lazy. Auditoria retornada, nunca colocada na pasta publicada.
- `src/optional/remissions-contract.js`: validação de contrato e acesso às mesmas arestas por saída e entrada.
- `src/optional/remissions.js`: factory de carregamento; promessa compartilhada para chamadas simultâneas, recuperação após falha.
- `src/optional/remissions-runtime.js`: API interna `loadRemissions()`, sem consumidor no app.
- `src/loading.js`: exporta o verificador SHA já existente; não acrescenta downloads.
- `src/sw.js`: respeita recursos lazy na instalação inicial. O preparo completo explícito inclui os recursos opcionais quando habilitados.
- Helpers de build/medição, testes Node, fixtures anotadas e testes Chromium acrescentados. `scripts/run_browser_tests.py` inclui a nova integração na suíte essencial já usada no CI.

Não houve alteração de app, leitor, estilos, dependências ou módulos originais do extrator.

## Política de elegibilidade 1a.0

A classificação A é necessária, mas insuficiente. São exigidos origem e destinos existentes e individuais, hashes corretos, localização em `paragraphs`, offsets UTF-16 verificáveis, qualificadores e identidade normativa preservados, sem marcação riscada necessária à resolução. Destinos agrupados, evidência editorial e reprodução de texto de outra norma ficam excluídos.

Quatro classes podem entrar **somente no índice experimental**:

| Classe | Limites |
|---|---|
| `parenthetical-article-list` | Lista simples dentro de parênteses; sem qualificadores compartilhados; rejeita contexto normativo externo anterior e qualificação externa imediatamente posterior. |
| `self-qualified-article-list` | Lista simples seguida de “desta Lei”, “deste Código” ou “desta Consolidação”, compatível com a identidade da origem. |
| `adct-self-article` | Referência singular explicitamente a “deste Ato”, dentro do ADCT. |
| `numbered-law-article-list` | Identidade numerada da lei diretamente associada e conferida no catálogo; admite um qualificador inicial de parágrafo explicitamente ligado. |

Sem whitelist de números de artigos. Intervalos, listas complexas, associação contextual distante e padrões sem evidência suficiente permanecem desabilitados. A ausência de tachado não certifica vigência.

Incluídos nos testes reais: CC 927 → CC 186/187; CPC 240 → CC 397/398; CPC 609 → CC 1031; ADCT 54-A → ADCT 54; CDC 104-A → CDC 54-A. CF 18 → ADCT 96 **não entra**: é remissão editorial (“Vide”), não uma classe autorizada desta política.

## Resultado no acervo

4.896 ocorrências candidatas; 272 ocorrências elegíveis, formando **329 arestas únicas** (uma ocorrência pode citar vários destinos). 4.624 rejeições:

| Motivo | Quantidade |
|---|---:|
| Classificação C | 1.857 |
| Classificação D | 1.185 |
| Classe sintática não autorizada | 1.084 |
| Lista/intervalo/sintaxe complexa | 395 |
| Classificação B | 84 |
| Contexto de reprodução de alteração | 8 |
| Classificação E | 7 |
| Editorial ou implícita | 4 |

Ocorrências por classe: parentética 26; autoqualificada 192; ADCT 23; lei numerada 31. Esses totais não representam auditoria jurídica integral das arestas.

## Conferência adicional

Fixtures e critérios em `tests/fixtures/remissions-1a/{additional,sampling}.json`. Seleção de fontes por hash determinístico, filtros lexicais e limite de 650 unidades UTF-16, excluindo artigos das amostras anteriores e um artigo visto informalmente na Fase 0. Não foi seleção de saídas bem-sucedidas do extrator. Anotação do próprio agente, não independente.

19 parágrafos/artigos, 8 legislações, 24 expressões e 25 destinos atuais esperados. Extrator bruto: 24 expressões localizadas, 20 classificações corretas; 20 destinos emitidos, 19 corretos e **1 incorreto** (precisão amostral 95%; cobertura 76%). No CPP 13-A, `art. 158` pertence ao Código Penal na enumeração; o extrator bruto associa indevidamente ao CPP. A política exclui essa classe não qualificada, e o erro não entra no índice experimental. Não foi alterado o extrator para encobrir essa limitação.

Após a política: 7 destinos emitidos, 7 corretos, nenhum incorreto, cobertura 7/25 (28%). Os outros 18 destinos esperados são omitidos conservadoramente; não são todos falhas de detecção. Os contadores genéricos `missedExpressions` do avaliador filtrado também incluem B/C/D deliberadamente excluídos e não devem ser lidos como recall do extrator. Não extrapolar 7/7 para o acervo inteiro.

Exemplos aceitos nessa amostra: Licitações 148 → 147; CPP 13-A → CP 159 e ECA 239; ADCT 90 → ADCT 84; CC 1489 → 41; CPP 685 → 762; CC 1328 → 1297. Permanecem omitidos os intervalos e qualificadores compartilhados complexos, entre outros. Diagnósticos completos e erros estão em `fase-1a/metrics.json`.

## Contrato e integridade

JSON schema 1, modo experimental, hashes do conjunto ordenado de edições, extrator (versão/hash), política (versão/hash/classes), geração e SHA-256 do recurso. A edição inclui hashes de **todas** as normas, inclusive destinos; mudança isolada de destino invalida o índice. A hash da geração vincula essas dependências; o recurso imutável tem seu próprio SHA.

`editions`: pares `[codeId,sha256]`. `occurrences`: `[id,sourceCodeIndex,sourceArticleId,paragraph,start,end,syntaxClass,kind,qualifierSpans,normSpan]`. Proveniência declara `paragraphs`/`utf16`. `edges`: `[sourceCodeIndex,sourceArticleId,targetCodeIndex,targetArticleId,occurrenceIndices]`. Sem cópias integrais do texto. `incoming` contém apenas posições dessas mesmas arestas, derivadas na geração e reconferidas na carga. Duplicações de ocorrência preservam proveniência, sem duplicar a relação.

Validação no navegador confere esquema, catálogo jurídico exato, hashes de geração, classes, tuplas, duplicações e adjacência inversa; congela o objeto validado. Falha de rede, SHA ou contrato rejeita o carregamento inteiro, sem grafo parcial. Build ausente retorna null. API: `outgoing(code,id)`, `incoming(code,id)`, `hasConnections(code,id)`, `occurrence(index)` e `norm(index)`.

Cada build reconstrói as relações; não reaproveita arestas antigas. Simulações cobrem inclusão/exclusão/troca, remoção e mudança de identificador do destino, escopo CF/ADCT, tachado e alteração normativa. Regras e política também invalidam a geração.

## PWA e distribuição

Build padrão: sem índice, módulos opcionais, preload ou chamadas adicionais. Build habilitado: descriptor no catálogo, recurso imutável com SHA, módulos opcionais fora do preload e da instalação inicial. Carregamento somente por chamada explícita; não baixa outras legislações para consultar arestas.

O índice consultado fica disponível offline pela infraestrutura existente. Isso **não implica** que o texto do destino esteja disponível: o teste reproduz esse caso. Preparar explicitamente a biblioteca completa inclui índice, módulos e normas. Atualização exige consentimento; duas abas mantêm índices de suas respectivas edições, incluindo recarga explícita offline da API antiga. A retenção segue os limites existentes da PWA, não garante edições antigas indefinidamente.

## Medições executadas

Dados brutos: `fase-1a/metrics.json` e `fase-1a/browser-metrics.json`. Node 22.23.3, AMD EPYC 9V74; cinco repetições em memória, sem limitação de CPU no Node. Medianas: extração 465,65 ms; elegibilidade 16,22 ms; grafo/serialização 2,01 ms. Build padrão anterior 101,65 ms e posterior 97,57 ms; não caracterizamos essa variação como ganho comprovado.

Índice: **54.795 bytes**, gzip **18.728 bytes**. Módulos opcionais: 4.891 bytes. Dados offline: 16.313.192 → 16.367.987 bytes (+54.795); módulos somam separadamente. Gzip é medida local, não promessa da compressão do GitHub Pages.

Chromium 154.0.8037.57, Playwright, viewport 1366×768, CPU 4×, HTTP local sem limitação de banda, cinco contextos frios por build. Renderização medida até biblioteca pronta; transferências incluem a instalação leve da PWA, separadas do preparo completo. Sem teste de dispositivo físico. Houve outras verificações no mesmo host, portanto tempos são observações, não comparação causal controlada.

| Mediana | Base | Padrão atual | Experimental |
|---|---:|---:|---:|
| Biblioteca pronta (ms) | 880,46 | 822,91 | 652,69 |
| Requisições até instalação | 30 | 30 | 30 |
| Bytes de corpo até instalação | 285.831 | 285.852 | 288.434 |
| Heap da página após GC (bytes) | 1.409.112 | 1.409.152 | 1.411.428 |
| Pedidos iniciais de remissões | 0 | 0 | 0 |

Impacto padrão observado: +21 bytes de código transferido, mesma quantidade de pedidos; **não impacto zero**. Na API experimental: 66,20 ms incluindo importação/carga/verificação; parse isolado 1,10 ms; heap retido adicional 198.004 bytes, incluindo módulos e índice. Heap CDP da página, não RAM total nem memória do service worker. Sem benchmark de longa duração ou móvel físico nesta fase.

## Reprodução

```sh
npm test
python -m unittest discover -s tests -p 'test_*.py'
python scripts/run_browser_tests.py --suite essential
node scripts/build-remissions-experiment.mjs
node scripts/remissions/measure-integration.mjs test-results/remissions-1a.json
python tests/browser/remissions_integration.py
# Requer três diretórios já construídos (base, padrão e experimental):
python tests/browser/remissions_metrics.py BEFORE_SITE dist test-results/remissions-experiment test-results/browser-remissions.json
```

Use Node 22 conforme CI e Chromium/Playwright disponíveis. `npm test` executa também o build de produção. O helper experimental escreve em `test-results/remissions-experiment`; auditoria detalhada fica em `test-results/remissions-audit.json`, fora da pasta publicável. Nunca publicar essa pasta experimental como aprovação implícita.

## Validações e recomendação

Testes Node: 109; Python: 46; suíte essencial Chromium: 12 verificações. Integração Chromium repetida na revisão final: cinco grupos aprovados (carga sob demanda/offline parcial; atualização consentida/duas edições; rede e SHA; preparo completo; build desabilitado). Testes específicos incluem determinismo, imutabilidade jurídica, precisão dos casos autorizados, exclusões, alterações de origem/destino/regras/política, proveniência inválida, contrato e deduplicação.

A integridade é conferida por hashes e comparação dos objetos; nenhum arquivo jurídico foi editado. A suíte funcional não comprova precisão jurídica global. Sem mudança visual, não foram produzidas capturas antes/depois artificiais.

Recomendação: revisar esta infraestrutura isoladamente contra a Fase 0.5, mantendo padrão desabilitado. Antes de Fase 1B, obter revisão humana independente das classes e amostra maior, resolver as limitações de escopo compartilhado do extrator ou continuar excluindo-as, e aprovar expressamente a política. Não ampliar a cobertura apenas para aumentar contagens. Sem merge ou deploy nesta entrega.
