# Índice da documentação — Lexa

**Escopo:** documentação corrente da `main` e ligações explícitas para registros históricos. Referências a commits antigos identificam a proveniência dos documentos, não o estado atual da aplicação.

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

## Remissões expressas — funcionalidade temporariamente suspensa

As remissões expressas foram retiradas temporariamente do Lexa e **não integram a interface nem a documentação operacional corrente**. Sua eventual retomada é uma decisão futura; os protótipos e pareceres anteriores não autorizam ativação, não constituem homologação jurídica e não alteram o texto das normas.

Para preservar a rastreabilidade sem sobrecarregar a documentação de uso, os registros experimentais permanecem consultáveis pelo [histórico de desenvolvimento das remissões (commit fixado)](https://github.com/pajaao/lexa./tree/64862b4b47811ab886396b9b22d4888af49aa4db/docs/remissoes) e pelo [PR #19](https://github.com/pajaao/lexa./pull/19). A Coordenação também registrou um [backup ZIP no Drive](https://drive.google.com/file/d/1SwW70b05p6H7pEmtmrH9_eLRfwOQYGAx/view) e um [inventário de arquivos e SHAs](https://docs.google.com/document/d/1WWYtqP3ot84Wq0Lr9u0HwkvWOUUbIIJxGyHz9KlsL-0/edit); **o conteúdo do ZIP e seus hashes ainda não foram verificados independentemente**. Nenhum desses registros é parte do produto publicado.

## Pareceres e Coordenação — Drive como repositório administrativo
- [Índice dos pareceres, bases e PRs](coordenacao/INDEX.md).
- [Parecer O1 no Google Drive](https://docs.google.com/document/d/1uFfKWgjsr_PI0IGksg2JlgM46ZHfOBJX-cu-x8Jx7dE/edit), preservado após [encerramento do PR #17 sem merge](https://github.com/pajaao/lexa./pull/17); [commit original](https://github.com/pajaao/lexa./blob/8c93c9dd9fabfa4296e1faff417f04a3ab2650da/docs/coordenacao/01-engenharia-organizacao-o1.md).

**Regra de manutenção:** atualizar este índice após confirmar refs/commits e diffs efetivos, sem reescrever históricos, inventários ou relatórios originais.
