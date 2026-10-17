# Otimização técnica — etapas 2 a 6

A etapa 1 foi preservada, não reimplementada. A referência é o relatório de 135 amostras em `docs/baselines/chromium-cpu4x-2026-10-17.json`. As alterações desta sequência estão separadas em commits; não se destinam à publicação sem revisão humana.

## Etapa 2 — busca global

**Causa:** a busca carregava e preparava o leitor completo de todas as normas, para depois construir outro índice de parágrafos. Filtros de área também aguardavam coleções que não participariam do resultado.

**Decisão:** gerar índices compactos derivados dos runs originais. Cada campo mantém texto integral, tipo e intervalos riscados; títulos de divisões são compartilhados por referência. A busca e as referências usam esses arquivos, preservando a ordem, o primeiro campo correspondente e os trechos originais. O leitor continua abrindo somente os JSONs jurídicos originais. A área selecionada limita os índices baixados; referências com sigla usam apenas a coleção indicada. A retomada pode validar a referência sem pré-carregar a norma completa.

Os novos arquivos são imutáveis, têm hash verificado e entram no manifesto offline. Nesta etapa intermediária o pacote offline completo fica maior por conter também os índices derivados; a etapa 6 trata o download automático e a disponibilidade explícita, sem remover a opção de biblioteca completa offline.

**Validação:** testes Node e 46 testes Python aprovados; verificações de interface, carga seletiva, leitura, busca global, favoritos, cópia e contrato do benchmark passaram. A PWA passou após corrigir no teste a observação de uma instalação que podia ter começado pelo evento `online`. Há comparação exaustiva de textos/riscos de todos os campos dos índices e de resultados para várias consultas; a fixture dos 52 resultados de “dignidade” permanece inalterada.

**Medição intermediária:** três rodadas dos cenários de interface, CPU 4×, workers bloqueados, mesma metodologia da baseline. Medições completas e limitações constarão na comparação final; não se trata de estimativa nem de um limite de CI.

| Indicador | Baseline (5 rodadas) | Etapa 2 (3 rodadas) |
| --- | ---: | ---: |
| Primeira busca fria, mediana | 1538,0 ms | 1122,0 ms |
| Primeira busca fria, bytes de rede | 8.946.085 | 7.234.938 |
| Heap após a primeira busca/GC | 34.442.364 bytes | 24.275.336 bytes |
| Busca posterior, mediana | 264,8 ms | 301,9 ms |

O custo da primeira busca e o volume/heap caíram; a busca posterior ficou mais lenta nesta amostra intermediária. A etapa 4 investigará o acesso aos campos normalizados, sem alterar resultados para esconder esse custo.

## Etapa 3 — leitor

**Causa:** o índice lateral era reconstruído a cada paginação e cada seção fazia uma nova varredura dos artigos. A abertura também montava textos derivados de todos os artigos, mesmo sem busca.

**Decisão:** mapas de artigos/seções/escopos e árvores são reutilizados por identidade dos dados; o cache é fraco e não prende edições descartadas. O texto derivado é calculado apenas quando lido. A seleção de artigos é reutilizada enquanto query, escopo, divisão e favoritos não mudam. Paginação simples atualiza a posição sem substituir o índice lateral; buscas e filtros mantêm a lógica de expansão existente.

**Validação:** Node e 46 testes Python passaram; as dez verificações de navegador passaram. O teste de hierarquia compara parágrafos em todas as coleções e agora verifica que o nó do índice continua conectado após paginar. Há testes de reaproveitamento e invalidação do modelo e de marcadores sem alteração de texto.

**Medição intermediária (3 rodadas, frio):**

| Cenário | Mediana (ms) |
| --- | ---: |
| reader_open_civil:cold | 441.9 |
| reader_next_civil:cold | 98.3 |
| reader_previous_civil:cold | 115.9 |
| reader_open_cpc:cold | 452.2 |
| reader_next_cpc:cold | 114.7 |
| reader_previous_cpc:cold | 116.4 |
| reader_open_clt:cold | 445.2 |
| reader_next_clt:cold | 163.4 |
| reader_previous_clt:cold | 131.2 |

## Etapa 4 — memória e indexação

**Causa:** todos os leitores abertos permaneciam no catálogo durante a sessão; promessas concluídas também ficavam guardadas. A busca consultava um WeakMap por campo normalizado a cada nova consulta.

