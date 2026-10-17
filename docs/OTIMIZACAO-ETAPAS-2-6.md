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
