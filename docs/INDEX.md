# Índice da documentação — Lexa

**Referência:** `main` em 18/10/2026, commit `84c5bb5c5e28c08376e0bf40cf3f3f4b4fd783cf`. Este índice distingue documentação incorporada na base de pareceres e experimentos existentes apenas em outros refs. A criação do índice em um PR **não significa que ele já esteja em `main`**.

## Introdução e arquitetura — documentação corrente
- [README principal](../README.md): produto, instalação, navegação, fontes e desenvolvimento.
- [Estrutura do projeto](ESTRUTURA.md): diretórios, ESM, build, versões e política de publicação.

## Operação e manutenção — documentação corrente
- [Manutenção](MANUTENCAO.md): execução, fontes, PWA, testes e implantação.
- [Monitoramento das legislações](../monitor/README.md): Planalto, propostas de revisão, dados oficiais e histórico.
- [Monitoramento do STF](../monitor/stf/README.md): automação de súmulas pausada; diagnóstico manual.
- [Workflows](../.github/workflows/verify.yml): verificações de PR; [publicação](../.github/workflows/deploy-pages.yml) condicionada a push na `main`.

## Fontes jurídicas e proveniência — documentação corrente
- [Manifesto de PDFs](../sources/manifest.json), [manifesto oficial](../sources/official-manifest.json), [súmulas](../sources/sumulas-manifest.json) e [relatório de importação](../sources/import-report.json).
- [Catálogo](../src/catalog.js), [dados arquivados](../data/archive/), [edições oficiais](../data/official/), [histórico](../data/history/). Estes são **dados e código de referência**, não documentos descartáveis.
- [Configuração das fontes monitoradas](../monitor/sources.json). Edição incorporada, edição publicada e vigência são conceitos diferentes.

## Desempenho e otimizações — registros históricos, preservados
- [Baseline de desempenho](BASELINE-DESEMPENHO.md), [revisão de desempenho](REVISAO-DESEMPENHO.md) e [etapas 2–6](OTIMIZACAO-ETAPAS-2-6.md).
- [Dados de baselines](baselines/) e [medição UX etapa 2](medicoes/ux-etapa-2-carregamento.json). Não atualizar métricas antigas para refletir resultados novos.

## UX e histórico de melhorias — registros históricos
- [Refinamentos etapa 1](UX-REFINAMENTOS-ETAPA-1.md) e [etapa 2](UX-REFINAMENTOS-ETAPA-2.md).

## Testes e verificações — documentação corrente
- [Instruções de manutenção e execução](MANUTENCAO.md), [comandos npm](../package.json), [suíte Node](../tests/node/), [suíte Python](../tests/python/) e [suíte browser](../tests/browser/).
- [Verificação CI](../.github/workflows/verify.yml). Testes descritos em pareceres não equivalem a execuções próprias.

## Remissões expressas — **experimentais, não incorporadas à `main`**
- [Histórico experimental e artefatos da Fase 0.5 ao fechamento 1A.2](https://github.com/pajaao/lexa./tree/64862b4b47811ab886396b9b22d4888af49aa4db/docs/remissoes) (**branch de fechamento**, commit fixado).
- [Relatório da Fase 1A.2](https://github.com/pajaao/lexa./blob/64862b4b47811ab886396b9b22d4888af49aa4db/docs/remissoes/fase-1a-2.md), [fechamento](https://github.com/pajaao/lexa./blob/64862b4b47811ab886396b9b22d4888af49aa4db/docs/remissoes/fase-1a-2-fechamento.md) e [protocolo](https://github.com/pajaao/lexa./blob/64862b4b47811ab886396b9b22d4888af49aa4db/docs/remissoes/fase-1a-2-fechamento/protocolo-revisao.md).
- [Deliberação metodológica 1A.3 — PR #16 aberto](https://github.com/pajaao/lexa./pull/16). O documento não altera regras executáveis nem homologa relações.
- **Estado:** quatro classes existentes, política `experimental-only`, inventário de 329 arestas e 30 parentéticas pendentes. Sem remissões ativadas no leitor da `main`. A primeira liberação exige decisão central e revisão jurídica humana independente.
- [Índice da branch experimental — PR documental separado](https://github.com/pajaao/lexa./tree/docs/engenharia-o2-remissoes/docs/remissoes) (referência à proposta, **não** conteúdo incorporado à `main`).

## Pareceres e Coordenação — Drive como repositório administrativo
- [Índice dos pareceres, bases e PRs](coordenacao/INDEX.md).
- [Parecer O1 no Google Drive](https://docs.google.com/document/d/1uFfKWgjsr_PI0IGksg2JlgM46ZHfOBJX-cu-x8Jx7dE/edit), preservado após [encerramento do PR #17 sem merge](https://github.com/pajaao/lexa./pull/17); [commit original](https://github.com/pajaao/lexa./blob/8c93c9dd9fabfa4296e1faff417f04a3ab2650da/docs/coordenacao/01-engenharia-organizacao-o1.md).
- **Situação pós-T3 (18/10/2026):** #7–#12, #14, #15, #17 e #20 encerrados sem merge; seus pareceres estão preservados no Drive. #13 e #16 seguem abertos para destinação técnica; #18 e #19 seguem como propostas documentais, em bases distintas. [Registro de saneamento T3](https://docs.google.com/document/d/1qWamkDUgSPCnJs4X245ZyvNrZ06M0JjsIsfg8Vh-OhE/edit). Não há incorporação desses pareceres à `main` por efeito de seu encerramento.
- A presença de um link externo para PR/branch **não** constitui aprovação, merge ou publicação. Para documentos históricos não incorporados, usar URL com commit fixo ou PR, nunca caminho relativo local inexistente.

**Regra de manutenção:** atualizar este índice após confirmar refs/commits e diffs efetivos, sem reescrever históricos, inventários ou relatórios originais.
