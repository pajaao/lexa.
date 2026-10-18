# Fase 1A.1 — robustez das remissões expressas

## Escopo e versões

Trabalho restrito à resolução/elegibilidade determinística e aos respectivos testes. Branch `correcao/remissoes-fase-1a-1`, derivada de `funcionalidade/remissoes-fase-1a` em **`3bb3c412e06f23a7be27458669ddd1448f35a130`**. Main de referência: `84c5bb5c5e28c08376e0bf40cf3f3f4b4fd783cf`.

Pareceres lidos diretamente das branches documentais, sem incorporá-las ou modificar documentos de coordenação:

| Parecer | Commit consultado | Documento |
|---|---|---|
| Engenharia | `60b67a63a93f9340e310446e4f92d04f23cfb52d` | `docs/coordenacao/01-engenharia.md` |
| Integridade | `ea1eecf2b773354d25e650e70b5bf0566e88bc3c` | `docs/coordenacao/02-integridade-juridica.md` |
| Qualidade | `67a2de4a6a46a13634e3129a7a7c0030e7923f44` | `docs/coordenacao/04-qualidade-testes.md` |
| UX | `d11823f6faddd286fd94cf4c6c3260f851fe61b8` | `docs/coordenacao/03-ux-produto.md` |

Engenharia, Integridade e Qualidade orientaram as correções. A leitura de UX não resultou em mudanças: contrato do índice, API, leitor e navegação futura permanecem iguais.

Extrator: **0.5.1 → 0.5.2**. Política: **1a.0 → 1a.1**, com as mesmas quatro classes e `experimental-only`. Build padrão continua desabilitado. Sem merge, deploy ou liberação visual.

## 1. Método e casos reproduzidos

Expectativas declaradas a partir das entradas e critérios do parecer de Qualidade, não geradas pela saída do extrator. Cada caso sintético substitui somente `paragraphs[].runs` de um artigo em uma cópia profunda do corpus. O hash da cópia é recalculado. O corpus de produção nunca é modificado. CPP 13-A usa os runs reais, selecionando a ocorrência literal `art. 158`.

Entradas completas, motivos e destinos esperados estão em [`adversarial.json`](../../tests/fixtures/remissions-1a-1/adversarial.json). Saídas por ocorrência, com classificação, resolução, histórico, offsets UTF-16, hash da origem e decisão do gate:

- [Antes](fase-1a-1/adversarial-before.json), capturado antes das correções, na base 1A.
- [Depois](fase-1a-1/adversarial-after.json).
- [Comparação e variantes de histórico](fase-1a-1/eligibility-delta.json).

Na tabela, “bruto” significa classe emitida e destinos **ativos A**, não todos os destinos diagnósticos guardados no objeto `resolution`. `∅` indica ausência de vínculo ativo. Em especial, C/D podem conservar uma resolução diagnóstica, sem integrar o grafo.

