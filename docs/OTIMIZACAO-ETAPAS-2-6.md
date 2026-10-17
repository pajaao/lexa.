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
