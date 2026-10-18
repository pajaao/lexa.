# Parecer — Qualidade e Testes | Lexa Fase 1A

## 1. Identificação
- **Frente:** Qualidade e Testes.
- **Data:** 18/10/2026.
- **Repositório:** https://github.com/pajaao/lexa.
- **Base main verificada:** `84c5bb5c5e28c08376e0bf40cf3f3f4b4fd783cf`.
- **Branches examinadas:** `investigacao/remissoes-fase-0-5` (base documental `b414204aadf24d0a0d213365060bc347b3f3847d`, conforme relatório da fase) e `funcionalidade/remissoes-fase-1a`. Comparações GitHub: ambas estavam à frente de `main`, respectivamente 6 e 9 commits, sem incorporação à base examinada. A análise original inspecionou arquivos nessas branches; não foi registrada verificação independente de cada SHA de ponta. Hash do extrator reportado: `6cf232f85d242a28dd81ff654811106327f13948948b884afe8b7d289d3ae434` (hash de conteúdo, **não** commit).
- **Natureza:** parecer documental baseado na análise já realizada; não houve execução independente de suíte ou revisão jurídica humana.

## 2. Escopo
Avaliar criticamente o extrator determinístico e a política experimental 1A, priorizando falsos positivos, normas não identificadas, incompatibilidade de edições, ambiguidades, tachado, reprodução normativa e degradação da PWA. Sem modificação de código ou legislação.

## 3. Evidências verificadas
1. [Relatório 1A](../remissoes/fase-1a.md) e [métricas](../remissoes/fase-1a/metrics.json): 4.896 ocorrências candidatas, 272 elegíveis, 329 arestas, 4.624 rejeições. Na amostra adicional de 19 parágrafos, o extrator bruto emitiu 20 destinos (19 corretos, 1 incorreto); a política emitiu 7/7 corretos conforme anotação do próprio agente, cobertura 7/25. **Não extrapolar** essa precisão para o acervo.
2. [Extrator](../../scripts/remissions/extract.mjs), [gramática](../../scripts/remissions/grammar.mjs), [resolução de normas](../../scripts/remissions/norms.mjs) e [política](../../scripts/remissions/eligibility.mjs): separação entre classificação e elegibilidade; o reconhecimento lexical e contextual pode produzir resolução incorreta antes do filtro.
3. [Testes Node](../../tests/node/remissions-integration.test.js): incluem o caso CPP 13-A e rejeição pela política; são evidências de testes escritos e resultados relatados, não reexecução desta frente.
4. [Integração PWA](../../tests/browser/remissions_integration.py), [service worker](../../src/sw.js), [métricas Chromium](../remissoes/fase-1a/browser-metrics.json): build padrão sem índice; índice opcional com SHA, lazy loading e cache. Relatório: 54.795 bytes de índice, mediana de 66,2 ms para API experimental, +21 bytes de transferência no padrão. Não houve medição em Android físico nem teste de longa duração.
5. A revisão adicional foi produzida pelo próprio agente de desenvolvimento; **não constitui auditoria jurídica humana independente**.

## 4. Problemas confirmados
| ID | Gravidade | Evidência e reprodução | Impacto |
|---|---|---|---|
| Q-CONF-01 | Alta no extrator bruto; mitigado na política 1A | CPP art. 13-A: `art. 158` foi atribuído a CPP 158 quando a enumeração remete a CP 158. Ver `metrics.json > additional.raw.errors` e teste `caso novo CPP13-A`. A política não publica CPP 158. | Demonstra que classe A isolada não certifica destino correto. |
| Q-CONF-02 | Limitação de validação, bloqueante para liberação | 7/7 da amostra filtrada foram anotados pelo mesmo agente, sem revisão independente; ver relatório e `sampling.json`. | Testes verdes não certificam integridade jurídica integral. |
| Q-CONF-03 | Limitação de cobertura de desempenho | Métricas Chromium em desktop emulado, CPU 4×, HTTP local; sem móvel físico. | Não há prova de ausência de degradação em dispositivos modestos. |

Não há confirmação de falsos positivos adicionais **atravessando a política**: os itens seguintes são hipóteses a reproduzir.

## 5. Hipóteses e riscos adversariais
As entradas são **sintéticas** e devem ser injetadas apenas em cópias do corpus em memória; não representam redação real das normas. Para todos os negativos, saída esperada: nenhuma aresta elegível.

