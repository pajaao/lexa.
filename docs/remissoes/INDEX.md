# Índice experimental das remissões expressas — Lexa

**Base:** `validacao/remissoes-fase-1a-2-fechamento` no commit `64862b4b47811ab886396b9b22d4888af49aa4db`. Este índice pertence a **uma proposta documental**, não a `main`; não autoriza publicação nem altera o extrator.

## Histórico cronológico e status

| Etapa | Relatório | Papel e status |
|---|---|---|
| 0.5 | [Investigação determinística](fase-0-5.md) | Léxico, identidade de norma, offsets UTF-16, histórico e amostras congeladas. Experimental |
| 1A | [Integração opcional](fase-1a.md) | Build Node, contrato SHA/ESM, índice e carregamento sob demanda. `experimental-only` |
| 1A.1 | [Robustez adversarial](fase-1a-1.md) | Correções A01/B01/B02/C01/CPP13-A; extrator 0.5.2 e política 1a.1. Experimental |
| 1A.2 | [Auditoria das arestas](fase-1a-2.md) | 329 arestas, 272 ocorrências, 353 participações; auditoria, não homologação |
| Fechamento 1A.2 | [Fechamento](fase-1a-2-fechamento.md) | Verificação documental/computacional, sem alteração do inventário |
| 1A.3 | [Deliberação metodológica — PR #16 pendente](https://github.com/pajaao/lexa./pull/16) | P1-r–P5-r como protocolo documental, não política executável; 30 parentéticas pendentes |

## Artefatos e reprodutibilidade

- **0.5:** [resultados](resultados.json), [diagnósticos](revisao-diagnosticos.json) e [isolamento](isolamento.json). Fixtures congeladas em [`tests/fixtures/remissions/`](../../tests/fixtures/remissions/).
- **1A:** [métricas de integração](fase-1a/metrics.json), [métricas browser](fase-1a/browser-metrics.json).
- **1A.1:** [comparativo de métricas](fase-1a-1/metrics-after.json), [antes](fase-1a-1/metrics-before.json), [delta de elegibilidade](fase-1a-1/eligibility-delta.json) e [casos adversariais](fase-1a-1/adversarial-after.json).
- **1A.2:** [inventário JSON](fase-1a-2/arestas.json), [arestas CSV](fase-1a-2/arestas.csv), [rejeições amostradas](fase-1a-2/rejeicoes-amostra.json), [revisão humana ainda não preenchida](fase-1a-2/revisao-humana.csv), [manifesto/hashes](fase-1a-2/manifesto.json) e [validações](fase-1a-2/validacoes.json).
- **Fechamento:** [30 parentéticas](fase-1a-2-fechamento/parenteticas.csv), [protocolo de revisão](fase-1a-2-fechamento/protocolo-revisao.md), [verificação registrada](fase-1a-2-fechamento/verificacao.json).
- **Implementação/avaliação:** [README do extrator](../../scripts/remissions/README.md); [auditoria](../../scripts/audit-remissions/run.mjs); [verificador independente do algoritmo](../../scripts/verify_remissions_closure.py); [reprodutor e snapshot](../../scripts/reproduce_remissions_closure.mjs); [testes de fechamento](../../tests/test_remissions_closure.py).
- **Comandos históricos (não executados nesta O2):** `node --test tests/node/remissions*.test.js`; `python scripts/verify_remissions_closure.py docs/remissoes/fase-1a-2 --output /tmp/verificacao.json`; `node scripts/reproduce_remissions_closure.mjs /tmp/lexa-closure-repro`; `python -m unittest discover -s tests -p 'test_remissions_closure.py'`. Execução em diretórios de saída novos, sem sobrescrever artefatos aprovados; conferir instruções e versões no [fechamento](fase-1a-2-fechamento.md).

## Invariantes e restrições

1. **Quatro classes:** `parenthetical-article-list`, `self-qualified-article-list`, `adct-self-article`, `numbered-law-article-list`; política executável `experimental-only`.
2. **Inventário imutável nesta fase:** 329 arestas, 272 ocorrências, 353 participações. A amostra inclui 354 rejeições e 683 linhas para revisão humana.
3. **Parentéticas:** 30 arestas / 26 ocorrências, nenhuma promovida nem excluída do histórico; permanecem pendentes de decisão para a primeira liberação, conforme [PR #16](https://github.com/pajaao/lexa./pull/16). Sem inferência temática ou troca arbitrária de edição.
4. Preservar SHA-256 de edições, regras, política, texto jurídico, corpus, CSV/JSON e offsets UTF-16. **Não** recriar dados para “ajustar” números históricos.
5. A aceitação do fechamento é **técnico-documental**, não revisão jurídica humana independente. A interface de remissões permanece desativada no build padrão e no leitor publicado em `main`.
6. Pareceres históricos preservados no [Google Drive](https://drive.google.com/drive/folders/1-UUemCijzHqp0vp1BzpMHATu7hvYzM3x), com origem técnica rastreável: [PR #11](https://github.com/pajaao/lexa./pull/11), [#12](https://github.com/pajaao/lexa./pull/12), [#13](https://github.com/pajaao/lexa./pull/13), [#14](https://github.com/pajaao/lexa./pull/14), [#15](https://github.com/pajaao/lexa./pull/15), [#16](https://github.com/pajaao/lexa./pull/16) — #11, #12, #14 e #15 encerrados sem merge na T3, #13 e #16 ainda abertos e pendentes de destinação técnica. Os documentos de parecer encerrados permanecem no Drive, não incorporados à base experimental pelo encerramento dos PRs.

**Estado pós-T3 (18/10/2026):** PRs #7–#12, #14, #15, #17 e #20 encerrados sem merge; #13 e #16 em análise técnica, #18 e #19 ainda abertos para integração documental em bases separadas. [Parecer de Qualidade O2 no Drive](https://docs.google.com/document/d/1Q-biANYskXdOR9fQ4NyqhvFDb9ZrsPtDEyO1u4bCDks/edit); [destinação T3](https://docs.google.com/document/d/1DyWRaqs75iSIglF2oOb6k9NRx2tA8lohhV0zki_Phsg/edit). **Nenhuma das 329 arestas está automaticamente homologada para exibição; as 30 parentéticas permanecem excluídas da primeira liberação pública e exigem revisão jurídica humana independente.** Este índice e o experimento não estão incorporados à `main`.

**ORG-A01:** apenas o caminho de link no relatório 0.5 foi corrigido de `phase 0.json` para `phase0.json`. Nenhum fixture foi renomeado ou modificado.
