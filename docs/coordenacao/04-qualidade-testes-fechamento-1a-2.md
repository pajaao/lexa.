# Parecer final — Qualidade e Testes — Fechamento técnico-documental da Fase 1A.2

**Data:** 18/10/2026  
**Frente:** Qualidade e Testes (revisão assistida por IA)  
**Branch examinada:** `validacao/remissoes-fase-1a-2-fechamento`  
**Objeto:** verificador e critérios de aceite do fechamento, confrontados com o parecer de execução independente registrado no [PR #13](https://github.com/pajaao/lexa./pull/13), `docs/coordenacao/05-execucao-independente-fechamento-1a-2.md`.

## Veredito

**APROVAR COM RESSALVAS o fechamento técnico-documental da Fase 1A.2.** A pendência anterior de execução separada do agente de implementação foi atendida pelo registro da Coordenação Central. A aprovação é limitada à integridade e à reprodutibilidade computacional dos artefatos, **não** à validação jurídica das remissões.

## Evidências e critérios de aceite

| Critério | Evidência e situação |
|---|---|
| Testes direcionados | PR #13 relata execução de `python -m unittest discover -s tests -p 'test_remissions_closure.py'`, exit code 0, **10 testes aprovados**. Atendido conforme registro de execução independente. |
| Reprodução | PR #13 relata `node scripts/reproduce_remissions_closure.mjs /tmp/lexa-closure-repro`, exit code 0; duas gerações idênticas entre si e aos cinco artefatos aprovados. Atendido conforme registro. |
| Verificação com população | PR #13 relata `python scripts/verify_remissions_closure.py docs/remissoes/fase-1a-2 --snapshot /tmp/lexa-closure-repro/snapshot.json`, exit code 0, `ok: true`, `divergences: []`. Atendido conforme registro. |
| Contagens | 329 arestas, 272 ocorrências, 353 participações, 354 rejeições amostradas, 683 registros de revisão humana, 203 estratos. Conferidas pela execução relatada. |
| Isolamento do PR #13 | Diff inspecionado: somente `docs/coordenacao/05-execucao-independente-fechamento-1a-2.md` adicionado, sem código, inventário ou corpus alterado. Atendido. |
| Separação técnico/jurídica | Expressamente mantida no documento de execução e no protocolo. Atendido. |

**Distinção de evidências:** esta frente inspecionou o código do verificador, os testes, o relatório do fechamento e o conteúdo/diff do PR #13. **Não reexecutou nesta revisão os três comandos**; seus resultados são os observados e documentados pela Coordenação Central em ambiente isolado (Python 3.13.5; Node.js 22.16.0). Não se apresentam testes relatados como reexecução própria.

## Ressalvas e riscos residuais

1. **Independência limitada:** o Python verifica hashes, IDs, CSV/JSON, spans UTF-16, campos de revisão e seleção determinística por lógica própria; o snapshot suplementar ainda provém do pipeline. Não certifica autenticidade externa, vigência, correção semântica ou completude das remissões.
2. **Rastreabilidade do ambiente:** o PR #13 documenta comandos, saídas e códigos de sucesso, mas não constitui certificação externa do ZIP/ambiente. Não bloqueia o aceite no escopo acordado.
3. **Robustez diagnóstica:** entradas estruturalmente malformadas podem provocar exceções em vez de divergências estruturadas. Melhoria futura, sem defeito demonstrado nos artefatos aprovados.
4. **Revisão jurídica pendente:** 30 parentéticas seguem pendentes de decisão; as 292 consistentes e as demais relações não foram homologadas por revisão jurídica humana independente. Não se pode inferir aprovação jurídica de testes verdes.

**Falha técnica bloqueante confirmada:** nenhuma na evidência examinada. **Pendências técnicas para o aceite delimitado:** nenhuma demonstrada após o registro do PR #13. **Pendências de produto/jurídicas:** adjudicação humana, convenção parentética, tratamento histórico e autorização expressa para eventual exposição.

## Encaminhamento e limites

Registrar o fechamento técnico-documental como concluído, mantendo inventários e regras preservados. Conservar as quatro classes, `experimental-only`, abstenção em caso de identidade/condição histórica incerta e remissões desligadas no leitor. Esta aprovação **não autoriza** Fase 1B, alteração de elegibilidade, ativação de links, merge ou deploy. Decisões vinculantes pertencem exclusivamente à Coordenação Central.
