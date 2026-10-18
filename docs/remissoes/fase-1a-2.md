# Fase 1A.2 — validação documental das remissões elegíveis

## Resultado executivo

Inventário integral: **329 arestas únicas, provenientes de 272 ocorrências elegíveis**. A verificação automatizada separada do extrator classificou:

| Resultado por aresta | Quantidade |
|---|---:|
| Consistente na verificação automatizada | **292** |
| Suspeita | **8** |
| Inconclusiva | **29** |
| Erro confirmado por contradição documental verificável | **0** |

Esses resultados **não equivalem a revisão jurídica humana, certificação de vigência ou precisão jurídica de 100%**. As 329 relações continuam exclusivamente experimentais. Nenhuma foi removida, acrescentada ao leitor ou publicada. As oito suspeitas são alertas para conferência; não são oito erros confirmados.

Amostra de rejeições: **354 ocorrências**, de uma população de **4.624**, distribuídas em **203 estratos**, cobrindo as 13 legislações. Todas têm evidência documental e campos de revisão humana vazios.

## Base e referências consultadas

Branch local: `validacao/remissoes-fase-1a-2`, criada de `correcao/remissoes-fase-1a-1`, commit **`5b218d9dc38c94194e0a13c51984d2b6d14c2f14`**. HEAD permaneceu nesse commit: esta entrega não cria commit, PR, merge ou deploy, conforme a restrição da Coordenação.

Consultados o relatório `docs/remissoes/fase-1a-1.md`, os módulos em `scripts/remissions/` e:

- Integridade Jurídica, incluindo adendo 1A.1: `docs/parecer-integridade`, commit `55039203a75c8663514c4ef6512f35bbf898b15e`, `docs/coordenacao/02-integridade-juridica.md`.
- Qualidade da branch documental: `docs/parecer-qualidade`, commit `67a2de4a6a46a13634e3129a7a7c0030e7923f44`.
- Parecer específico da Fase 1A.1 no **PR #11**, obtido por `refs/pull/11/head`, commit `9b296a43c2bfd44d1c303f647a877007818f79b1`: `docs/coordenacao/04-qualidade-testes-fase-1a-1.md`.

A consulta à API GraphQL do PR retornou `Forbidden`. O conteúdo versionado do parecer foi lido pelo Git; comentários/conversas do PR não puderam ser consultados. Não foram presumidas decisões da Coordenação ausentes desses documentos.

## Artefatos e uso pela revisão humana

Arquivos em [fase-1a-2/](fase-1a-2/):

- [arestas.json](fase-1a-2/arestas.json): todas as arestas, IDs, normas, escopos, artigos, hashes jurídicos e de artigo, ocorrências, qualificadores, runs, offsets UTF-16, contexto integral dos artigos de origem/destino, condições verificadas e motivo objetivo da elegibilidade.
- [arestas.csv](fase-1a-2/arestas.csv): **329 linhas**, uma por aresta, com identificação, literal, parágrafo, início/fim, evidência normativa, classe, histórico e referência ao JSON completo.
- [rejeicoes-amostra.json](fase-1a-2/rejeicoes-amostra.json): **354 rejeições**, com contexto integral, resolução diagnóstica original, razão da exclusão, estrato, posição de seleção por hash e conferências adicionais de proveniência.
- [revisao-humana.csv](fase-1a-2/revisao-humana.csv): **683 linhas** (329 arestas + 354 rejeições), com `decision`, `justification`, `evidenceConsulted` e `needsAdjudication` **integralmente vazios**.
- [manifesto.json](fase-1a-2/manifesto.json): SHA-256 e tamanho dos quatro arquivos, fingerprints dos módulos protegidos, hash do corpus, hash do build padrão e hashes dos scripts desta auditoria.
- [validacoes.json](fase-1a-2/validacoes.json): registros dos testes e da comparação com a base.

