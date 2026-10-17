# Remissões expressas — Fase 0.5

## 1. Escopo, materiais e revisão analisada

**Branch:** `investigacao/remissoes-fase-0-5`. **Main de origem:** `84c5bb5c5e28c08376e0bf40cf3f3f4b4fd783cf`. A main não mudou desde a Fase 0. Implementação medida: `fd781f51f0df87c8077b33eb7d5e53423ef39f82`. Regras `0.5.1`, SHA-256 `6cf232f85d242a28dd81ff654811106327f13948948b884afe8b7d289d3ae434`.

Foram examinados o relatório, `poc.py`, as amostras, os testes e os resultados do ZIP da Fase 0. O SHA do ZIP está em [sampling.json](../../tests/fixtures/remissions/sampling.json). A PoC e seus resultados foram preservados como referência histórica, não promovidos a código publicável.

**Não há integração com o leitor, home, build publicado ou PWA.** Não foram alterados textos, PDFs, fontes oficiais, históricos, módulos de `src/`, configuração de build, dependências ou workflows. O extrator roda exclusivamente por comando explícito em Node, sem modelo, embedding, serviço externo ou inferência temática. Python permanece apenas no comparador opcional da PoC histórica; não é dependência do novo extrator nem de sua integração futura.

## 2. Diagnóstico e alterações

A PoC anterior resolvia casos simples, mas sua regex podia confundir sufixos com palavras (`96 - ADCT`, `167 - Nos`), ler apenas parte de uma lista intercalada e associar uma lei distante à citação. Verificava o tachado do núcleo, mas não todos os qualificadores necessários. Não delimitava suficientemente reproduções de alterações de outra lei, normas antigas ou contexto riscado em torno de uma referência cujo hipertexto não estava riscado.

A implementação nova separa responsabilidades:

| Arquivo | Responsabilidade |
|---|---|
| `scripts/remissions/grammar.mjs` | Lexer numérico e parser de listas/intervalos/qualificadores com offsets UTF-16 |
| `norms.mjs` | Identidades explícitas do catálogo, escopo CF/ADCT, normas externas e anteriores; qualificadores ligados sintaticamente |
| `extract.mjs` | Integridade da edição, resolução conservadora, proveniência e tachado em dimensões distintas |
| `graph.mjs` | Conexões únicas e adjacência inversa derivada; representação compacta experimental |
| `corpus.mjs` | Leitura em memória dos mesmos JSONs escolhidos pelo build existente |
| `evaluate.mjs`, `select-sample.mjs` | Avaliação de expectativas declarativas e reprodução da seleção de fontes |
| `simulate.mjs`, `analyze.mjs` | Simulações controladas, análise e medição por comando explícito |
| `tests/node/remissions*.test.js` | Regressões reais, casos adversariais e testes do próprio avaliador |

As listas reconhecem vírgulas, conjunções, `artigos`, milhares e letras, inclusive sufixos sucessivos. Qualificadores antes/depois do artigo são preservados, sem inventar âncoras internas. Intervalos alfanuméricos não são expandidos por aritmética. Intervalos numéricos exigem ordem crescente, até 500 passos e todos os destinos individuais existentes; o limite é proteção de recursos, não afirmação jurídica.

O parser de busca do produto não foi reutilizado para extrair prosa. `deste Ato` isolado só identifica ADCT com origem ADCT; o nome completo ou a sigla são explícitos. `ambos deste Ato` qualifica um par delimitado, sem contaminar uma remissão anterior já qualificada como Código Civil.

Normas identificadas por número/ano usam o catálogo, sem apelidos por assunto. A lei deve estar anexada à expressão, ou em forma parentética anterior suportada. Contextos concorrentes, identidade insuficiente ou referência anterior sem ponte sintática produzem abstenção. Constituição estadual não identificada, código de outra edição, número malformado e sufixo desconhecido não recebem um artigo coincidente por palpite.

## 3. Exemplos reais antes/depois

