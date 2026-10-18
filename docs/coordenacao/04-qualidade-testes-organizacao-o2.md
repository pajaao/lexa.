# Parecer — Qualidade e Testes — Verificação final da Fase O2

**Data:** 18/10/2026. **Natureza:** revisão assistida por IA, dirigida aos diffs dos [PR #18](https://github.com/pajaao/lexa./pull/18) e [PR #19](https://github.com/pajaao/lexa./pull/19). **Base documental deste parecer:** head do PR #18, derivado de `main`. Não é homologação jurídica nem autorização de merge.

## Veredito

**APROVAR COM RESSALVAS** a Fase O2 quanto ao escopo documental e à segregação entre `main` e a branch experimental. Não foram identificadas alterações executáveis nos dois diffs. A conferência integral independente de todos os links relativos permanece pendente; a amostra verificada resolveu corretamente.

## Evidências verificadas

- **PR #18 contra `main`:** quatro arquivos Markdown: `README.md` (somente dois links de navegação), `docs/INDEX.md`, `docs/coordenacao/INDEX.md`, `docs/coordenacao/01-engenharia-organizacao-o2.md`. Nenhuma alteração de `src/`, `scripts/`, `tests/`, `data/`, `sources/`, `public/`, workflows, PWA ou política.
- **PR #19 contra `validacao/remissoes-fase-1a-2-fechamento`:** dois arquivos Markdown: novo `docs/remissoes/INDEX.md` e correção pontual em `docs/remissoes/fase-0-5.md`. Comparar o PR #19 com `main` apresenta muitos arquivos experimentais por ancestralidade, mas **não são alterações introduzidas pelo PR #19 relativamente à sua base correta**. Não retargetar ou mesclar diretamente na `main`.
- **ORG-A01:** comparação textual das versões base/head confirmou a substituição de `../../tests/fixtures/remissions/phase 0.json` por `../../tests/fixtures/remissions/phase0.json`. A existência do fixture `tests/fixtures/remissions/phase0.json` foi confirmada na branch do PR #19. O fixture não integra o diff e não foi renomeado.
- **Links relativos:** destinos representativos confirmados por leitura GitHub nas branches respectivas: `docs/ESTRUTURA.md`, `docs/MANUTENCAO.md`, `docs/BASELINE-DESEMPENHO.md`, `docs/coordenacao/INDEX.md`, `tests/fixtures/remissions/phase0.json`, `docs/remissoes/fase-1a.md`, `docs/remissoes/fase-1a-1.md`, `docs/remissoes/fase-1a-2.md`, `scripts/remissions/README.md`. A checagem independente **não cobriu exaustivamente** todos os links. Engenharia relata 38/38 na principal e 43/43 na experimental, não reproduzidos integralmente nesta revisão.
- **Estados documentais:** `docs/INDEX.md` distingue documentação incorporada, registros históricos e links externos a experimentos ainda não incorporados. `docs/coordenacao/INDEX.md` discrimina PRs, bases e estados; `docs/remissoes/INDEX.md` afirma expressamente sua natureza experimental. Links para PR/branch não são tratados como merge ou homologação.

## Riscos e ressalvas

1. **Verificação de links:** antes do merge documental, completar verificação de todos os caminhos relativos na árvore exata de cada PR, inclusive diretórios e âncoras quando relevantes. Links externos fixados por SHA oferecem maior estabilidade que branches móveis.
2. **Ancestralidade:** o PR #19 tem como base uma branch que contém o experimento. Retargetá-lo para `main` ou integrar seu head diretamente nela pode incorporar código experimental, apesar do diff documental em sua base correta. Para levar apenas o índice à `main`, exigir PR isolado com diff reavaliado.
3. **Estado temporal:** a matriz de PRs registra um corte datado; revalidar estados, commits e links no momento da decisão.
4. **Execução:** foram realizadas consultas e comparações via GitHub, leitura de conteúdo e verificação pontual de caminhos. **Não** foram executados `npm test`, testes Python/browser, builds, benchmarks ou deploy, por não haver alteração de código. As contagens de links da Engenharia são **relatadas**, não testes independentes desta frente.

## Critérios de aceite e encaminhamento

**Atendidos:** diff exclusivamente documental; preservação do fixture e do corpus; ORG-A01 correta; distinção explícita entre documentos correntes, históricos e experimentais; nenhuma alteração indireta de comportamento demonstrada.

**Pendente recomendado antes do merge:** conferência exaustiva dos links relativos, e confirmação das bases/heads dos PRs no momento da integração. Não é necessária nova auditoria jurídica nem regressão funcional integral apenas por esta O2.

**Conclusão:** aprovar com ressalvas os dois PRs como propostas documentais isoladas, sem incorporar por esta decisão qualquer experimento, sem autorizar alteração de elegibilidade, merge ou deploy. A Coordenação Central decide a integração.