CSV em UTF-8 com BOM, vírgula como separador, aspas duplas escapadas e linhas CRLF. Importar explicitamente como CSV UTF-8 se a planilha usar ponto e vírgula por padrão. As colunas de contexto resumem o parágrafo de origem e o cabeçalho do destino; o contexto integral está nos JSONs, localizável por ID. Não é necessário executar o extrator para conferir esses arquivos. As colunas de status são **resultados automáticos**, separadas das decisões humanas vazias.

Parágrafos e offsets são baseados em **zero**; `end` é exclusivo. Os offsets são unidades UTF-16 do parágrafo formado pela concatenação dos runs, e não posições em bytes do JSON/PDF.

### Ocorrências versus arestas

Há **272 IDs de ocorrência distintos** e **329 IDs de aresta distintos**. A associação entre as duas tabelas tem **353 participações**: uma ocorrência pode citar vários destinos, e uma mesma aresta pode ser sustentada por várias ocorrências. Não se interpretam 353 participações como 353 remissões independentes. IDs de aresta são SHA-256 da geração e da tupla origem/destino; IDs de ocorrência são preservados da edição auditada.

As quatro classes continuam as mesmas. Por aresta (nenhuma aresta reúne classes diferentes):

| Classe | Arestas | Consistentes | Suspeitas | Inconclusivas |
|---|---:|---:|---:|---:|
| `self-qualified-article-list` | 229 | 224 | 5 | 0 |
| `adct-self-article` | 19 | 18 | 1 | 0 |
| `parenthetical-article-list` | 30 | 0 | 1 | 29 |
| `numbered-law-article-list` | 51 | 50 | 1 | 0 |

Contagem distinta **por ocorrência**: 192 autorreferentes, 23 ADCT, 26 parentéticas e 31 com lei numerada, totalizando 272.

## Método da verificação integral

`scripts/audit-remissions/run.mjs` usa o build e a geração experimental existentes **somente para obter o corpus e delimitar o conjunto elegível**. Não é importado pelo build público. O julgamento documental fica em `scripts/audit-remissions/checks.mjs`, que **não importa** a gramática, o resolvedor de normas ou a política de elegibilidade de produção.

Para cada participação ocorrência/aresta, o auditor:

1. Recalcula SHA-256 do objeto jurídico de origem e destino e confronta-os com os hashes registrados; confere existência individual, número e escopo do artigo.
2. Reconstrói os parágrafos pelos runs e confere literal, limites, offsets UTF-16 e interseção com runs riscados, inclusive qualificadores e identidade normativa.
3. Faz leitura lexical própria das listas simples e das identidades de lei por espécie/número/ano. Compara a identidade com o catálogo do corpus, sem escolher destinos por coincidência temática.
4. Confere as condições textuais das quatro classes existentes, sem ampliar sua gramática: autorreferência compatível com o diploma, Ato com origem ADCT, parênteses simples e identidade numerada diretamente anexada.
5. Procura marcadores adicionais de reprodução/alteração em todo o artigo de origem; considera prefixo riscado e identidades normativas anteriores na mesma unidade textual como alertas de revisão.
6. Inspeciona o cabeçalho do destino quanto a notas expressas de revogação/veto. Isso é um alerta documental, não uma decisão automatizada sobre vigência ou incorreção da remissão.

O status da aresta segue a condição mais restritiva das evidências: contradição verificável → erro; alerta contextual → suspeita; identidade não comprovada literalmente → inconclusiva; sem essas ressalvas e com condições verificáveis satisfeitas → consistente automatizada.

Uma remissão parentética sem nome de diploma depende da convenção de referência local. Embora essa convenção seja admitida pela política experimental, **a própria política não foi usada como prova independente da identidade**: por isso os casos ficam inconclusivos, salvo alerta adicional mais prioritário. Não foram criados links alternativos ou destinos presumidos.

## Alertas e evidências para adjudicação