**Decisão:** conjunto de trabalho LRU de três leitores completos, com proteção do leitor ativo contra respostas atrasadas. Descartar significa soltar referências derivadas do catálogo, nunca modificar arrays/textos originais. Favoritos são resolvidos nos índices compactos e recarregam o original ao abrir a entrada. Os mapas/modelos do leitor têm chaves fracas pelos arrays de dados. Promessas mantêm apenas tarefas em andamento. Campos normalizados são guardados por índice em arrays, evitando consultas repetidas ao cache por campo. Getters não capturam a coleção original inteira quando bastam seus parágrafos e uma flag.

Os índices compactos do acervo são mantidos após a busca global, pois ela precisa cobrir todas as normas e consultas seguintes não devem repetir parse/download de cada arquivo. Não foi introduzido cache ilimitado de resultados por palavra nem um limite artificial que elimine ocorrências.

**Validação:** Node, 46 testes Python e os fluxos essenciais passaram; a sessão longa validou limite de três leitores, recarga de artigo descartado, favoritos persistentes e a mesma fixture de 52 resultados. A falha do teste de PWA foi tornada determinística: o servidor agora arma a falha antes de reativar a conexão, impedindo uma instalação válida acidental entre o deploy de teste e a ativação do erro.

**Memória intermediária:** uma sessão controlada por compilação, CPU 4×, duas voltas pelas 14 coleções, snapshots do heap da página após GC. Antes do limite (etapa 3), após a segunda volta: 38.496.712 bytes e 14 leitores. Durante a etapa 4: 31.589.728 bytes e 3 leitores. Não é mediana nem medida de RAM total, e os getters receberam depois um refinamento adicional de retenção. A validação final repete a sessão na arquitetura consolidada. Não se afirmou que o crescimento entre snapshots caracteriza vazamento.

## Etapa 5 — módulos e build

**Causa:** o build removia imports/exports por expressões regulares e concatenava módulos em um escopo global. Uma nova forma de import/export, um comentário ou um nome repetido podia quebrar o pacote. O leitor e a apresentação estavam concentrados no controlador principal.

**Decisão:** ESM nativo, sem framework ou dependência de bundler. Os módulos são copiados sem transformação para um namespace SHA-256, com modulepreload para evitar descoberta serial de dependências. Apenas os adaptadores de catálogo/coleções são gerados para o navegador, sem importar bases jurídicas no shell. O template tem slots literais únicos validados. O servidor reconhece os módulos imutáveis. `reader.js`, `presentation.js`, `clipboard.js` e `history-store.js` separam responsabilidades; o controlador principal caiu de cerca de 449 para 249 linhas. O HTML ficou com 53.407 bytes nessa etapa, mas sua transferência total inclui os módulos externos — não se apresenta a redução do HTML como redução equivalente de rede.

**Validação:** Node, 46 testes Python e as onze verificações de navegador passaram, incluindo a sessão longa e PWA. O teste de build inicializa a home com import nativo, mantém a injeção de teste de escape HTML e compara byte a byte os módulos publicados com os de origem (exceto os dois adaptadores gerados). O teste de alteração exclusiva de CSS continua preservando nomes/bytes dos dados e módulos. Os testes acessam exports pelo loader de módulos; nenhuma API de debug foi exposta no produto. O harness também continua aceitando as baselines inline anteriores.

## Etapa 6 — armazenamento offline

**Causa:** a primeira instalação baixava automaticamente todas as normas, mesmo sem consulta. A arquitetura ESM também exige manter arquivos da mesma edição durante atualizações e entre abas.

**Decisão:** instalação inicial verifica e guarda apenas o shell e os módulos. Conteúdos consultados são guardados com SHA-256; o rodapé lista as normas disponíveis e oferece preparo explícito do acervo inteiro, com tamanho estimado. O download usa concorrência três e compartilha tarefas em andamento; arquivos imutáveis podem vir do cache HTTP, e arquivos de edições anteriores só são reutilizados após verificação. Bibliotecas completas anteriores continuam completas antes de oferecer atualização. Edições parciais preservam as categorias/coleções já guardadas. Falhas de instalação não ativam um shell incompleto; falhas no preparo explícito preservam arquivos válidos e permitem repetir. Uma edição anterior é retida quando há outra aba, evitando mistura de módulos durante leitura; o número de edições não cresce indefinidamente.

A biblioteca completa agora inclui índices compactos e originais de leitura: seu tamanho é maior que antes. O ganho é separar essa escolha do carregamento inicial e evitar leitores completos na busca. PDFs e fontes externas continuam dependendo de rede. O armazenamento do navegador pode ser removido pelo próprio navegador; não é garantia de arquivo permanente.