| Caso e entrada/origem | Antes: bruto; elegibilidade | Depois: bruto; elegibilidade | Destino esperado e diagnóstico |
|---|---|---|---|
| **A01**, Licitações 100: `Consultar o art. 147 desta Lei nº 8.666/1993.` | A → Licitações 147; aceita | C, identidade conflitante → ∅; rejeita | ∅. **Erro confirmado nas duas camadas**: a identidade numerada era ignorada após “desta Lei”. |
| **A02**, CC 900: `No trecho reproduzido de um diploma não identificado: (art. 186).` | A → CC 186; aceita | C, reprodução sem atribuição suportada → ∅; rejeita | ∅. **Erro confirmado nas duas camadas**: parentética em diploma não identificado não é referência local segura. |
| **A03**, CC 900: `Consultar o art. 186 da Lei nº 3.071/1916.` | B externa → ∅; rejeita | B externa → ∅; rejeita | Norma anterior externa. **Bloqueio já correto**, sem defeito reproduzido. |
| **A04**, CPC 300: `Consultar o art. 186 da mesma lei.` | C → ∅; rejeita | C → ∅; rejeita | ∅. **Bloqueio já correto** de anáfora indeterminada. |
| **A05**, ADCT 95: `Consultar o art. 84 da Constituição Estadual do Rio Grande do Norte.` | C → ∅; rejeita | C → ∅; rejeita | ∅. **Bloqueio já correto**; não equivale a CF ou ADCT. |
| **B01**, ADCT 95: `Consultar o art. 84 deste Ato das Disposições Constitucionais Transitórias de 1967.` | A → ADCT 1988/84; aceita | B, ADCT de 1967 externo → ∅; rejeita | ∅ interno. **Erro confirmado nas duas camadas**: o ano explícito era descartado. |
| **B02**, Licitações 100: run riscado `Segundo a Lei nº 8.666/1993, ` + atual `ver art. 147 desta Lei.` | A → Licitações 147, contexto `clear`; gate já rejeita por “ver” | C → ∅, contexto `mixed`; rejeita por classificação C | ∅. **Erro bruto confirmado, gate original correto por motivo editorial**. Não se afirmou que o caso original atravessava a barreira. |
| **B03**, ADCT 95: `Consultar o art. 84 da Constituição Federal de 1988.` | A → **CF 84**, não ADCT; gate rejeita | Igual | ∅ elegível. **Resolução correta**, classe de CF explícita continua não autorizada. |
| **B04**, Licitações 100: texto todo riscado `Consultar o art. 147 desta Lei.` | D → ∅; rejeita | D → ∅; rejeita | ∅. **Bloqueio já correto** de histórico integral. |
| **C01**, Licitações 100, terceiro parágrafo, após dois parágrafos neutros: `Passa a vigorar a seguinte redação: “art. 147 desta Lei”.` | A → Licitações 147; aceita | C, reprodução → ∅; rejeita | ∅. **Erro confirmado nas duas camadas**: limite dos dois primeiros parágrafos e guarda bruta só para default local. |
| **C02**, Licitações 100: `Confira os arts. 147 a 150 desta Lei.` | A → 147–150; gate rejeita intervalo | Igual | ∅ elegível. **Bloqueio já correto**; os destinos brutos não são por isso remissões falsas. |
| **C03**, CC 900: `Confira (arts. 186 e 187).` | A → CC 186/187; aceita | Igual | CC 186/187. **Controle positivo preservado**. |
| **C04**, CPC 300: `Aplicam-se os arts. 186 e 187 da Lei nº 10.406/2002.` | A → CC 186/187; aceita | Igual | CC 186/187. **Controle positivo preservado**. |
| **CPP13A**, CPP 13-A real: `art. 158` dentro da enumeração expressa do Código Penal | A → **CPP 158**; gate rejeita | C, escopo coordenado não suportado → ∅; rejeita | Nunca CPP 158. **Erro bruto confirmado**; não se implementou propagação do destino CP 158 sem gramática validada. |

### Variantes e limites da reprodução

B02 também foi executado com `consultar`, `aplicar` e `considerar` no lugar de `ver`. As três variantes **atravessavam o gate original**, emitindo Licitações 147; depois, as três ficam C por evidência histórica necessária. O arquivo de comparação preserva entradas e saídas de ambas as implementações, sem depender de um resultado esperado criado pelo extrator.

Testes suplementares cobrem reprodução introduzida em parágrafo próprio depois do segundo, remissão em parágrafo posterior à instrução, conservação da exclusão do artigo inteiro e tentativa de reutilizar classificação/spans truncados da resolução antiga de A01.

Nos 14 casos centrais, seis casos tinham destinos A indevidos no bruto antes (A01/A02/B01/B02/C01/CPP13A); depois, nenhum desses seis emite A. Quatro deles atravessavam a elegibilidade original; depois, nenhum. As três variantes B02 são registradas separadamente, não contadas como três novas falhas independentes. C02 tem destinos textualmente corretos mas fora da política, não entra na contagem de falso positivo jurídico.

Não houve nova auditoria geral, revisão humana independente ou garantia de precisão global.

## 2. Correções implementadas

### Identidade normativa — `scripts/remissions/norms.mjs`