| Origem → destino | Evidência documental | Classificação e encaminhamento |
|---|---|---|
| ADCT 107-A → ADCT 107 | A origem diz `art. 107 deste Ato das Disposições Constitucionais Transitórias`; o cabeçalho do destino contém nota `Revogado pela Emenda Constitucional nº 126, de 2022` e texto riscado. | Suspeita por destino com histórico explícito. Conferir apresentação/aceitabilidade documental sem decidir vigência automaticamente. |
| CLT 413 → CLT 384 | Autorreferência literal; cabeçalho de CLT 384 tem redação riscada e nota de revogação pela Lei 13.467/2017. | Mesmo alerta. A correspondência numérica e normativa não está contradita pelo teste. |
| CLT 461 → CLT 510 | Origem menciona `art. 510 desta Consolidação`; o texto do destino está riscado e traz revogação pela Lei 4.668/1965. | Priorizar confronto humano. O auditor não substitui 510 por outro número nem conclui erro jurídico. |
| CPC 499 → CC 757 | Identidade expressa da Lei 10.406/2002; destino traz `Revogado pela Lei nº 15.040, de 2024`. | Conferir relação com edição incorporada e manutenção da remissão no texto de origem. |
| CPP 211 → CPP 561 | Parentética `art. 561`; destino contém redação riscada e nota de revogação pela Lei 8.658/1993. | Suspeita por nota do destino e identidade local contextual não comprovada literalmente. |
| ECA 161 → ECA 24 | O mesmo parágrafo menciona CC 1637/1638 e depois `art. 24 desta Lei`. | Suspeita lexical de antecedente concorrente. Pode ser autorreferência perfeitamente adequada; não há contradição demonstrada. |
| ECA 190-F → ECA 190-A | Antes de `art. 190-A desta Lei` aparece a Lei 9.296/1996. | Mesmo alerta conservador; conferir o antecedente de “desta”, sem presumir erro. |
| Licitações 1 → Licitações 178 | Antes de `art. 178 desta Lei` aparece a Lei 13.303/2016. | Mesmo alerta conservador. Não redirecionar ao art. 178 de outra lei. |

Essas oito relações têm os números, spans e hashes conferidos. Os alertas de nota de revogação **não significam** que a conexão documental seja incorreta: uma edição pode preservar uma remissão expressa a dispositivo com histórico. Os três alertas de identidade anterior podem ser falsos alarmes da triagem. A decisão humana continua vazia.

As **29 inconclusivas** são parentéticas sem identidade normativa literal suficiente para este critério independente. Exemplo: CC 927 → CC 186/187 permanece no inventário e na política experimental, mas a convenção local exige revisão; isso não transforma o conhecido caso positivo em erro.

### Distribuição por norma de origem

| Norma | Consistentes | Suspeitas | Inconclusivas | Erro confirmado |
|---|---:|---:|---:|---:|
| CDC | 9 | 0 | 0 | 0 |
| CF/ADCT | 18 | 1 | 0 | 0 |
| CC | 6 | 0 | 16 | 0 |
| CLT | 24 | 2 | 0 | 0 |
| CPC | 8 | 1 | 0 | 0 |
| CPP | 57 | 1 | 8 | 0 |
| CTN | 4 | 0 | 0 | 0 |
| ECA | 60 | 2 | 0 | 0 |
| Improbidade | 34 | 0 | 0 | 0 |
| LEP | 18 | 0 | 3 | 0 |
| Licitações | 26 | 1 | 0 | 0 |
| Maria da Penha | 2 | 0 | 0 | 0 |
| CP | 26 | 0 | 2 | 0 |

Riscos concentrados: antecedente de autorreferência no ECA/Licitações; dispositivos de destino com notas históricas no ADCT/CLT/CPC/CPP; identidade local implícita em CC/CPP/LEP/CP. A ausência de alertas nas outras normas não dispensa revisão humana.

## Amostragem das rejeições

População: **4.624 ocorrências rejeitadas**, sem incluir as 272 elegíveis. Estrato é a combinação de:

- Norma e escopo da origem (`main`/`adct`).
- Classe A/B/C/D/E, motivo do gate e razão diagnóstica do extrator.
- Facetas de histórico, ambiguidade normativa, reprodução e sintaxe não autorizada.