**Validação:** teste PWA cobre subpasta, offline, atualização consentida, favoritos/preferências, reutilização, isolamento de caches e rejeição de shell/JSON adulterados. Novo teste `offline_policy.py` cobre visita inicial sem JSON jurídico, leitura consultada offline e preparo explícito com busca global offline. Integra o conjunto essencial de CI. O benchmark mantém os cenários de interface; acrescenta `offline_first_visit` e pede explicitamente a biblioteca completa em `offline_preparation`. Esses dois cenários não devem ser confundidos.

## Reprodução e limites

```sh
npm test
python3 -m unittest discover -s tests -p 'test_*.py'
python3 -m pip install -r scripts/requirements-browser.txt
python3 -m playwright install --with-deps chromium
python3 scripts/run_browser_tests.py --suite all
python3 tests/browser/performance.py --runs 5 --cpu 4 --output test-results/performance.json
python3 tests/browser/memory_session.py --output test-results/memory.json
```

Use `LEXA_CHROMIUM=/caminho/do/chromium` para escolher o executável; neste ambiente foi usado `/usr/bin/chromium`. O Chromium instalado pelo Playwright pode ser de outra versão; registre a diferença antes de comparar. Não execute testes pesados concorrentes com o benchmark. A baseline original está em `docs/baselines/chromium-cpu4x-2026-10-17.json`; a medição final e a sessão longa têm arquivos próprios na mesma pasta.

CPU 4× da página via CDP, viewport móvel 375×812, loopback sem compressão nem limitação de rede, cinco rodadas e medianas por cenário. Cache frio significa contexto novo; quente significa cache HTTP preparado fora da janela medida, com modelo JavaScript reiniciado. Busca posterior mantém os dados em memória. Service worker bloqueado nas medições de interface, permitido apenas nos cenários offline. O tempo inclui debounce/automação até prontidão funcional. Heap V8 após GC não representa RAM total ou pico; worker, DOM e GPU não foram medidos. A CPU do worker não foi limitada separadamente. O contêiner é compartilhado e não representa um celular físico.

A modularização troca um script inline por módulos com preload: aumenta o número de requisições de shell. Os tempos locais não estimam diretamente o custo em conexões móveis com alta latência. A primeira busca textual abrangente ainda precisa dos índices de todas as coleções; consultas de referência, título/sigla e filtros evitam carregar leitores desnecessários. Não foram truncados resultados para melhorar as medições.

## Revisão humana e continuidade

Revisar manualmente instalação/atualização nos navegadores móveis reais, sobretudo Safari/iOS, limites de armazenamento e sessões com abas abertas durante mais de uma atualização. Os testes automatizados desta execução usam Chromium; não certificam todos os navegadores. Conferir o novo estado parcial/completo no rodapé, sem depender de PDFs externos offline. Favoritos e preferências continuam locais no mesmo formato.

A CI executa verificações funcionais, sem reprovação por tempos absolutos. As execuções locais não são evidência de execução no GitHub Actions. A branch não publica: publicar exige merge humano posterior na principal. Dados jurídicos, PDFs, fontes e históricos não foram alterados. Não há IA, telemetria ou novo serviço externo no produto.

Próximas investigações devem partir de uso real: custo de parse dos índices em celulares modestos, latência dos módulos em rede móvel e cotas de cache nos navegadores suportados. Manter a comparação de resultados jurídicos e a verificação de hashes em qualquer futura compactação.

## Comparação final executada

Cinco rodadas por cenário, 140 amostras finais (130 de interface e 10 offline), contra 135 amostras na baseline (130 de interface e 5 offline). Zero erros JavaScript, requisições falhadas ou pendentes no benchmark. Revisão medida `e251e83a5ba41fed83a7cff58a7330629d897926`; condições completas nos JSONs.