- “desta Lei” seguido de identificação numérica não pode terminar a análise antes do número/ano. A identidade é preservada e conferida contra a origem; contradição ou identidade incompleta produz abstenção, não redirecionamento conveniente.
- ADCT com ano explícito diferente de 1988 é identificado como outra edição, externa. A evidência textual inclui o ano. Não confundir `cf/N`, `cf/adct-N` ou atos constitucionais anteriores.
- Classes novas não foram autorizadas: uma variante autoqualificada numerada ou ADCT explicitamente datado não passa automaticamente pela classe curta anteriormente aprovada.

### Resolução e histórico — `scripts/remissions/extract.mjs`

- O estado `mixed` do contexto anterior à remissão é preservado, em vez de reduzido a `clear`. A condição histórica impede A mesmo quando o núcleo e o qualificador imediato são atuais. A resolução diagnóstica permanece separada do histórico, conforme o contrato já existente.
- Em coordenação textual direta, uma referência não qualificada não recebe o default local quando a seguinte contém identidade normativa externa/concorrente ou escopo compartilhado já não suportado. A análise usa somente o conector e os qualificadores textuais imediatos. **Não propaga** o destino externo, não escolhe por coincidência de número e não associa lei distante. CPP 13-A passa a abster-se no ponto que antes recebia CPP 158.
- Regras versionadas e SHA atualizados; o novo módulo de contexto participa do hash das regras.

### Reprodução — `scripts/remissions/context.mjs`

Guarda lexical compartilhada entre extrator e elegibilidade. Examina todos os parágrafos, sem corte nos dois primeiros; reconhece também o marcador expresso de trecho reproduzido de diploma não identificado. Não presume onde acaba a reprodução nem atribui suas remissões à norma hospedeira. Mantém a exclusão conservadora do artigo inteiro da política anterior; não libera automaticamente referências introdutórias anteriores à citação. Esse limite pode omitir referências legítimas e está documentado, não mascarado como interpretação da transcrição.

A verificação é calculada uma vez por artigo na extração, evitando repetir a varredura para cada candidata.

### Elegibilidade — `scripts/remissions/eligibility.mjs`

Além das condições já existentes, revalida a identidade normativa diretamente anexada à ocorrência e a extensão integral da evidência. Uma saída antiga/forjada com “desta Lei” truncada antes da identidade contraditória não supera a política. A guarda de reprodução é compartilhada, sem duplicar regex divergentes.

Política 1a.1 mantém **as mesmas quatro classes**, `experimental-only`, revisão independente pendente e geração opcional. Nenhuma mudança na apresentação.

### Testes e ferramentas de análise

- `tests/fixtures/remissions-1a-1/adversarial.json`: novas entradas e expectativas declaradas; fixtures anteriores intactas.
- `tests/node/remissions-adversarial.test.js`: 18 regressões, incluindo os 14 casos e verificações suplementares.
- `tests/node/remissions-integration.test.js`: o teste que documentava CPP 158 como defeito agora exige abstenção C, nenhum destino resolvido e nenhuma aresta CPP 158. Preserva os demais controles; não altera o gold anterior para coincidir com o parser.
- `scripts/remissions/adversarial.mjs`: execução reproduzível sobre cópias, com opção de usar implementação arquivada.
- `scripts/remissions/compare-robustness.mjs`: comparação de ocorrências elegíveis e build padrão, mais variantes históricas. Apenas ferramenta de análise, sem ligação com o build publicado.

## 3. Comparação antes/depois

Arquivos completos: [métricas anteriores](fase-1a-1/metrics-before.json), [posteriores](fase-1a-1/metrics-after.json), [delta](fase-1a-1/eligibility-delta.json). Mesmo corpus e hashes jurídicos nas duas versões; 7.110 entradas estatutárias. Cinco execuções Node 22.23.3 no mesmo host AMD EPYC 9V74, sem limitação de CPU; medianas em memória, incluindo verificação SHA. São medições locais, não limiares absolutos nem benchmark móvel.

