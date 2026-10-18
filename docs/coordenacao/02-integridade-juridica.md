# Parecer técnico — Integridade Jurídica (Lexa)

**Frente:** Integridade Jurídica  
**Data do registro:** 18/10/2026  
**Natureza:** parecer técnico de fidelidade textual assistido por IA; **não** constitui revisão jurídica humana independente.  
**Status:** revisão documental; sem autorização para publicar remissões no leitor.

## 1. Identificação e versões examinadas

- Repositório: [pajaao/lexa.](https://github.com/pajaao/lexa.).
- `main` verificada no commit `84c5bb5c5e28c08376e0bf40cf3f3f4b4fd783cf` (base de referência).
- `investigacao/remissoes-fase-0-5`, commit `b414204aadf24d0a0d213365060bc347b3f3847d` (6 commits à frente da `main`, nenhum atrás, na verificação).
- `funcionalidade/remissoes-fase-1a`, commit `3bb3c412e06f23a7be27458669ddd1448f35a130` (9 commits à frente da `main`, nenhum atrás, na verificação).
- Extrator documentado: versão `0.5.1`, SHA-256 `6cf232f85d242a28dd81ff654811106327f13948948b884afe8b7d289d3ae434`; política de elegibilidade: `1a.0`, modo `experimental-only`.
- Registro exclusivo nesta branch: `docs/parecer-integridade`; documento `docs/coordenacao/02-integridade-juridica.md`.

As duas branches funcionais permaneciam **separadas da `main`** na verificação; não inferir integração, aprovação de produto ou deploy a partir da existência do código experimental.

## 2. Escopo e método

Investigar a **fidelidade textual** de remissões expressas: identificação da norma/edição e do artigo de destino; separação CF/ADCT; edições anteriores; tachados e contexto histórico; reproduções de alterações legislativas; qualificadores ambíguos e falsos positivos. O objeto é a correção da correspondência documental, **não** a interpretação da norma, sua vigência ou a criação de conexões por semelhança temática.

Este registro consolida investigação **já realizada**: leitura de `scripts/remissions/{grammar,norms,extract,eligibility}.mjs`, relatórios, métricas e fixtures; confronto textual anterior de exemplos reais com o corpus e páginas oficiais indicadas em `src/catalog.js`. Nenhuma suíte foi reexecutada para produzir este documento. Casos adicionais foram avaliados por leitura textual e das regras, **não** por uma nova execução integral do extrator; suas saídas efetivas e offsets específicos permanecem por comprovar.

## 3. Evidências verificadas

### 3.1 Separação entre extração e elegibilidade

- `extractRemissions()`, em [`extract.mjs`](../..//scripts/remissions/extract.mjs), produz ocorrências A/B/C/D/E, resolução, proveniência de parágrafo/offset UTF-16 e dimensões distintas de histórico (`core`, `qualifiers`, `context`, `state`).
- `applyEligibility()`, em [`eligibility.mjs`](../../scripts/remissions/eligibility.mjs), exige **A mais validações adicionais**: hashes da edição de origem/destino, spans correspondentes aos runs, ausência de tachado indispensável, destinos individuais, classe sintática autorizada e correspondência entre números literais e destinos. A política `experimental-only` admite quatro classes: `parenthetical-article-list`, `self-qualified-article-list`, `adct-self-article`, `numbered-law-article-list`.
- `norms.mjs` distingue referências a CF/ADCT, normas externas catalogadas por número/ano e edições anteriores identificadas; identidade insuficiente ou conflitante pode resultar em abstenção, sem substituição pela edição atual.
- `graph.mjs` só transforma ocorrências A resolvidas e sem impedimento histórico em arestas; na Fase 1A, o recurso resulta do **subconjunto elegível**, não de todas as candidatas A. Ver [`build-resource.mjs`](../../scripts/remissions/build-resource.mjs) e [relatório da Fase 1A](../remissoes/fase-1a.md).

### 3.2 Resultados já documentados (não reexecutados neste parecer)

| Indicador | Valor registrado | Alcance |
|---|---:|---|
| Candidatas do extrator | 4.896 | Varredura automática, não acurácia certificada |
| Candidatas elegíveis na política 1A | 272 | 329 arestas únicas experimentais |
| Rejeições | 4.624 | Incluem B/C/D/E e padrões A não autorizados |
| Nova amostra 1A | 19 parágrafos/artigos, 24 expressões | Anotação do próprio agente desenvolvedor |
| Extrator bruto na amostra 1A | 20 destinos emitidos; 19 corretos; **1 incorreto** | Erro observado, antes da barreira |
| Após política na mesma amostra | 7 destinos emitidos; 7 correspondentes à anotação | 18 dos 25 destinos esperados omitidos por segurança |

Fontes exatas: [`docs/remissoes/fase-1a.md`](../remissoes/fase-1a.md), [`docs/remissoes/fase-1a/metrics.json`](../remissoes/fase-1a/metrics.json), [`tests/fixtures/remissions-1a/additional.json`](../../tests/fixtures/remissions-1a/additional.json), [`docs/remissoes/fase-0-5.md`](../remissoes/fase-0-5.md) e [`docs/remissoes/revisao-diagnosticos.json`](../remissoes/revisao-diagnosticos.json).

**Limite probatório:** 7/7 na amostra filtrada não demonstra precisão jurídica global. Os próprios relatórios declaram ausência de revisão humana independente e de aprovação para exposição ao usuário.

### 3.3 Casos reais adicionais, fora dos três conjuntos de fixtures

Na investigação anterior, foi confrontada a redação de exemplos reais com a identificação das normas nos textos oficiais. Os **artigos de origem** abaixo não figuravam em `phase0.json`, `holdout.json` ou `remissions-1a/additional.json`. A coluna final descreve o **tratamento prudencial esperado**, não uma saída do código comprovada por execução nesses casos.

| Origem | Ponto textual examinado | Resultado conservador esperado |
|---|---|---|
| ADCT 92-A | Referência ao art. 92 do próprio ADCT | Destino `cf/adct-92`, nunca `cf/92`, condicionado à evidência e edição |
| ADCT 92-B | Combina referências a dispositivos da CF e do ADCT, inclusive intervalo | Resolver apenas o escopo explicitamente individualizado; demais, omitir |
| CC 941/942 | Referências internas aos arts. 939/940 e 932 | Omitir até a classe sintática pertinente estar autorizada |
| CPC 1.054 | Art. 503 do CPC atual e arts. 5º, 325 e 470 da Lei 5.869/1973 | Preservar a identidade histórica do CPC de 1973; jamais redirecionar ao CPC atual |
| Lei Maria da Penha 45 | Referência à LEP, art. 152, junto de reprodução de redação alterada | Não transformar cabeçalho/texto reproduzido em remissão ativa |
| ADCT 91, § 1º | Referência ao art. 158 da CF em redação riscada | Não criar aresta atual derivada do trecho riscado |

Fontes oficiais de confronto: [Constituição/ADCT](https://www.planalto.gov.br/ccivil_03/constituicao/constituicao.htm), [CC](https://www.planalto.gov.br/ccivil_03/leis/2002/l10406compilada.htm), [CPC](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2015/lei/l13105.htm), [Lei Maria da Penha](https://www.planalto.gov.br/ccivil_03/_ato2004-2006/2006/lei/l11340.htm). Para cada novo teste executável, registrar a edição exata do Lexa, `paragraph`, `runs` e offsets antes de elevar a constatação a resultado do extrator.

## 4. Problemas confirmados e reprodução

Os identificadores abaixo são exclusivos deste parecer; não reutilizam A01/B01/B02/C01 de outras frentes.

| ID / gravidade | Evidência e reprodução documental | Impacto verificado |
|---|---|---|
| **IJ-C01 / alta no extrator bruto; bloqueado na 1A** | Em CPP 13-A, a referência `art. 158` da enumeração pertence ao **Código Penal**, mas o extrator bruto a atribuiu ao CPP. Conferir a entrada do CPP 13-A em `additional.json` e o erro registrado em `fase-1a/metrics.json`, seção `additional`; confrontar com `fase-1a.md`, seção “Conferência adicional”. | **Um destino bruto incorreto confirmado** na amostra; a política 1A excluiu a classe não qualificada. Não há aresta errada demonstrada nesse índice filtrado. |
| **IJ-C02 / baixa na configuração atual** | Cabeçalho `Art. 61` reproduzido na Lei Maria da Penha 43 ficou **C em vez de E**. Reproduzir documentalmente em `revisao-diagnosticos.json` e no `holdout.json`. | Falso candidato/classificação imperfeita, **sem aresta ativa** documentada. |
| **IJ-C03 / baixa na configuração atual** | No CDC 113, `§§ 4°, 5° e 6°` a acrescentar à Lei 7.347 foi fragmentado como candidato implícito C excedente. Conferir `revisao-diagnosticos.json` e `holdout.json`. | Falso candidato bruto, **sem aresta ativa**. |
| **IJ-C04 / omissão deliberada, não falso positivo** | CDC 1, `art. 48 de suas Disposições Transitórias`: destino textual ADCT 48, mas falta ponte gramatical suportada; classificado C. Mesmo registro em `revisao-diagnosticos.json`. | Perda conhecida de cobertura, em favor da segurança. **Não** corrigir presumindo equivalência ao CDC 48. |

Para execução dirigida futura, conferir diretamente os fixtures congelados e invocar as rotinas do extrator/elegibilidade sobre **essas fontes específicas**, registrando `source`, `location`, `resolution`, `historical` e decisão da política. Não substituir essa conferência por testes verdes genéricos; não reajustar o gold para melhorar métricas.

## 5. Hipóteses e riscos (não confirmados como arestas erradas)

- **IJ-R01 / potencial alta — alterações legislativas depois da introdução:** `amendmentContext()` em `extract.mjs` e a guarda `amendment-reproduction-context` em `eligibility.mjs` consultam somente os **dois primeiros parágrafos** do artigo para determinados padrões de alteração. **Fato:** limite de varredura no código. **Hipótese:** reprodução mais tardia, ou introdução sintaticamente diferente, pode escapar dessa defesa. Não foi demonstrada aresta elegível indevida causada por isso.
- **IJ-R02 / potencial alta — histórico parcial:** `extract.mjs` marca o contexto anterior como `deleted` quando a faixa relevante está inteiramente riscada; uma faixa mista pode não acionar essa condição específica. **Fato:** distinção `deleted`/`mixed` e teste contextual. **Hipótese:** contexto parcialmente riscado indispensável à identidade normativa poderia não ser bloqueado em todo cenário; exige prova com `runs.deleted` e avaliação até o índice.
- **IJ-R03 / média — escopo compartilhado:** enumerações com CF/ADCT, várias leis ou qualificadores propagados exigem atribuição por ocorrência, não por proximidade. O erro confirmado do CPP 13-A sustenta manter vedadas classes não qualificadas; não comprova falha nas quatro classes atuais.
- **IJ-R04 / governança — anotações não independentes:** gold e revisão da amostra foram preparados pelo agente que desenvolveu as regras. Há risco de viés de validação. O conjunto filtrado não foi revisado por jurista independente.

## 6. Recomendações priorizadas

**Obrigatórias antes de ativação visual/produção (P0):**

1. **Manter `experimental-only`** e bloquear a apresentação das relações ao usuário até aprovação explícita da Coordenação e revisão jurídica humana independente da política e de amostra nova.
2. Criar testes adversariais isolados para IJ-R01 e IJ-R02; se revelarem arestas indevidas, corrigir bloqueios **antes** de qualquer expansão da elegibilidade, sem alterar o texto legal.
3. Preservar a abstenção para identidade/edição/escopo incertos, referências históricas, alterações reproduzidas e tachados; nunca encaminhar `C/D/E/B` por aproximação.
4. Congelar e identificar novas amostras com `code/article/paragraph`, hash de edição, span UTF-16, trechos e runs; revisão humana separada de desenvolvimento, acompanhada de adjudicação de divergências.

**Aperfeiçoamentos opcionais (P1/P2; depois das barreiras):**

- Ampliar a gramática para `de suas Disposições Transitórias`, listas e qualificadores compartilhados **somente após** fixtures novos, com resultado negativo seguro por padrão.
- Distinguir no diagnóstico “cabeçalho reproduzido”, “referência a norma anterior”, “destino não catalogado” e “sintaxe não suportada”, sem transformar melhor diagnóstico em autorização de link.
- Ampliar a amostragem por legislação e classe e registrar cobertura separada de precisão, sempre com contagem de destinos incorretos.

## 7. Critérios objetivos de aceite

| Verificação | Critério |
|---|---|
| IJ-C01 — escopo entre normas | CPP 13-A nunca produz `cpp/158` para a expressão que remete ao CP; qualquer classe não resolvida permanece inelegível |
| IJ-C02/IJ-C03 — falso candidato | Cabeçalhos e parágrafos de inserção podem permanecer em auditoria, mas geram **zero arestas**; correção futura para E não altera artificialmente o gold |
| IJ-C04 — omissão segura | CDC 1 não aponta para `cdc/48`; só ligar `cf/adct-48` após sintaxe expressa, edição e teste aprovados |
| IJ-R01 — reprodução tardia | Para entrada adversarial com instrução de alteração após o 2º parágrafo, **zero vínculo a cabeçalho/dispositivo reproduzido** |
| IJ-R02 — tachado misto | Variar tachado do núcleo, qualificador, norma e contexto essencial: nenhum fragmento histórico necessário produz aresta atual |
| CF versus ADCT | Casos ADCT 92-A/92-B são confrontados com `scope`; inexiste troca entre `cf/N` e `cf/adct-N` por coincidência numérica |
| Edições anteriores | CPC 1.054 não aponta artigos da Lei 5.869/1973 para a edição 2015; identidade externa é preservada ou o link é omitido |
| Proveniência/edição | Para cada elegível, `text.slice(start,end)` corresponde aos runs UTF-16 e aos hashes jurídicos; mudança isolada em destino invalida o índice |
| Aprovação jurídica | Revisão humana independente documentada das classes e amostra inédita: **zero destinos errados entre os autorizados na amostra de aceite**, omissões e divergências publicadas no relatório interno, sem inferir garantia estatística global |

Os testes devem ser direcionados e reproduzíveis. Aprovação de suíte funcional não substitui a conferência documental.

## 8. Pendências para a Coordenação Central

1. Designar revisor(es) humano(s) independente(s) para as quatro classes de elegibilidade e para novos artigos de origem, sem reaproveitar apenas os fixtures conhecidos.
2. Decidir formalmente se a estratégia **“na dúvida, omitir”** permanece requisito absoluto da primeira liberação (recomendação: sim).
3. Condicionar a futura Fase 1B à aprovação explícita da política, à resolução/mitigação demonstrada dos riscos IJ-R01/IJ-R02 e à validação de edição/escopo.
4. Manter relatório de candidatos B/C/D/E fora do conteúdo público de navegação, preservado para auditoria, e decidir o ritual de revisão a cada nova edição jurídica.

Nenhuma destas decisões é tomada por este parecer; não modificar `docs/coordenacao/decisoes.md`.

## 9. Parecer final

**Parecer: favorável à continuidade da infraestrutura isolada; desfavorável à ativação dos vínculos no leitor neste momento.** A separação técnica entre extração e elegibilidade é coerente com fidelidade textual, mas IJ-C01 confirma que um artigo numericamente reconhecido pode apontar para a norma errada; IJ-R01 e IJ-R02 ainda exigem testes de segurança. Preferir omitir uma remissão certa a criar uma correspondência documental falsa.

**Condições de avanço:** manter a política restritiva; reproduzir e decidir os casos adversariais; revisar classes e amostra inédita por pessoas independentes; obter aprovação central explícita para qualquer fase visual ou publicação. Este documento não autoriza alteração de código, merge, deploy ou mudança de redação legislativa.