| Caso | Fase 0 | Fase 0.5 |
|---|---|---|
| CC 927, `arts. 186 e 187` | Correto | Mantido: CC 186 e CC 187 |
| CPC 240, `arts. 397 e 398 da Lei nº 10.406...` | Correto | Mantido: CC 397 e CC 398 |
| CPC 609, `§ 2º do art. 1.031 da Lei nº 10.406...` | Artigo correto, qualificador não estruturado | Artigo CC 1031, qualificador preservado, sem promessa de âncora §2 |
| ADCT 54-A, `art. 54 deste Ato...` | Correto | Mantido: `cf/adct-54`, separado de CF 54 |
| CDC 104-A, `art. 54-A deste Código` | Correto | Mantido, ID letrado completo |
| CF 18, `art. 96 - ADCT` | Fragmentava `96 - A`; C | A: `cf/adct-96` |
| CF 28, lista `37, XI, 39, §4º, 150, II, 153...` | C | Quatro destinos distintos: CF 37,39,150,153 |
| ADCT 72, `artigos 153, §5º, 157, II, 212 e 239 da Constituição` | C | CF 153,157,212,239 |
| ADCT 121, duas citações 107 seguidas de `ambos deste Ato` | Primeira C | Ambas ADCT 107; CC 1275 anterior não é requalificado |
| CC 2040, Código Civil anterior, Lei 3.071/1916 | B | B com identidade externa preservada, nunca CC 827 atual |
| Licitações 193, `art. 1º a art. 47-A` riscado | Duas candidatas | Uma ocorrência D, sem expandir extremo alfanumérico |
| CLT 417/P 10, hipertexto art 422 não riscado dentro de oração riscada | A incorreto na avaliação nova | C: contexto necessário histórico; sem conexão ativa |
| ECA 263/P 1, cabeçalho reproduzido `1) Art. 121 ...` | A incorreto na avaliação nova | E: cabeçalho reproduzido, sem ECA 121 |
| ADCT 28 e ADCT 41, Constituição de 1967 | Correspondência com Constituição catalogada possível | B: edição constitucional externa expressa, sem CF 1988 |
| CP 359-M-A/359-M-B, numeração sucessiva | Truncamento potencial em 359-M | Não cria remissão do próprio cabeçalho para 359-M; IDs completos são reconhecidos |

As formas abreviadas acima identificam os dispositivos; os textos integrais dos parágrafos e as expectativas permanecem nos fixtures, sem redação legal alterada.

## 4. Método de validação e separação das amostras

- **Desenvolvimento:** 44 parágrafos/27 artigos da Fase 0, arquivo preservado byte a byte; 44 expressões anotadas, 54 destinos A esperados por ocorrência, 53 conexões únicas esperadas.
- **Avaliação separada:** 58 parágrafos de 58 artigos sem qualquer artigo de origem compartilhado com o desenvolvimento; 54 unidades candidatas anotadas, sendo 52 remissões e 2 negativos E, com 42 destinos A esperados e 41 conexões únicas.
- **Total de fontes anotadas:** 102 parágrafos,85 artigos distintos, nas 13 legislações. Não confundir com o total da varredura automática.

Seleção reproduzível: ordenar fontes por SHA-256 da seed `lexa-fase05-holdout-v1` com `code:article:paragraph`; escolher três parágrafos candidatos de artigos distintos e um negativo de cabeçalho por legislação; limitar comprimento para viabilizar conferência textual; acrescentar ADCT até sete artigos distintos (incluindo negativo) e dois casos deliberados de CTN com destino agrupado. O filtro lexical de seleção não usa o extrator ou seus resultados. [select-sample.mjs](../../scripts/remissions/select-sample.mjs) reproduz os 58 identificadores.

Os fixtures foram congelados no commit `d87e880` **antes da implementação Node**. A primeira avaliação ocorreu depois de `cc52223`, com resultados 41/42 e nenhum destino incorreto. Não foram corrigidas as três falhas diagnósticas específicas reveladas pela avaliação. Depois houve revisão adversarial do código: guardas de números malformados, identidade concorrente, Constituição antiga/estadual, `deste Ato` sem origem e sufixos sucessivos. A avaliação foi reexecutada e seus alvos, classes e erros originais permaneceram idênticos. Houve também ampliação do formato compacto para preservar o tipo da referência; não mudou a extração.

**Limitação:** o mesmo agente responsável pelo desenvolvimento preparou/conferiu as expectativas diretamente nos textos e no inventário. Não é revisão humana jurídica independente nem avaliação cega; o desenvolvedor tinha acesso aos fixtures. Não foram usados modelos ou saídas do extrator para gerar automaticamente os destinos esperados. Uma nova rodada deve reservar fontes inéditas e revisão humana antes de afirmar confiabilidade jurídica abrangente.

## 5. Métricas comparativas executadas

Uma expressão/lista ocupa uma ocorrência textual. A lista pode produzir vários destinos; duas ocorrências podem produzir uma única conexão origem→destino. O avaliador confere origem/parágrafo, sobreposição de offsets e conjunto de destinos, e penaliza destinos extras. Há testes para garantir que uma previsão parcialmente correta não conte como classificação integral correta.

