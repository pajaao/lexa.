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

---

## 10. Adendo — revisão independente da Fase 1A.1 (18/10/2026)

**Objeto e comparação:** `correcao/remissoes-fase-1a-1` (`5b218d9dc38c94194e0a13c51984d2b6d14c2f14`) contra `funcionalidade/remissoes-fase-1a` (`3bb3c412e06f23a7be27458669ddd1448f35a130`). Revisão **restrita ao diff, relatório e testes adversariais**, sem repetir auditoria geral. Não se trata de revisão jurídica humana independente.

### 10.1 Correções confirmadas nos artefatos e no código

| Identificador | Situação anterior | Fase 1A.1 | Conclusão |
|---|---|---|---|
| A01 — identidade numérica conflitante | `art. 147 desta Lei nº 8.666/1993` associava-se indevidamente à Lei 14.133/2021, inclusive após gate | Classe C; identidade de 1993 preservada e associação rejeitada | Corrigido no caso |
| A02 — reprodução de diploma não identificado | `(art. 186)` gerava CC 186 e passava no gate | Classe C; não presume norma hospedeira | Corrigido no caso |
| B01 — ADCT de 1967 | `art. 84` atribuía-se ao ADCT de 1988 e passava no gate | Classe B; edição 1967 externa e sem aresta | Corrigido no caso |
| B02 — histórico parcialmente riscado | Contexto misto indevidamente `clear`; variante com “ver” já barrada pelo gate | Contexto `mixed`, classe C; variantes “consultar”, “aplicar”, “considerar” também barradas | Corrigido nos casos |
| C01 — reprodução legislativa tardia | Terceiro parágrafo com reprodução atribuía `art. 147` à norma hospedeira | Guarda de reprodução em todos os parágrafos; classe C e sem aresta | Corrigido no caso |
| CPP 13-A — escopo coordenado | `art. 158` da enumeração do Código Penal produzia `cpp/158` no extrator bruto | Classe C por escopo coordenado não suportado, sem `cpp/158`; não se inventa `penal/158` | Corrigido por abstenção |

O código observado em [`norms.mjs`](../../scripts/remissions/norms.mjs), [`extract.mjs`](../../scripts/remissions/extract.mjs), [`context.mjs`](../../scripts/remissions/context.mjs) e [`eligibility.mjs`](../../scripts/remissions/eligibility.mjs) implementa as respectivas barreiras, com versões `0.5.2` e `1a.1`. As **quatro classes de elegibilidade** permanecem inalteradas e a política continua `experimental-only` com `independentReview: pending`.

### 10.2 Regressões e limites de evidência

Foi realizada nesta revisão **verificação comparativa dos JSONs já gravados**, sem executar novamente suítes ou extrator: os 14 casos adversariais têm saídas consistentes com suas expectativas; seis casos antes emitiam destinos A indevidos no extrator bruto (A01/A02/B01/B02/C01/CPP13A) e nenhum o faz depois. Quatro dos seis também atravessavam a elegibilidade antiga (A01/A02/B01/C01). Os controles positivos C03/C04 mantêm destinos autorizados; B03 continua a distinguir `cf/84` de `cf/adct-84` e permanece inelegível.

No [`eligibility-delta.json`](../remissoes/fase-1a-1/eligibility-delta.json), o build padrão é assinalado como idêntico byte a byte, o conjunto de arestas elegíveis é idêntico (**329 → 329; zero inclusão/remoção**), e as três variantes históricas B02 deixam de atravessar o gate. Esta revisão conferiu a **consistência dos registros**, não reproduziu a execução que os gerou. A contagem de 18 testes adversariais, 127 testes Node, 46 Python e 12 verificações Chromium aprovadas é **resultado relatado pela implementação**, não executado por esta frente. Não houve nova falha ou regressão demonstrada nos casos examinados.

### 10.3 Riscos ainda não comprovados e bloqueios