| ID | Entrada e origem sintética | Risco e resultado esperado | Prioridade |
|---|---|---|---|
| A01 | Lei 14.133, art. 100: `Consultar o art. 147 desta Lei nº 8.666/1993.` | `desta Lei` pode ser consumido antes da numeração contraditória; rejeitar por identidade incompatível. | P0 |
| A02 | CC 900: `No trecho reproduzido de um diploma não identificado: (art. 186).` | Parentética presumida como local em transcrição; abster-se. | P1 |
| A03 | CC 900: `Consultar o art. 186 da Lei nº 3.071/1916.` | Não ligar à edição atual. | P1 |
| A04 | CPC 300: `Consultar o art. 186 da mesma lei.` | Anáfora sem identificação inequívoca; rejeitar. | P1 |
| A05 | ADCT 95: `Consultar o art. 84 da Constituição Estadual do Rio Grande do Norte.` | Não mapear para CF. | P1 |
| B01 | ADCT 95: `Consultar o art. 84 deste Ato das Disposições Constitucionais Transitórias de 1967.` | Sufixo histórico pode ser ignorado; não ligar a ADCT/1988. | P0 |
| B02 | Lei 14.133, art. 100: run **riscado** `Segundo a Lei nº 8.666/1993, ` + run atual `ver art. 147 desta Lei.` | `condition()` produz contexto misto, mas `extract.mjs` o reduz a `clear` na dimensão contextual; não emitir aresta. | P0 |
| B03 | ADCT: `Consultar o art. 84 da Constituição Federal de 1988.` | Distinguir escopo principal do ADCT; permanecer fora das classes 1A não autorizadas. | P1 |
| B04 | Lei 14.133, art. 100: run inteiramente riscado `Consultar o art. 147 desta Lei.` | Classificação D, zero arestas. | P1 |
| C01 | Lei 14.133, art. 100, **terceiro** parágrafo: `Passa a vigorar a seguinte redação: “art. 147 desta Lei”.` | `amendmentContext()` examina só os dois primeiros parágrafos; rejeitar reprodução normativa. | P0 |
| C02 | Lei 14.133, art. 100: `Confira os arts. 147 a 150 desta Lei.` | Intervalo não autorizado, zero arestas. | P1 |
| C03 | CC 900: `Confira (arts. 186 e 187).` | Controle positivo: CC 186 e 187, com proveniência íntegra. | P1 |
| C04 | CPC 300: `Aplicam-se os arts. 186 e 187 da Lei nº 10.406/2002.` | Controle positivo: CC 186 e 187. | P1 |

**Reprodução:** checkout da branch 1A em Node 22; executar `buildPackage()`; construir corpus a partir dos JSONs do manifesto; `structuredClone`; substituir apenas `paragraphs[].runs` do artigo de origem; recalcular SHA com `sha256(JSON.stringify(code))`; chamar `extractRemissions(corpus,{selected:[codeId]})`, depois `applyEligibility(corpus, extraction)`; comparar `accepted[].resolution.targets` ao esperado e registrar classificação, `reason`, offsets e `historical`. O roteiro detalhado com script executável foi fornecido na avaliação anterior desta frente. **Ainda não executado** para os novos casos. Atribuir gravidade definitiva apenas após reprodução e adjudicação.

## 6. Recomendações priorizadas
**Obrigatórias antes de avançar para apresentação 1B:** (P0) executar A01, B01, B02 e C01; bloquear/corrigir classes que publiquem identidade, edição ou contexto histórico conflitantes; preservar a regra de abstenção; repetir regressões afetadas; realizar revisão humana independente das 329 arestas e amostragem estratificada de rejeições. (P0) demonstrar que origem e destino sempre pertencem à mesma geração jurídica e que a PWA falha fechada em índices inválidos.

**Aperfeiçoamentos opcionais:** (P1) ampliar testes de ambiguidades A02–A05/B03, controles positivos e corpus adversarial; (P1) ensaiar Android físico e cenários de memória limitada; (P2) avaliar desempenho da consulta linear às arestas em grafos sintéticos maiores, sem otimização prematura.

## 7. Critérios de aceite
1. **Segurança jurídica:** zero falso positivo confirmado nas classes liberáveis, após adjudicação independente; A01/B01/B02/C01 sem arestas indevidas; A03/A04/A05/B04/C02 sem arestas; C03/C04 com os dois destinos esperados. Relatar omissões separadamente.
2. **Proveniência:** offsets UTF-16 conferem com runs, tachado/contexto são preservados e mudanças de origem/destino/edição/política invalidam geração.
3. **PWA-01:** comparar main, padrão e experimental em Android real ou perfil limitado, p50/p95, memória, requisições e inicialização; sem carregamento automático do índice e sem regressão relevante definida antes da medição.
4. **PWA-02:** offline parcial com destino não armazenado deve falhar explicitamente sem texto incorreto.
5. **PWA-03:** corpo adulterado, SHA divergente, rede interrompida e resposta incompleta rejeitam o índice integralmente, com recuperação.
6. **PWA-04:** três abas e duas atualizações jurídicas sucessivas, incluindo offline, nunca misturam edições.
7. **PWA-05:** índices sintéticos de 1 mil, 10 mil e 50 mil arestas medidos quanto a latência, heap e responsividade; estabelecer limites com base em dispositivo-alvo.
8. Registrar versões, hashes, entradas, saídas e justificativa humana das divergências; não regenerar expectativas pelo próprio extrator.

## 8. Pendências para a Coordenação Central
- Aprovar ou ajustar o bloqueio de 1B até revisão jurídica humana independente.
- Designar responsáveis pela adjudicação das 329 arestas e da amostra de rejeições, sem confundir revisão por IA com humana.
- Definir limiares objetivos de desempenho móvel e política de retenção de edições offline.
- Decidir quais classes permanecerão experimental-only após os resultados adversariais; nenhuma ampliação por mera meta de cobertura.

## 9. Parecer final
**Manter a Fase 1A experimental e desabilitada no padrão.** A separação entre extração, elegibilidade e apresentação é adequada, mas a precisão jurídica global não está demonstrada. O erro confirmado CPP 13-A evidencia a importância do filtro; A01, B01, B02 e C01 são suspeitas de alta prioridade, **não defeitos confirmados**. Avançar somente após reprodução, eventual correção ou bloqueio conservador, revisão independente e aceite explícito da Coordenação Central. Sem autorização para merge ou deploy.
