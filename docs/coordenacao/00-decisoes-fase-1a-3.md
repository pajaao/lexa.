# Coordenação Central — deliberação metodológica da Fase 1A.3

**Data:** 18/10/2026  
**Base examinada:** `validacao/remissoes-fase-1a-2-fechamento`, commit `64862b4b47811ab886396b9b22d4888af49aa4db`.  
**Natureza:** decisão de governança documental e de planejamento. **Não modifica a política de produção**, a gramática, as classes elegíveis ou o leitor.

## Evidências e contexto

- Fechamento técnico-documental da Fase 1A.2: artefatos com 329 arestas experimentais, 272 ocorrências, 353 participações, 354 rejeições amostradas e 683 linhas de revisão humana preservadas.
- Verificação independente documentada no [PR #13](https://github.com/pajaao/lexa./pull/13): três comandos executados, dez testes direcionados aprovados, reprodução dos cinco artefatos, zero divergências detectadas.
- [PR #14](https://github.com/pajaao/lexa./pull/14): Qualidade e Testes recomenda **aprovar com ressalvas** o fechamento técnico-documental, sem homologar os vínculos juridicamente.
- [PR #15](https://github.com/pajaao/lexa./pull/15): Integridade Jurídica recomenda **P1-r–P5-r com ajustes como protocolo de revisão**, mantendo as 30 parentéticas pendentes; revisão assistida por IA, não adjudicação jurídica humana.

Esses PRs foram consultados como fontes; **a sua abertura não equivale a merge ou aprovação de código**.

## Decisões da Coordenação

**D1 — Aprovação metodológica restrita.** A Coordenação **adota P1-r a P5-r como protocolo de investigação e revisão documental**, conforme fundamentação do parecer de Integridade Jurídica da Fase 1A.3 (PR #15). Em síntese:

- **P1-r:** autorreferência exige qualificador literal ligado à referência; eventual convenção de autorreferência local depende de deliberação própria, delimitada por espécie, edição e contexto.
- **P2-r:** antecedente normativo explícito exige ponte sintática inequívoca na unidade textual pertinente, sem antecedente concorrente.
- **P3-r:** diferenciar identidade demonstrada, insuficiente e contraditória, exigindo evidência textual positiva para bloqueio por contradição.
- **P4-r:** examinar runs, reprodução e edições; aviso histórico só no destino não demonstra associação incorreta nem certifica vigência.
- **P5-r:** similaridade de tema, artigo numericamente coincidente ou simples proximidade não demonstram identidade normativa.

Esta aprovação vale **apenas para orientar avaliação humana e futuros testes**, sem tornar essas redações regras automáticas de `eligibility`.

**D2 — Parentéticas na primeira liberação.** As **30 arestas parentéticas de identidade insuficientemente demonstrada** ficam **excluídas de qualquer primeira liberação pública de remissões** enquanto não houver decisão independente documentada sobre a identidade normativa e eventual convenção local. Permanecem identificadas no inventário experimental, sem remoção e sem classificação como erro jurídico demonstrado: **0 candidatas promovidas, 30 pendentes, 0 bloqueadas por contradição positiva demonstrada**.

**D3 — Demais arestas.** Os resultados automatizados `292 consistentes / 8 suspeitas / 29 inconclusivas` pertencem à triagem original; as sete correspondências documentalmente sustentadas por revisão assistida são apenas subsídio. Nenhuma das 329 arestas está homologada automaticamente para exibição. Antes de apresentação pública é necessária revisão jurídica humana independente, com identidade de norma, dispositivo, edição, CF/ADCT quando aplicável, spans, histórico, proveniência e adjudicação de divergências.

**D4 — Preservação e separação de etapas.** Manter as quatro classes atuais, `experimental-only`, build público sem remissões habilitadas, textos jurídicos intocados e separação entre extração, identidade, elegibilidade e apresentação. Não autorizar nesta decisão mudança de código, de política executável, merge ou deploy. Um protótipo de interface isolado com dados artificiais poderá ser proposto em tarefa específica, mas não está autorizado por este documento.

## Pendências e critérios antes de liberação

1. Estabelecer protocolo operacional e responsáveis humanos independentes para a revisão documental das relações, com fontes oficiais e edições correspondentes; as 30 parentéticas exigem decisão individual.
2. Revisar as demais 292 arestas classificadas automaticamente como consistentes, as 354 rejeições amostradas e uma amostra de texto selecionada independentemente do extrator para investigar falsos negativos.
3. Definir apresentação de destinos históricos, revogados, vetados ou alterados, sem indicar vigência automaticamente.
4. Propor implementação e testes adversariais apenas depois de autorização específica, com regressões A01/B01/B02/C01/CPP13-A preservadas.
5. Deliberar separadamente sobre qualquer publicação, merge ou mudança na política executável.

## Planejamento posterior: saneamento estrutural do repositório

Após o registro desta decisão, iniciar **diagnóstico de organização** antes de mover, renomear, excluir ou mesclar qualquer arquivo. Inventariar branches, PRs, seus destinos, dependências, artefatos grandes e documentação; distinguir histórico a preservar de duplicatas comprovadas. Preparar mapa de consolidação por etapas, backups/referências imutáveis e checagem de build/testes. **Nenhuma limpeza destrutiva ou merge automático está autorizada.**

**Veredito:** P1-r–P5-r aprovados como **protocolo documental de investigação**; 30 parentéticas retidas apenas experimentalmente e excluídas da primeira exposição pública; política de produção e publicação permanecem inalteradas.