- A identificação de reproduções permanece **lexical** e conservadora; formulações fora dos padrões conhecidos ainda podem exigir novos casos de teste. A exclusão do artigo inteiro pode omitir vínculos legítimos, mas previne atribuição indevida.
- Escopos compartilhados, anáforas, intervalos, qualificadores complexos, referências a normas anteriores e evidência histórica insuficiente devem permanecer bloqueados. O caso CPP 13-A não autoriza inferir a relação com o CP apenas pela enumeração.
- A igualdade das 329 arestas elegíveis não prova sua correção jurídica integral; a amostra não constitui auditoria humana independente e não elimina falsos positivos desconhecidos.
- A Coordenação deve exigir revisão jurídica humana independente das quatro classes e amostra inédita, além de aceite explícito para qualquer etapa de exposição pública.

**Veredito da Integridade Jurídica para a Fase 1A.1: APROVAR COM RESSALVAS a correção técnica isolada.** Os erros direcionados estão neutralizados nos casos adversariais comparados, sem expansão artificial das relações. **Não aprovar ativação no leitor, retirada de `experimental-only`, merge automático ou início incondicional da Fase 1B.** Na dúvida sobre norma, edição, escopo ou histórico, omitir o vínculo.

**Fontes principais:** [relatório 1A.1](../remissoes/fase-1a-1.md), [antes](../remissoes/fase-1a-1/adversarial-before.json), [depois](../remissoes/fase-1a-1/adversarial-after.json), [delta de elegibilidade](../remissoes/fase-1a-1/eligibility-delta.json), [testes adversariais](../../tests/node/remissions-adversarial.test.js).

---

## 11. Adendo — revisão documental da Fase 1A.2 (18/10/2026)

**Escopo isolado:** 8 arestas «Suspeita» e 29 «Inconclusiva» do inventário da branch `validacao/remissoes-fase-1a-2`; base experimental 1A.1 (extrator 0.5.2 e política 1a.1). Sem reauditoria das outras 292 arestas, sem reexecução dos testes e sem edição de corpus ou regras. **Parecer assistido por IA, não adjudicação jurídica humana independente.**

### 11.1 Síntese e regra de decisão

- **7 correspondências documentais sustentadas:** referências com qualificador explícito de norma/escopo; quatro têm **alertas históricos de destino**, que não constituem por si erro de associação, e três são falsos alarmes de antecedente normativo concorrente.
- **0 associações indevidas demonstradas** entre as 37.
- **30 identidades insuficientemente demonstradas:** CPP 211 → CPP 561 (oitava suspeita) e 29 referências parentéticas. Todas possuem números de artigos expressos e contextos com diferentes graus de apoio, mas **não nomeiam a norma na própria parentética**. Sua contextualização não deve ser confundida com prova independente de identidade.
- Os graus «alta» e «moderada» abaixo são julgamentos qualitativos da evidência documental, **não** probabilidades ou interpretação de vigência.

Os números refletem **este parecer** sobre as 37 arestas; não substituem as categorias de triagem automática (292/8/29) e não foram escritos em campos reservados a revisores humanos.

### 11.2 Registro individual das 37 arestas

Os IDs abaixo são SHA-256 completos do inventário. O campo de evidência reproduz o **núcleo literal**, acrescido do qualificador adjacente quando existente. Cada localização, contexto integral, offsets, runs e hash de edição podem ser consultados no [inventário JSON](../remissoes/fase-1a-2/arestas.json) e na [tabela CSV](../remissoes/fase-1a-2/arestas.csv). A tabela apresenta recomendação para o **inventário experimental**, nunca autorização para tornar o vínculo visível no leitor.

