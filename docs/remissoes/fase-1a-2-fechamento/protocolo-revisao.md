# Protocolo de revisão documental restante — proposta à Coordenação

Não homologa relações nem interpreta vigência. Mantém `experimental-only`, quatro classes, leitor sem remissões e inventário original intacto. Revisão assistida por IA não substitui adjudicação humana independente.

## Critério proposto para parentéticas

**P1 — Autorreferência inequívoca pela estrutura literal.** Exigir ligação sintática verificável à norma/edição: nome e identidade normativa explícitos, ou expressão de autorreferência inequívoca ancorada no diploma, sem qualificação concorrente. Reter fonte, trecho completo, escopo, offsets e edição. Pode ser candidata à conferência humana; nunca autoriza uma nova classe ou ativação automática. O título do arquivo, a existência do número na biblioteca e a convenção “sem nome = mesma lei” isoladamente não bastam.

**P2 — Antecedente normativo próximo.** Exigir identidade explícita e ponte sintática inequívoca na mesma unidade textual. “Próximo” não é distância em caracteres: a ligação deve ser gramaticalmente documentada. Registrar o antecedente e a ponte literal. Se há mais de um antecedente possível, permanecer pendente; se há contradição demonstrada, bloquear. Notas editoriais de redação posterior não se propagam para trás como identidade do destino.

**P3 — Identidade não demonstrada ou contraditória.** Sem identificação suficiente, concluir **pendente de decisão** e não promover. Com identidade/edição/escopo expressos contraditórios ao destino, concluir **bloqueada**, com evidência de contradição. Não substituir por outro diploma por coincidência numérica. CF, ADCT e constituições anteriores são distintos.

**P4 — Reprodução, alteração e histórico.** Identidade dependente de texto necessário riscado, ou dispositivo reproduzido sem atribuição documental segura: bloquear. Reprodução possível sem fronteiras demonstráveis: pendente. Uma nota histórica ou de revogação no destino, por si só, não torna incorreta a associação literal da origem: registrar para adjudicação, sem inferir vigência. A posição histórica exige edição e runs, não um resumo temático.

**P5 — Semelhança temática apenas.** Proibida como evidência de elegibilidade. Se só há afinidade temática e não há remissão textual expressa, bloquear a proposição de relação. Se há número expresso mas falta diploma, isso é P3, não uma referência puramente temática: manter pendente.

### Aplicação às 30 relações existentes

Todas têm números expressos, mas nenhuma fornece, nos trechos examinados, identidade nominal/deítica suficiente ou ponte normativa explícita aprovada para substituir a convenção local. Distribuição provisória: **0 candidatas, 0 bloqueadas por contradição demonstrada, 30 pendentes de decisão**. CPP 211 → CPP 561 também exige tratamento do alerta histórico do destino. Não foi inferida uma associação errada nem removida qualquer aresta.

`parenteticas.csv` individualiza as 30 arestas com IDs originais, ocorrência, origem/destino, hashes, offsets, prefixo/sufixo literal, cabeçalho do destino, nota específica e conclusão provisória. Essas conclusões documentais assistidas não preenchem a revisão humana original nem autorizam uma exceção de produção. A Coordenação deve aprovar ou revisar P1–P5 e designar revisores antes de qualquer aplicação liberatória.

## Ordem de revisão