Dentro de cada estrato, ordena-se por `SHA256("lexa-1a2-rejeicoes-v1" + NUL + occurrenceId)` e selecionam-se **até duas ocorrências**. Resultado: 203 estratos, 52 unitários e 151 com pelo menos duas ocorrências; **354 registros**. A seleção é independente da ordem de entrada, sem escolher saídas bem-sucedidas. O identificador da ocorrência incorpora a edição/regras: a amostra é estável para a mesma base e versões, não necessariamente para outra edição.

É uma amostra de **cobertura de riscos**, não amostragem proporcional para estimar precisão/recall global. Os estratos pequenos são deliberadamente sobrerrepresentados. Não houve cálculo de precisão jurídica ou revisão humana da amostra.

### Distribuições e resultados

| Classe bruta | Selecionadas |
|---|---:|
| A, mas não elegível | 146 |
| B | 23 |
| C | 93 |
| D | 89 |
| E | 3 |

36 registros são do escopo ADCT; os demais são de escopo principal. Todas as 13 legislações aparecem: CDC 20; CF/ADCT 61; CC 14; CLT 43; CPC 22; CPP 44; CTN 23; ECA 36; Improbidade 18; LEP 25; Licitações 21; Maria da Penha 11; CP 16.

Triagem pelo **motivo de exclusão**, não um gold jurídico independente:

| Grupo | Selecionadas | Leitura prudente |
|---|---:|---|
| Classes/sintaxes não autorizadas | 137 | Omissões intencionais da política; podem orientar cobertura futura após validação. |
| Destinos externos | 23 | Omissões intencionais por ausência de destino interno, conforme diagnóstico; conferir identidade antes de qualquer ampliação de acervo. |
| Reprodução sem atribuição suportada | 13 | Bloqueio conservador; pode omitir referências introdutórias legítimas. |
| Histórico | 94 | Bloqueio de evidência riscada/mista; não promover a vínculo ativo. |
| Limitação de reconhecimento ou ambiguidade | 78 | Necessitam distinguir ambiguidade real de padrão textual ainda não reconhecido. Não há destino novo confirmado por esta triagem. |
| Outros motivos de política | 9 | Incluem qualificadores compartilhados e editoriais; não assumir que sejam candidatos a liberação. |

Conferência adicional independente: **354/354 hashes de origem e spans de núcleo válidos**, sem divergência nos spans de qualificadores/identidade normativa presentes. Isso valida a localização das evidências, **não** a correção da classificação ou da resolução bruta.

Exemplos efetivamente selecionados:

- CDC 78, `arts. 44 a 47, do Código Penal`: intervalo conscientemente excluído; oportunidade futura de sintaxe, sem promoção nesta fase.
- CDC 77, `art. 60, §1° do Código Penal`: qualificador fora do recorte atual; futura avaliação deve manter navegação somente ao nível realmente verificável.
- CDC 103, parágrafo 6, `art. 13 da Lei 7.347/1985`: diagnóstico externo, sem substituição por outro art. 13.
- CDC 117, parágrafo 1, `Art. 21`: reprodução bloqueada, sem atribuição automática ao CDC.
- ECA 263/264 e Licitações 179: três candidatos E selecionados são cabeçalhos reproduzidos (`Art. 129`, `Art. 102`, `Art. 2º`); contexto preservado para revisão, sem aresta ativa.
- CDC 82, parágrafo 5, `arts. 91`: contexto normativo anterior sem ponte suportada; possível limitação de reconhecimento, não confirmação de destino.
- CF 18, parágrafo 5, `art. 96 - ADCT`: editorial excluído; não deve ser liberado apenas para elevar cobertura.
- ADCT 107-A/121: `ambos da Constituição Federal`/`ambos deste Ato` são exemplos de evidência compartilhada; permanecem fora das classes autorizadas.

A população amostrada contém apenas candidatas detectadas e rejeitadas. **Referências que o extrator nem detectou não podem ser estimadas por essa amostra.** Não se mediu cobertura do universo de remissões do acervo.

## Integridade, reprodução e testes

Não foram modificados extrator, gramática, identificação normativa, política, build, leitor, PWA, fontes, PDFs, históricos ou textos jurídicos. Só foram acrescentados scripts de auditoria, um teste direcionado e os documentos/artefatos desta fase.