### Mesma amostra de desenvolvimento da Fase 0

| Métrica | Fase 0 reexecutada | Fase 0.5 |
|---|---:|---:|
| Parágrafos / artigos examinados |44/27|44/27|
| Expressões anotadas |44|44|
| Candidatas detectadas, excluindo cabeçalhos próprios |41|45|
| Correspondentes à anotação |40|44|
| Expressões anotadas não detectadas |4|0|
| Candidatas excedentes brutas |1|1|
| Classificações A/B/C/D/E |25/7/4/5/0|29/7/5/4/0|
| Destinos A esperados |54|54|
| Destinos emitidos corretos |41|51|
| Destinos emitidos incorretos |0|0|
| Destinos omitidos por segurança em ocorrências C |10|3|
| Precisão dos destinos emitidos |41/41 =100%|51/51 =100%|
| Cobertura dos destinos esperados |75,93%|94,44%|
| Conexões únicas corretas |41|50|

**Interpretação dos excedentes:** na PoC era a fragmentação do intervalo histórico de Licitações 193. Na 0.5, `caput deste artigo` do ADCT 121 é remissão literal C que faltava na anotação original; não é ligação inventada. Mantivemos o gold congelado e registramos essa lacuna, sem manipular denominadores. Os três destinos não emitidos correspondem a remissões locais sem número expresso de artigo; a fase 0 as anotou A, mas o contrato 0.5 as mantém C. Essa mudança de escopo é deliberada e não foi ocultada do comparativo.

### Nova amostra de avaliação — ambos os extratores

| Métrica | Fase 0 | Fase 0.5 |
|---|---:|---:|
| Parágrafos / artigos |58/58|58/58|
| Unidades candidatas anotadas, incluindo 2 negativos E |54|54|
| Candidatas detectadas |52|55|
| Correspondentes à anotação |49|54|
| Unidades anotadas não detectadas |5|0|
| Candidatas excedentes sem correspondência |3|1|
| Classificações A/B/C/D/E |34/1/11/6/0|34/2/12/6/1|
| Classificações integralmente corretas |40/49|52/54|
| Destinos A esperados |42|42|
| Destinos emitidos |35|41|
| Destinos emitidos corretos |32|41|
| Destinos emitidos incorretos |3|0|
| Destinos esperados omitidos por segurança em C |8|1|
| Precisão das conexões por ocorrência |32/35 =91,43%|41/41 =100%|
| Cobertura dos destinos esperados |76,19%|97,62%|
| Conexões únicas corretas / emitidas |31/34|40/40|
| Conexões únicas esperadas |41|41|

A 0.5 encontrou 52/52 remissões normativas anotadas; os outros dois casos são negativos para avaliar rejeição. Na detecção normativa estrita, ficam dois candidatos indevidos retidos como C: o fragmento dos parágrafos a acrescentar no CDC 113 e o cabeçalho da LMP 43. Assim, precisão de candidatos normativos:52/54=96,30%; **nenhum desses dois gera conexão**. O avaliador mantém também os números brutos para inspeção, sem chamar todo excedente de erro jurídico.

Os três destinos errados da PoC antiga foram CDC 1→CDC 48 (o texto aponta ao ADCT 48), ECA 263→ECA 121 (cabeçalho de alteração de outra lei) e CLT 417→CLT 422 como corrente apesar da oração riscada. No novo extrator esses casos são C/E, sem aresta ativa. Não foram removidos da avaliação.

**Nenhuma destas porcentagens é precisão garantida do acervo.** A avaliação é pequena, não independente e não distribui casos igualmente entre todas as classes. Resultados brutos completos e todos os erros estão em [resultados.json](resultados.json); a adjudicação textual está em [revisao-diagnosticos.json](revisao-diagnosticos.json).

### Varredura completa — sem precisão aferida

Foram examinadas 7.110 entradas de 13 legislações, com 3.777 no núcleo CC/CF-ADCT/CPC/Licitações. As 148 entradas ADCT estão preservadas. Súmulas e notas jurisprudenciais não fazem parte da extração.

Saída 0.5: **4.896 ocorrências candidatas**, A/B/C/D/E = **1763/84/1857/1185/7**, 7.724 cabeçalhos próprios rejeitados e **2.326 conexões ativas únicas candidatas**. Antes havia 2.009 conexões. O aumento não é prova de precisão nem autorização para publicar; não houve auditoria integral desses candidatos A.