| ID da aresta | Origem → destino | Evidência textual | Avaliação individual | Conclusão, certeza e pendência |
|---|---|---|---|---|
| `ab1800adcea2cb1f378a59124c3f9204a6ef83f30beccd37505101504a214f75` | `cf/adct-107-A → cf/adct-107` | `art. 107 deste Ato das Disposições Constitucionais Transitórias` | Qualificador expresso «deste Ato» identifica ADCT; aviso de revogação no destino é alerta histórico, não erro. | **Correspondência documental sustentada**; certeza alta; manter experimental e observar histórico |
| `984240bcd1aede0ceddab59f81effe59515673eed1f3a99f2634b4620aa1d73f` | `civil/1070 → civil/1016` | `art. 1.016` | Responsabilidade de administradores aponta contextualmente ao CC 1.016; falta identificação literal da norma. | **Identidade insuficientemente demonstrada**; certeza moderada de contexto, insuficiente de identidade; investigar, não promover |
| `4574b985b1674808be72d20ee9297d75394bfae3b506369f10f83b2caa5211b3` | `civil/1243 → civil/1207` | `art. 1.207` | Soma de posses remete contextualmente ao CC 1.207; sem identidade nominal. | **Identidade insuficientemente demonstrada**; certeza moderada de contexto, insuficiente de identidade; investigar, não promover |
| `9b0f16aa743a6c865355efd40e3f980ad712df2139e772f837dc54110d5d1bdb` | `civil/1328 → civil/1297` | `art. 1.297` | Limites e cercas correspondem ao CC 1.297; norma não expressa. | **Identidade insuficientemente demonstrada**; certeza moderada de contexto, insuficiente de identidade; investigar, não promover |
| `dab44af07be62dac6118e4e28630293ee4313a2f8ab97f0427f6205a6dda1d8d` | `civil/1410 → civil/1390` | `arts. 1.390 e 1.399` | Lista «arts. 1.390 e 1.399» sobre usufruto; destino 1.390 está numerado mas norma implícita. | **Identidade insuficientemente demonstrada**; certeza moderada de contexto, insuficiente de identidade; investigar, não promover |
| `14024433eb2c8c561556e63c15d051f217544e08fdc06843a66e0c1604cef033` | `civil/1410 → civil/1399` | `arts. 1.390 e 1.399` | Mesma lista de usufruto; destino 1.399 numerado mas norma implícita. | **Identidade insuficientemente demonstrada**; certeza moderada de contexto, insuficiente de identidade; investigar, não promover |
| `36fd0fe2fece3062ee12cc30c61f97d835de488129d7673027918cf59b13f54f` | `civil/1489 → civil/41` | `art. 41` | «pessoas de direito público interno» concorda com CC 41; identidade da norma implícita. | **Identidade insuficientemente demonstrada**; certeza moderada de contexto, insuficiente de identidade; investigar, não promover |
| `05134d14e90d4f570066f6bfb31e1edbd12ef3c4b60e2139a0709549ae23228e` | `civil/1649 → civil/1647` | `art. 1.647` | Autorização conjugal corresponde ao CC 1.647; identidade implícita. | **Identidade insuficientemente demonstrada**; certeza moderada de contexto, insuficiente de identidade; investigar, não promover |
| `305e994f3fa81f2b16b1afef8daf9a3f98071a309219e08ea5445b1e947fc6e2` | `civil/1935 → civil/1913` | `art. 1.913` | Legado de coisa de terceiro relaciona-se ao CC 1.913; identidade implícita. | **Identidade insuficientemente demonstrada**; certeza moderada de contexto, insuficiente de identidade; investigar, não promover |
| `65ef4bebd14f3eee6f495f05b6a4d91ee2fe8f75af77eaacf5459a6e133c4a6d` | `civil/442 → civil/441` | `art. 441` | Redibição do contrato corresponde ao CC 441; identidade implícita. | **Identidade insuficientemente demonstrada**; certeza moderada de contexto, insuficiente de identidade; investigar, não promover |
| `f0f62fd9032d60f614ef40d6613c3ff4fc034e7b984ff458fb5cb11c244703c9` | `civil/613 → civil/610` | `art. 610` | Empreitada de lavor corresponde ao CC 610; identidade implícita. | **Identidade insuficientemente demonstrada**; certeza moderada de contexto, insuficiente de identidade; investigar, não promover |
| `1f7de70fec57729f06201841d9ddd7768b1521b04da453492ca672e83d92dec1` | `civil/65 → civil/62` | `art. 62` | Fundação e bases do patrimônio correspondem ao CC 62; identidade implícita. | **Identidade insuficientemente demonstrada**; certeza moderada de contexto, insuficiente de identidade; investigar, não promover |
| `3f262ffd667143d6489a28bc0db3979d4691a34a0b4893b514f30b15b838c0da` | `civil/927 → civil/186` | `arts. 186 e 187` | «ato ilícito (arts. 186 e 187)» sustenta contexto local de CC 186; diploma não nomeado. | **Identidade insuficientemente demonstrada**; certeza moderada de contexto, insuficiente de identidade; investigar, não promover |
| `47819f75b43ea96dfaf6bab27b6d57f17af69e3becdf6667e5f843290b4c61c8` | `civil/927 → civil/187` | `arts. 186 e 187` | Mesmo parêntese, CC 187 contextualmente associado; diploma não nomeado. | **Identidade insuficientemente demonstrada**; certeza moderada de contexto, insuficiente de identidade; investigar, não promover |
| `afc09e5125599223cd5fee960c2fe6e155da7a9bfda200ea81744bb9e6a7ee40` | `civil/982 → civil/967` | `art. 967` | Registro de empresário corresponde ao CC 967; identidade implícita. | **Identidade insuficientemente demonstrada**; certeza moderada de contexto, insuficiente de identidade; investigar, não promover |
| `68d6145bc7297ea8ff83c09b2409bbb11e14a99e8e9097e7fcc417bed4b97415` | `civil/985 → civil/1150` | `arts. 45 e 1.150` | «arts. 45 e 1.150» em registro constitutivo; CC 1.150 é plausível, norma implícita. | **Identidade insuficientemente demonstrada**; certeza moderada de contexto, insuficiente de identidade; investigar, não promover |
| `f15766feaa9f2de8043572be2213067990bd4b2355ec51180f3d80b24aa8991b` | `civil/985 → civil/45` | `arts. 45 e 1.150` | Mesmo parêntese sobre registro constitutivo; CC 45 plausível, norma implícita. | **Identidade insuficientemente demonstrada**; certeza moderada de contexto, insuficiente de identidade; investigar, não promover |
| `179bfc3d71578b6754c4feae095b5cb13ea8a115e09eb77b80570d0ae6215904` | `clt/413 → clt/384` | `art. 384 desta Consolidação` | «desta Consolidação» identifica CLT; destino riscado/revogado requer apresentação histórica. | **Correspondência documental sustentada**; certeza alta; manter experimental e observar histórico |
| `b55518db38675c61f04b9b7e0afe55f5a71de752c3ef3d79f0c16957e54f13c0` | `clt/461 → clt/510` | `art. 510 desta Consolidação` | «desta Consolidação» identifica CLT; anotação histórica no destino não altera identidade. | **Correspondência documental sustentada**; certeza alta; manter experimental e observar histórico |
| `b36e2db5e4feea74dd60889bf2c52e994cae61c864197f9a27c6ea3e02681d24` | `cpc/499 → civil/757` | `arts. 441, 618 e 757 da Lei nº 10.406, de 10 de janeiro de 2002 (Código Civil)` | Lei 10.406/2002 (Código Civil) nomeada após a lista; nota posterior no destino não invalida a referência documental. | **Correspondência documental sustentada**; certeza alta; manter experimental e observar histórico |
| `24d4b0d972047db1d923dd87fedf4a3d63df0a73415fb8c3b0b5cfb27cc2c069` | `cpp/143 → cpp/63` | `art. 63` | Juiz cível e execução da condenação correspondem ao CPP 63; norma implícita. | **Identidade insuficientemente demonstrada**; certeza moderada de contexto, insuficiente de identidade; investigar, não promover |
| `5bd25c9fda178907e5fffd99f3398ed01762b49774fdbf1b634fb805b5b93b0e` | `cpp/211 → cpp/561` | `art. 561` | Parentética sem nome normativo; referência ao tribunal favorece CPP, mas identidade continua implícita; destino possui nota histórica. | **Identidade insuficientemente demonstrada**; certeza moderada de contexto, insuficiente de identidade; investigar, não promover |
| `256bcf90b9c76cbba169e81f4645a469bbd24c77dd278771c21cb5aa96a6ca63` | `cpp/46 → cpp/16` | `art. 16` | Devolução do inquérito remete contextualmente ao CPP 16; norma implícita. | **Identidade insuficientemente demonstrada**; certeza moderada de contexto, insuficiente de identidade; investigar, não promover |
| `11dd1a17f2abab9f5b9f1241a6328b27d7b5f4dca83f132495fcec75933a79af` | `cpp/571 → cpp/447` | `art. 447` | Anúncio do julgamento corresponde ao CPP 447; norma implícita. | **Identidade insuficientemente demonstrada**; certeza moderada de contexto, insuficiente de identidade; investigar, não promover |
| `275ff85de4f8c5504c075435367e1b9c8b3e8517636ba8d9b5424bdb1aaecd36` | `cpp/597 → cpp/374` | `arts. 374 e 378` | Lista «arts. 374 e 378» e medidas de segurança; norma implícita; conferir histórico. | **Identidade insuficientemente demonstrada**; certeza moderada de contexto, insuficiente de identidade; investigar, não promover |
| `4b27feeee5a2039418af5a78b2f27af945a971af0c19fea423af344a0f375d3f` | `cpp/597 → cpp/378` | `arts. 374 e 378` | Mesma lista; CPP 378 tem disciplina correspondente; norma implícita; conferir histórico. | **Identidade insuficientemente demonstrada**; certeza moderada de contexto, insuficiente de identidade; investigar, não promover |
| `ba033735dc48f56ae6b9996cac101b793801fa407b09bddb370a3de642a697fa` | `cpp/68 → cpp/63` | `art. 63` | Execução de sentença condenatória corresponde ao CPP 63; norma implícita. | **Identidade insuficientemente demonstrada**; certeza moderada de contexto, insuficiente de identidade; investigar, não promover |
| `dcdd94ae896f3a4d5e75186cc4ac4546ac970fb90d5a41f7bee677254b8b9df4` | `cpp/68 → cpp/64` | `art. 64` | Ação civil corresponde ao CPP 64; norma implícita. | **Identidade insuficientemente demonstrada**; certeza moderada de contexto, insuficiente de identidade; investigar, não promover |
| `115efa0e0b4f26aeafa6a65fcbb453536904321fa6ad5660a339006ef79b4787` | `cpp/685 → cpp/762` | `art. 762` | Medida de segurança detentiva e estabelecimento adequado correspondem ao CPP 762; norma implícita; conferir histórico. | **Identidade insuficientemente demonstrada**; certeza moderada de contexto, insuficiente de identidade; investigar, não promover |
| `fef0a22d3ef0972892b49f5ff7f9d7a54ff2156602e6b32d3f8bd0c0d9b1d0a0` | `eca/161 → eca/24` | `art. 24 desta Lei` | «desta Lei» identifica o ECA; artigos do CC estão em referência anterior, sem propagação. | **Correspondência documental sustentada**; certeza alta; manter experimental e observar histórico |
| `e5657a6f208424c875b1902df5dddf404a5447208c9c664266e690ab4e5425bc` | `eca/190-F → eca/190-A` | `art. 190-A desta Lei` | «desta Lei» identifica o ECA; Lei 9.296/1996 qualifica instituto diferente. | **Correspondência documental sustentada**; certeza alta; manter experimental e observar histórico |
| `817b18083a7ac568762aba56ae2325898b6ff69dee4b7395552eca045fd65ca4` | `lep/118 → lep/111` | `artigo 111` | Regime após soma de penas corresponde à LEP 111; norma implícita. | **Identidade insuficientemente demonstrada**; certeza moderada de contexto, insuficiente de identidade; investigar, não promover |
| `4d8d236575f59f82ef0a31ea1b3d8d212ffa261401e76a5a69b1574731cd8f40` | `lep/170 → lep/168` | `artigo 168` | Multa descontada da remuneração corresponde à LEP 168; norma implícita. | **Identidade insuficientemente demonstrada**; certeza moderada de contexto, insuficiente de identidade; investigar, não promover |
| `01171b012a7e3af49383c08a5cc14c16a1da4bbab60b996057e4d5a790f03dd3` | `lep/78 → lep/26` | `artigo 26` | Conceito de egresso corresponde à LEP 26; norma implícita. | **Identidade insuficientemente demonstrada**; certeza moderada de contexto, insuficiente de identidade; investigar, não promover |
| `1398314e40857d2a30899cca2e603790f926e22845fe88d715be30a629580fc7` | `licitacoes/1 → licitacoes/178` | `art. 178 desta Lei` | «desta Lei» identifica Lei 14.133/2021, embora a frase também mencione Lei 13.303/2016. | **Correspondência documental sustentada**; certeza alta; manter experimental e observar histórico |
| `530ccf051384717fc5a866cd83b918e8f6d3795725fd7039206e49536e355b31` | `penal/318 → penal/334` | `art. 334` | Contrabando/descaminho e CP 334; norma implícita e histórico do destino requer atenção. | **Identidade insuficientemente demonstrada**; certeza moderada de contexto, insuficiente de identidade; investigar, não promover |
| `2953dbf31d396bb7cec44d669a9d28ccc2cb67da70bd66b6ed24d122a06f04ff` | `penal/97 → penal/26` | `art. 26` | Inimputabilidade corresponde ao CP 26; norma implícita. | **Identidade insuficientemente demonstrada**; certeza moderada de contexto, insuficiente de identidade; investigar, não promover |