1. **Resolver a decisão documental das sete correspondências sustentadas no adendo de Integridade**, com notas históricas em quatro e falsos alarmes de antecedente em três. Preservar a distinção entre esse parecer e aprovação humana. CPP 211 → CPP 561 fica no grupo de 30, não no de sete.
2. Revisar as 30 parentéticas segundo P1–P5, priorizando CPP 211 → CPP 561 e outros destinos com contexto histórico. Não usar coerência temática como desempate.
3. Revisar individualmente as **292 arestas consistentes automaticamente**, começando por leis numeradas externas à origem, escopo ADCT, artigos com letras/milhar, listas e qualificadores; depois as autorreferências simples. “Consistente” é triagem técnica, não aprovação jurídica. Registrar decisão para todas, sem aprovar em lote por testes verdes.
4. Revisar as **354 rejeições amostradas**: primeiro os 78 casos de limitação/ambiguidade; depois qualificadores compartilhados e identidade não verificada; reprodução/histórico; sintaxes deliberadamente não autorizadas; externos e falsos candidatos. Conservar os motivos originais e documentar se a omissão foi intencional, uma ambiguidade real ou falha demonstrada de reconhecimento. Não promover resultados.
5. Investigar **referências não detectadas** por seleção de texto independente da saída do extrator: escolher previamente artigos/parágrafos por norma, escopo e edição com semente pública; congelar a lista antes de consultar candidatos. Incluir parágrafos sem candidatos, com runs riscados, listas, transcrições e normas externas. Dois revisores enumeram manualmente referências literais e destinos/abstenções. Só depois confrontar com a saída existente.

A amostra de rejeições é estratificada por risco e não representa o universo de remissões. Não estima recall, cobertura ou precisão global. Uma amostra futura de texto bruto deve ter objetivo, desenho, denominadores, anotação e limites próprios; não somar seus números à amostra anterior como se tivessem o mesmo desenho.

## Ficha de evidência obrigatória

Usar cópia de revisão dos CSVs; não sobrescrever os aprovados. Conservar ID original e geração. Acrescentar responsável, data, versão do protocolo e edição consultada. Para cada ocorrência/destino:

- Norma/espécie/número/ano, escopo e artigo de origem/destino; hashes da edição e do artigo.
- Parágrafo, offsets UTF-16 e runs; literal, antecedente normativo e ponte sintática, se existentes; texto anterior/posterior necessário.
- URL/identificação da fonte oficial e data de consulta, distinguindo edição oficial consultada da edição incorporada. Se não houver acesso ou correspondência de edições, registrar a limitação e abster-se.
- Estado histórico do núcleo, qualificadores e evidência normativa. Notas no destino separadas de evidência necessária riscada na origem.
- Critério aplicado (P1–P5), decisão do revisor, justificativa objetiva, evidência consultada e necessidade de adjudicação.

Não justificar por “faz sentido”, mesmo tema, número existente ou confiança do modelo. Não registrar revisão por IA como assinatura de especialista independente.

## Divergências e adjudicação

Revisor primário registra parecer sem ver a decisão do segundo, quando possível. Um segundo revisor independente confere casos liberáveis, dúvidas de identidade/edição/histórico, suspeitas e divergências. Manter ambos os pareceres, sem substituir um pelo outro. O adjudicador registra a divergência, evidência determinante e decisão, com identidade/data. Sem consenso documentado, permanecer bloqueada para exposição pública.

Decisões possíveis: **correspondência documental confirmada**, **pendente**, **bloqueada por contradição/insuficiência necessária**, **externa ao acervo**, **falso candidato**, **falha de reconhecimento a corrigir separadamente**. “Confirmada” não certifica vigência nem autoriza build público. Qualquer mudança de aresta, gramática, política ou classe exige tarefa de correção/implementação separada e nova revisão, sem editar este inventário para melhorar métricas.

## Critérios objetivos de aceite pela Coordenação

- Verificador técnico sem divergências; cinco artefatos originais reproduzidos byte a byte; inventário e regras protegidos sem alteração.
- Cada uma das 30 parentéticas com registro individual, critério, evidência e decisão humana/adjudicação, inclusive se a decisão for manter pendente.
- As 292 consistentes e a amostra de 354 não recebem aprovação automática. Responsáveis e progresso rastreáveis por ID; denominadores preservados.
- Para qualquer relação proposta à exposição: norma/edição/escopo inequívocos, número/qualificadores fiéis e destino existente; nenhuma evidência necessária histórica ou reprodução sem atribuição segura; revisão humana independente e divergências resolvidas. Na dúvida, não liberar.
- Decisão expressa e versionada sobre a convenção parentética, sem ampliar as quatro classes nesta etapa; decisão separada sobre tratamento histórico do destino.
- Autorização explícita da Coordenação para qualquer fase visual. Até lá, `experimental-only`, build padrão desligado e nenhum merge/deploy automático.