## 6. Casos residuais e política A–E

- **A:** artigo e norma/escopo determinados pelas classes suportadas, destino individual existente e evidência necessária não riscada.
- **B:** identidade externa identificada, sem destino catalogado; inclui CC 1916 e Constituição 1967. Preservar identidade/trecho, sem substituir pela edição atual.
- **C:** contexto insuficiente, padrão não suportado, destino ausente/agrupado ou evidência histórica parcial. Os motivos distinguem abstenção técnica de escopo não determinado; não afirmam ambiguidade jurídica onde só faltou gramática.
- **D:** núcleo da ocorrência riscado. A resolução pode continuar `resolved`, mas nunca entra no grafo ativo.
- **E:** candidato rejeitado como não remissão, por exemplo cabeçalho reproduzido. Cabeçalhos próprios são rejeitados previamente e têm contagem separada.

Os resíduos conhecidos da avaliação continuam expostos:

1. **CDC 1, `art. 48 de suas Disposições Transitórias`:** C, embora o destino textual seja ADCT 48. Falta a ponte gramatical `de suas`; não foi ajustada depois do holdout.
2. **CDC 113, `seguintes §§4°,5°e6° ao art.5º da Lei7.347`:** cria um diagnóstico implícito C extra para os parágrafos a acrescentar. Falta a ponte `ao` e a distinção completa de qualificador de inserção. O artigo externo continua B; sem aresta indevida.
3. **LMP 43, cabeçalho `“Art.61. ...`:** C em vez de E; a pontuação intermediária impede a rejeição específica, mas o contexto de alteração bloqueia a conexão.
4. **Subdispositivos sem artigo numericamente expresso:** registrados C; não prometer retorno ao caput/inciso por identidade fictícia.
5. **Intervalos alfanuméricos, entradas agrupadas, anáforas sem antecedente suportado e coordenações normativas complexas:** abstenção; não resolver por ordem presumida ou tema.

Essas limitações não produzem conexões incorretas conhecidas nas classes que emitiram A nas amostras. Sua resolução futura exige novos casos de regressão e avaliação reservada inédita.

## 7. Estrutura de relações e proveniência

Cada ocorrência contém `source` (norma/artigo/escopo/hash), `location` (campo/parágrafo/start/end/unidade/texto), qualificadores com seus próprios spans, evidência da norma, tipo, classificação, resolução com destinos e hashes e histórico em dimensões separadas (`core`, `qualifiers`, `context`, `state`).

**Exemplo real:** em CC 927/P 0, `text.slice(39,54)` é exatamente `arts. 186 e 187`. Os testes conferem todos os spans contra os runs originais e incluem prefixo com emoji para distinguir UTF-16 de pontos de código. Não há offsets aproximados ou placeholders nos resultados.

A máscara de tachado é construída pelas extensões reais dos runs. Normas/qualificadores riscados ou contexto necessário inteiramente riscado bloqueiam a publicação da ocorrência composta. Notas de decretos riscadas em outro ponto não contaminam a referência de Licitações 37/P 8. Não se certifica vigência pela ausência de tachado.

A tabela `edges` guarda fonte/destino deduplicados e índices das ocorrências. `incoming` referencia índices dessa mesma tabela; não é uma base inversa editável. Dois trechos iguais continuam duas ocorrências de uma conexão. Exemplo conferido: CC 927→CC 186 e inversa CC 186←CC 927.

No bundle compacto, as tuplas de ocorrência têm índices:

`[codeIndex, articleId, paragraph, start, end, classification, resolutionStatus, reason, coreHistory, qualifierHistory, contextHistory, qualifiers, normSpan, externalIdentity, kind]`.

`qualifiers` guarda `[start,end,kind,articleNumber|null]`; `normSpan` guarda `[start,end]`; identidade externa guarda `[kind,number|null,year]`. `codeIndex` refere-se à ordem de `editions`; os hashes dessa tabela valem para fontes e destinos. Campo jurídico é sempre `paragraphs`, e offsets são sempre UTF-16. `edges` guarda `[sourceCodeIndex,sourceArticle,targetCodeIndex,targetArticle,occurrenceIndices]`. `incoming` é derivado desses mesmos índices.

O JSON detalhado é a saída de auditoria e preserva também texto, IDs e todos os destinos resolvidos, inclusive diagnósticos históricos. O compacto é representação experimental para estimar custos; não é contrato integrado ao site nem substitui a auditoria detalhada. Na futura publicação, manter B/C/D/E no relatório do build, sem baixá-los desnecessariamente para o leitor.