| Medida | 1A | 1A.1 |
|---|---:|---:|
| Ocorrências candidatas no corpus | 4.896 | 4.896 |
| Ocorrências elegíveis | 272 | 272 |
| Arestas únicas elegíveis | 329 | 329 |
| Candidatas excluídas | 4.624 | 4.624 |
| Arestas elegíveis acrescentadas/removidas | — | **0 / 0** |
| Índice bruto (bytes) | 54.795 | 54.795 |
| Gzip local (bytes) | 18.728 | 18.716 |
| Dados offline com índice (bytes, sem módulos) | 16.367.987 | 16.367.987 |
| Módulos opcionais (bytes) | 4.891 | 4.891 |
| Extração, mediana (ms) | 464,88 | 504,64 |
| Elegibilidade, mediana (ms) | 15,75 | 34,77 |
| Grafo/serialização, mediana (ms) | 2,96 | 1,45 |

Há aumento observado de aproximadamente 57 ms na soma das três medianas do build experimental. Não se afirmou aceleração: a revalidação normativa e as guardas adicionais têm custo. Não há extração no navegador. O build padrão, incluindo HTML, manifesto e todos os arquivos do pacote, é **idêntico byte a byte** à base 1A; o script de comparação confere isso. Nenhum download adicional foi acrescentado. Os bytes do índice experimental mudam por versões/hashes/IDs de ocorrência, mesmo com o mesmo conjunto de arestas e tamanho bruto.

Distribuição das rejeições mudou, pois problemas agora são identificados antes do gate: C 1.857 → 1.886; B 84 → 68; D 1.185 → 1.185; E 7 → 7; sintaxe não autorizada 1.084 → 1.070; identidade revalidada 0 → 9; reprodução no gate 8 → 0 (agora essas ocorrências já não são A). Listas complexas 395 e editoriais 4 permanecem iguais. **Mudança de motivo não é nova conexão nem prova de falso positivo em todo item reclassificado.**

### Amostra anotada anterior, preservada

Nos 19 parágrafos/24 expressões da amostra adicional 1A, com 25 destinos esperados:

| Resultado | Antes | Depois |
|---|---:|---:|
| Destinos A emitidos pelo bruto | 20 | 19 |
| Destinos corretos na anotação existente | 19 | 19 |
| Destinos incorretos confirmados nessa amostra | 1 | 0 |
| Precisão amostral do bruto | 19/20 (95%) | 19/19 (100%) |
| Cobertura dos destinos esperados | 19/25 (76%) | 19/25 (76%) |
| Destinos esperados não confirmados pelo bruto | 6 | 6 |
| Destinos emitidos/corretos após política | 7/7 | 7/7 |
| Destinos esperados omitidos pela política | 18 | 18 |

A referência errada CPP 158 foi retirada por abstenção, não substituída por uma nova relação presumida. O percentual de 100% refere-se exclusivamente a esses 19 destinos da amostra preexistente, sem revisão humana independente. Não certifica o acervo. Os contadores genéricos do avaliador filtrado não devem confundir B/C/D excluídos com falhas de detecção; omissões acima são a diferença entre destinos esperados e destinos corretos confirmados.

## 4. Testes executados

| Verificação | Resultado |
|---|---|
| Testes dirigidos `node --test tests/node/remissions*.test.js` | 75 aprovados na primeira rodada; sem falhas |
| `npm test` após as correções finais | **127 aprovados**, zero falhas/skip; inclui build padrão de produção |
| Reexecução de `remissions-adversarial.test.js` após tornar o helper comparável à base | **18 aprovados** |
| `python -m unittest discover -s tests -p 'test_*.py'` | **46 aprovados** |
| `python scripts/run_browser_tests.py --suite essential` | **12 verificações aprovadas**, zero falhas |
| Reconstrução do índice, mesmos objetos/regras/política | Bytes idênticos em execuções repetidas |
| Comparação de build padrão contra arquivo Git da 1A | HTML, manifesto e todos os arquivos idênticos |
| Comparação das relações elegíveis por origem/localização e destinos | Nenhuma inclusão ou remoção |
| Integridade dos arquivos jurídicos e fixtures anteriores | Nenhuma alteração |