### 11.3 Distinções necessárias

**Alertas históricos legítimos, sem associação indevida comprovada:** ADCT 107-A → 107; CLT 413 → 384; CLT 461 → 510; CPC 499 → CC 757. As notas de revogação ou texto riscado no **destino** não apagam uma remissão expressa preservada na **origem** nem demonstram que a identidade normativa esteja errada. Sua futura apresentação demanda mecanismo de contexto histórico, sem conclusão automática de vigência.

**Falsos alarmes de antecedente concorrente:** ECA 161 → 24, ECA 190-F → 190-A e Lei 14.133/2021, art. 1º → 178. O qualificador `desta Lei` delimita a origem, sem propagar a identidade da outra lei mencionada antes.

**Conexões apenas contextuais:** CPP 211 → 561 e as 29 parentéticas; a ausência de identidade normativa literal deve ser tratada de modo distinto da coerência semântica entre artigos. Os casos CC 927 → 186/187 e CPP 68 → 63/64 mostram contexto forte, mas não dispensam regra de confirmação aprovada por pessoa independente.

### 11.4 Proveniência, limite da revisão e encaminhamento

**Conferência desta frente:** leitura individual dos 37 objetos em `arestas.json`, trechos da origem, destino existente e informações de runs/histórico fornecidas pelo inventário; verificação cruzada com o relatório da fase e pareceres anteriores. **Apenas pontual em fontes oficiais**: confronto constitucional e do CPC/CC indicado na análise da conversa. Não houve conferência oficial externa integral de todos os 37 artigos, auditoria de vigência, execução do extrator, recomputação independente de hashes ou certificação de spans. A integridade computacional desses atributos, os 329 totais e as 292 arestas fora do escopo seguem **relatados pela Fase 1A.2**, não reexecutados nesta revisão.

**Recomendação:** manter experimentalmente as 7 correspondências sustentadas com ressalvas históricas; deixar as 30 identidades implícitas **pendentes de investigação/adjudicação humana**, sem promovê-las como confirmadas; não remover automaticamente arestas por nota histórica; não ampliar elegibilidade por proximidade textual. A Coordenação deve definir e testar critério jurídico-documental para parentéticas, exigir revisão independente inédita e deliberar sobre a apresentação histórica. Até lá, preservar as quatro classes existentes, `experimental-only` e o leitor sem vínculos habilitados.

**Parecer da frente:** nenhuma associação indevida demonstrada nestas 37 relações; **não há autorização para liberação pública**. Nenhuma decisão de revisão humana foi preenchida ou substituída.

**Fontes internas:** [relatório Fase 1A.2](../remissoes/fase-1a-2.md), [inventário completo](../remissoes/fase-1a-2/arestas.json), [arestas CSV](../remissoes/fase-1a-2/arestas.csv).