## 8. Atualização e invalidação

Hash validado por norma + SHA do conjunto de edições, catálogo e regras; IDs de ocorrência dependem desse conjunto. Alterar somente um destino invalida o conjunto mesmo sem mudar a norma de origem. Os IDs textuais por parágrafo só são válidos para sua edição, não identidades jurídicas permanentes.

**Nove simulações em cópias**, com asserções, sem alterar arquivos legais:

1. Incluir 188 na lista de CC 927: nova conexão.
2. Excluir a lista: remover suas conexões.
3. Trocar 187 por 188: remover antigo, incluir novo.
4. Remover destino 187: lista inteira passa a não resolvida; nenhuma aresta obsoleta.
5. Renomear ID 187: não migrar por palpite.
6. Trocar `deste Ato...` por `desta Constituição Federal` em cópia do ADCT 54-A: destino muda de ADCT 54 paraCF 54.
7. Riscar ocorrência: retirar do grafo ativo, conservar diagnósticoD.
8. Alterar norma qualificadora em cópia do CPC 240: destinos mudam de CC 397/398 paraCPC 397/398.
9. Remover CC 397 sem alterar CPC: muda o conjunto de edições; nenhuma conexão antiga de CPC 240 permanece.

Além disso, regressões cobrem qualificador normativo riscado e versão das regras alterada. Reconstrução completa, determinística e sem patches aditivos é a proposta. Uma lista com algum destino ausente é rejeitada integralmente nesta versão, política conservadora explicitada no teste.

## 9. Integração futura — proposta, não implementada

Depois da seleção das edições no `buildPackage()`, executar a extração Node em memória, validar destinos/proveniência, derivar o grafo e emitir recurso imutável com SHA-256. O descritor deve carregar edição do conjunto e versão das regras. A coleta pendente não deve atualizar o grafo da edição publicada antes de revisão/incorporação.

O leitor futuro carregaria apenas o índice da edição aprovada, sob demanda na expansão do controle; **zero extração no navegador e zero download do índice na home**. O JSON jurídico do destino só precisa ser carregado ao navegar. Começar com um índice global compacto é simples e permite inversas entre normas sem baixar todos os índices de origem. Particionar apenas após medir necessidade real.

Para PWA: registrar recurso em integridade e papel próprio de retenção, verificar SHA antes de usar, não combinar grafo antigo com texto novo, respeitar abas na edição anterior e cachear somente os recursos visitados ou pedidos explicitamente para offline completo. Ter o índice não significa ter todos os textos de destino offline. Testes futuros precisam cobrir destino não baixado, falha de integridade e atualização parcial. Nada disso foi conectado ao aplicativo nesta etapa.

A comparação em memória confirmou **50 arquivos idênticos à main** (HTML+49 recursos internos). Scripts/testes/docs da investigação não entram no pacote publicado. [isolamento.json](isolamento.json) registra a evidência.

## 10. Custos medidos e limitações

Node v 22.23.3, Linux x 64, AMD EPYC 9 V 74, cinco rodadas sequenciais com corpus em memória, sem limitação de CPU. Inclui validação SHA, inventário, lexer, resolução, proveniência e IDs; exclui carregar/gerar o corpus, montar grafo, serializar, comprimir e trafegar rede. Não é teste de telefone ou do navegador.

| Extração | Rodadas (ms) | Mediana |
|---|---|---:|
| Núcleo 3.777 entradas |285.66, 225.40, 226.41, 214.25, 210.82|225.40 ms|
| Todas 7.110 entradas |446.60, 435.83, 428.02, 424.96, 426.52|428.02 ms|

| Representação experimental | JSON compacto | Gzip local |
|---|---:|---:|
| Núcleo, com diagnósticos |339.569 bytes|40.277 bytes|
| Todas as normas, com diagnósticos |724.936 bytes|78.871 bytes|
| Projeção de candidatos A, sem diagnósticos B–E |312.263 bytes|48.674 bytes|

Gzip usa zlib local, não transferência HTTP observada. A projeçãoA **não é arquivo aprovado para publicar**: candidatos completos não foram auditados. Não duplica textos legais. Os arquivos JSON detalhados têm custo maior, servem à investigação e não devem ser baixados pelo leitor.