A suíte essencial executou interface, carregamento progressivo, leitura, navegação, busca, home, favoritos, cópia, PWA, política offline, contrato do benchmark e integração de remissões. Esta última confirmou instalação inicial sem índice, carga explícita única em chamadas simultâneas, índice em cache offline sem implicar texto de destino disponível, falhas de rede/SHA com recuperação, preparo completo, atualização consentida e duas abas de edições diferentes. Os testes Node verificaram rejeição de contratos/edições incompatíveis e invalidação por origem, destino, regras e política, além de remover/renomear destinos e alterar escopo ou tachado.

Não houve falhas nas suítes finais. Na revisão intermediária da guarda de reprodução, o comparador detectou três referências introdutórias que seriam liberadas por uma versão restrita ao prefixo da citação. Essa abordagem foi descartada: preservou-se a exclusão do artigo inteiro. As métricas e o delta entregues são da versão final, sem essas três inclusões.

Não foram repetidas auditorias gerais ou medições de navegador sem relação com a correção. Não houve teste físico Android, revisão jurídica humana independente ou ampliação para três abas/duas atualizações nesta fase; isso permanece pendência, não resultado aprovado.

## 5. Reprodução

```sh
# Node 22 e Chromium/Playwright do ambiente existente; sem dependências novas.
npm test
python -m unittest discover -s tests -p 'test_*.py'
python scripts/run_browser_tests.py --suite essential
node scripts/remissions/adversarial.mjs test-results/adversarial-after.json
node scripts/remissions/measure-integration.mjs test-results/metrics-after.json

# Arquivo temporário da implementação anterior, sem branch/worktree adicional:
mkdir -p /tmp/lexa-1a-base
git archive 3bb3c412e06f23a7be27458669ddd1448f35a130 | tar -x -C /tmp/lexa-1a-base
node scripts/remissions/adversarial.mjs test-results/adversarial-before.json /tmp/lexa-1a-base
node scripts/remissions/compare-robustness.mjs /tmp/lexa-1a-base test-results/eligibility-delta.json
# Para medir a base, executar seu measure-integration.mjs a partir do arquivo Git:
(cd /tmp/lexa-1a-base && node scripts/remissions/measure-integration.mjs /tmp/metrics-before.json)
```

A comparação de casos aplica exatamente as mesmas cópias do corpus às duas implementações. As medições preservadas no relatório foram executadas, não estimadas. Os parâmetros temporários não entram no pacote público.

## 6. Casos bloqueados e riscos residuais

- CPP 13-A e outras coordenações sem gramática suficiente ficam C; não se resolveu automaticamente CP 158.
- Intervalos, anáforas, qualificadores compartilhados complexos, edições externas e remissões históricas continuam fora das classes elegíveis.
- Reprodução é reconhecida por marcadores lexicais declarados, sem parser geral de transcrição. Formulações ainda desconhecidas podem exigir novo teste e bloqueio. A guarda do artigo inteiro pode omitir referências introdutórias legítimas, por segurança.
- Contexto anterior misto é tratado conservadoramente; não se tenta provar vigência ou relevância jurídica de cada palavra riscada. Tachado e contexto são distintos do diagnóstico de resolução.
- A bateria não constitui prova de ausência de toda forma possível de identidade conflitante. Não expandir classes com base na precisão de uma amostra pequena.
- Não há mudança na estrutura geral da PWA, no contrato da API ou na retenção existente de edições. As limitações de dispositivo físico e longa duração da fase anterior permanecem.

## 7. Recomendação

Revisar e aceitar, se aprovado, esta correção isolada contra a branch 1A. **Não ativar a interface nem retirar `experimental-only`.** As falhas reproduzidas foram corrigidas ou convertidas em abstenção; os controles positivos e as 329 arestas experimentais anteriores foram preservados. Antes da etapa visual, manter a revisão humana independente da política e das relações, com aceite explícito da coordenação. Testes automatizados aprovados não substituem essa revisão.

Leitor, interface, textos jurídicos, PDFs, fontes, históricos e fixtures anotadas anteriores permaneceram inalterados. Nenhum merge ou deploy foi executado.