O manifesto registra extrator 0.5.2, política 1a.1, as quatro classes e `experimental-only`. A geração coincide com a de `fase-1a-1/metrics-after.json`. Os fingerprints dos módulos protegidos foram confrontados com os bytes do commit base. O objeto do corpus foi verificado antes/depois contra mutação.

Duas gerações dos cinco artefatos produziram **bytes idênticos**. O JSON experimental também foi reconstruído duas vezes de forma determinística. O build padrão foi comparado com um arquivo Git do commit base: HTML, manifesto e arquivos têm o mesmo fingerprint composto `4f29d56a55f754b6e4ce651b2e31250a149922c3113d8f0fa3ca40e280b4146a`, sem descriptor de remissões.

Validações executadas em Node **22.23.3**, Python/Playwright e Chromium disponíveis no ambiente:

| Verificação | Resultado |
|---|---|
| Testes de auditoria novos | **7 aprovados**, inclusive corrupção de SHA/span/escopo, CSV, revisão vazia e seleção independente da ordem |
| Auditoria + integração + adversariais Node | **41 aprovados**, zero falhas ou skips |
| Reexecução dos 7 testes após refinamento das colunas CSV | **7 aprovados** |
| `npm run build` | Aprovado; build padrão sem índice |
| `tests/browser/remissions_integration.py` | **5 grupos aprovados**: carga explícita, offline parcial, atualização/duas edições, rede/SHA, preparo completo e build desabilitado |
| Regeneração dos artefatos em outro diretório | Todos idênticos byte a byte |
| CSV por parser independente da biblioteca padrão Python | 329/683 linhas, colunas e células vazias conferidas |
| Fingerprints protegidos versus commit base | Todos idênticos |

Não foram repetidas a suíte Python geral, a auditoria técnica global, benchmarks de desempenho ou testes de dispositivo físico: não houve mudança nesses componentes. O teste de PWA foi dirigido às garantias de não ativação e integridade já existentes. Nenhum teste não executado é apresentado como aprovado.

### Comandos

```sh
node scripts/audit-remissions/run.mjs
node scripts/audit-remissions/run.mjs /tmp/lexa-1a2-repro
node --test tests/node/remissions-audit.test.js tests/node/remissions-integration.test.js tests/node/remissions-adversarial.test.js
npm run build
python tests/browser/remissions_integration.py
```

Comparar os quatro artefatos e `manifesto.json` entre o diretório padrão e o de reprodução. Requer corpus e versões do commit base preservados; não acrescenta dependências. Os scripts de auditoria não são chamados pelo build público.

## Limites e recomendações

1. **Prioridade imediata:** adjudicar as oito suspeitas. Confrontar literalmente as notas e referências, sem substituir números, inferir vigência ou tratar uma nota de revogação como erro automático de extração.
2. Revisar as 29 parentéticas inconclusivas e documentar explicitamente a convenção de identidade local. Conferir também as 292 consistentes; esse grupo não está aprovado por revisão humana.
3. Revisar as 354 rejeições, priorizando os 78 casos de limitação/ambiguidade e os exemplos de qualificadores compartilhados. Separar falsa negativa efetiva de omissão intencional. Nenhuma rejeição foi promovida.
4. Se houver contradição demonstrada, registrar adjudicação e abrir correção separada; nesta fase não se ajustam regras ou arestas para “corrigir” as métricas.
5. Manter a interface de remissões desligada, as quatro classes, o build opcional e `experimental-only`, até revisão humana independente e decisão expressa da Coordenação.

A checagem separada reduz dependência do resultado do próprio parser, mas foi desenvolvida pelo mesmo agente, usando o mesmo corpus e metadados. **Não constitui independência humana nem confronto integral com fontes oficiais externas.** Há riscos de metadados de origem incorretos, formulações de transcrição não reconhecidas e alertas excessivamente conservadores. Os arquivos facilitam revisão por especialista sem executar o extrator, mas não a substituem.

Entrega em branch local, arquivos não commitados. Não houve commit, PR, merge, deploy, ampliação de gramática ou modificação da experiência publicada.