A Fase 0 mediu aproximadamente 79 ms no núcleo em Python, sem o mesmo contrato de validação/hash/proveniência; o pacote completo daquela PoC tinha 374.412 bytes/48.499 gzip. Esses números não constituem comparação de velocidade equivalente. A 0.5 armazena mais ocorrências, qualificadores e condições, e seu custo adicional permanece no build. Não há promessa de redução de RAM ou tempo de leitura derivada desse ensaio. Heap de celular não foi medido com confiabilidade; permanece como validação futura.

## 11. Testes executados e falhas investigadas

- **93/93 testes Node**, pelo `npm test`, incluindo build de produção e 41 testes novos (38 do extrator e 3 do avaliador/seleção). Sem testes desativados ou limiares frágeis de tempo.
- **46/46 testes Python existentes**, `unittest discover`.
- **11/11 verificações essenciais Chromium/Playwright**: interface, carregamento, leitura, índice/paginação, busca, home, favoritos, cópia, PWA, política offline e contrato dos benchmarks. Não se reexecutou a baseline temporal da aplicação.
- **9/9 simulações** incluídas nas regressões Node e na análise.
- Corpus antes/depois idêntico, reconstrução determinística, hashes declarados conferidos, fixtures de avaliação congelados e fontes de avaliação distintas das de desenvolvimento.
- Pacote em memória idêntico ao da main; fidelidade de dados/PDFs e integridade também cobertas pelos testes existentes de páginas.

Durante desenvolvimento houve uma expectativa incorreta do teste de qualificador inteiramente riscado (`deleted`, não `mixed` nesse componente) e lentidão causada por clonar o corpus inteiro dentro da verificação de cada span. Corrigiu-se o teste, sem afrouxar a exigência de exclusão histórica ou de offsets. As falhas residuais da avaliação não foram escondidas nem transformadas em testes aprovados.

## 12. Riscos e recomendação para Fase 1

**Recomendo avançar para uma integração restrita e revisável das classes validadas, após aprovação humana deste trabalho; não recomendo publicar automaticamente a varredura de 2.326 conexões.** A interface e a PWA continuam totalmente pendentes de implementação/validação própria.

Critérios técnicos observados: os destinos emitidos foram corretos nas duas amostras; contexto ambíguo/insuportado fica fora das conexões ativas; ADCT e CF permanecem separados; históricos não alimentam o grafo; reconstruções retiram relações obsoletas; resultados são determinísticos, versionados e verificáveis. O custo de extração é compatível com build, e o índice permite carregamento sob demanda sem servidor ou IA.

Limites da recomendação:

- A avaliação não é humana independente, nem grande o bastante para garantir precisão do acervo ou de cada subclasse rara.
- As três falhas diagnósticas do holdout precisam continuar abstidas/rejeitadas; qualquer correção deve ser validada em fontes inéditas.
- Reproduções de leis alteradas, notas editoriais, nomes normativos incompletos e anáforas podem exigir outras guardas. Não usar vigência presumida ou tema para completá-las.
- Antes de ativar a funcionalidade, revisão humana das classes permitidas e amostra inédita, regressões com novos erros encontrados, orçamento medido no navegador e testes PWA/teclado de integração. Uma classe não validada não deve ser liberada apenas porque seu destino numérico existe.
- Destinos agrupados ou subdispositivos sem identidade verificável continuam sem conexão direta. Não estabelecer meta arbitrária de cobertura para forçar sua inclusão.

Não houve merge, deploy ou mudança visual. Este PR entrega módulos experimentais, testes, amostras e documentação; não a funcionalidade de navegação.

## 13. Reprodução e arquivos

Comandos completos em [scripts/remissions/README.md](../../scripts/remissions/README.md). Nenhuma dependência nova. A análise usa `test-results/remissions/`, ignorado pelo Git; o build comum não importa esses módulos.

- [Resultados medidos](resultados.json): métricas brutas por amostra, erros, varredura, hashes, tempos, tamanhos e simulações.
- [Amostra de desenvolvimento](../../tests/fixtures/remissions/phase 0.json) e [avaliação](../../tests/fixtures/remissions/holdout.json).
- [Seleção/hashes](../../tests/fixtures/remissions/sampling.json) e [adjudicação](revisao-diagnosticos.json).
- [Teste do extrator](../../tests/node/remissions.test.js) e [do avaliador](../../tests/node/remissions-evaluation.test.js).

Se uma atualização jurídica mudar textos/identidades usados nos fixtures, conferir e revisar as expectativas conscientemente; não aceitar a saída do extrator como novo gold. A base de conexões deve continuar vinculada exatamente à edição incorporada, nunca a uma coleta em revisão.