| Cenário | Antes (ms) | Depois (ms) | Variação |
| --- | ---: | ---: | ---: |
| `library_initial:cold` | 392.4 | 389.8 | -0.7% |
| `global_search_first:cold` | 1538.0 | 1045.7 | -32.0% |
| `global_search_subsequent:cold` | 264.8 | 279.1 | +5.4% |
| `global_search_repeated:cold` | 259.1 | 257.8 | -0.5% |
| `reader_open_civil:cold` | 526.9 | 395.2 | -25.0% |
| `reader_next_civil:cold` | 205.6 | 97.9 | -52.4% |
| `reader_previous_civil:cold` | 208.4 | 108.8 | -47.8% |
| `reader_open_cpc:cold` | 452.9 | 349.1 | -22.9% |
| `reader_next_cpc:cold` | 161.1 | 111.2 | -31.0% |
| `reader_previous_cpc:cold` | 162.6 | 95.3 | -41.4% |
| `reader_open_clt:cold` | 504.3 | 411.2 | -18.5% |
| `reader_next_clt:cold` | 184.1 | 156.0 | -15.3% |
| `reader_previous_clt:cold` | 158.6 | 133.6 | -15.8% |
| `library_initial:warm_http` | 182.9 | 209.2 | +14.4% |
| `global_search_first:warm_http` | 1494.2 | 1029.7 | -31.1% |
| `global_search_subsequent:warm_http` | 267.5 | 265.0 | -0.9% |
| `global_search_repeated:warm_http` | 274.3 | 266.9 | -2.7% |
| `reader_open_civil:warm_http` | 447.6 | 299.8 | -33.0% |
| `reader_next_civil:warm_http` | 193.4 | 94.7 | -51.0% |
| `reader_previous_civil:warm_http` | 209.9 | 119.9 | -42.9% |
| `reader_open_cpc:warm_http` | 356.5 | 253.7 | -28.8% |
| `reader_next_cpc:warm_http` | 152.4 | 95.3 | -37.5% |
| `reader_previous_cpc:warm_http` | 152.9 | 98.0 | -35.9% |
| `reader_open_clt:warm_http` | 451.7 | 327.5 | -27.5% |
| `reader_next_clt:warm_http` | 202.9 | 151.2 | -25.5% |
| `reader_previous_clt:warm_http` | 162.8 | 128.7 | -20.9% |

A primeira busca fria passou de **1.538,0 para 1.045,7 ms** (−32,0%); a transferência de rede passou de **8.946.085 para 7.234.938 bytes** (−19,1%). Heap após essa busca/GC: **34.442.364 → 24.329.720 bytes** (−29,4%). Buscas posteriores e paginação continuam sem downloads jurídicos. A busca posterior fria ficou **5,4% mais lenta**; a repetida ficou praticamente estável. Não se declara ganho universal.

A home fria ficou estável em tempo (392,4 → 389,8 ms), mas transferiu **136.100 → 157.628 bytes** (+15,8%) devido aos módulos e headers adicionais. A home quente ficou **14,4% mais lenta** (182,9 → 209,2 ms), embora sua rede tenha caído para 54.279 bytes pela reutilização dos módulos. Esse é o custo observado da troca do concatenador frágil por ESM; conexões reais precisam de nova avaliação.

O novo primeiro preparo parcial transferiu **278.607 bytes de corpos pela origem**, mediana **457,5 ms**. O preparo automático completo anterior transferia **9.272.819 bytes**: queda de **97,0%** no volume automático da visita. Não confundir com o render da home. O preparo **completo explícito** agora transferiu **16.458.407 bytes**, mediana **839,9 ms**, contra 9.272.819/412,3 ms antes. O aumento decorre dos índices além dos originais e é uma escolha explícita; não representa redução do armazenamento completo. Trabalho do worker não tem a mesma limitação de CPU das interações.

Na sessão longa final, após duas voltas: **29.179.904 bytes** de heap da página e **3 leitores completos**, contra **38.496.712 bytes/14 leitores** na observação intermediária anterior ao limite (−24,2%). Trata-se de uma sessão por compilação, sem mediana, não de RAM total. Os índices de todas as coleções permanecem após a busca global para preservar abrangência e rapidez nas consultas seguintes.

Resultados brutos: [benchmark final](baselines/optimization-final-2026-10-17.json), [baseline](baselines/chromium-cpu4x-2026-10-17.json) e [sessão longa final](baselines/memory-final-2026-10-17.json).

## Verificações finais

- Node 22.23.3: `npm test` aprovado, 12 testes, incluindo build de produção e integridade de PDFs/dados/módulos.
- Python 3.12.14: 46 testes aprovados.
- Chromium: 13 verificações aprovadas na suíte completa (nove essenciais e quatro extensas), incluindo persistência de favoritos, hierarquia, sessão longa, PWA e atualização parcial com duas abas. O teste de duas abas troca o namespace ESM, remove os módulos antigos do servidor e confirma que a outra aba ainda os acessa offline pelo cache da edição anterior.
- Benchmark: 140 amostras, cinco rodadas, sem erros JavaScript ou falhas/pendências de requisição.
- YAMLs de workflows/action analisados com PyYAML; alterações verificadas com `git diff --check`.
- Comparação de arquivos com a base `54be7bd`: nenhum diff em `data/`, `sources/` ou `monitor/`. Testes também verificam hashes e correspondência dos textos derivados.
- Não houve coleta de novas fontes, execução de deploy, merge ou alteração direta da principal.
