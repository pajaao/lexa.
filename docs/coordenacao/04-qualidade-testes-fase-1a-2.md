# Parecer independente — Qualidade e Testes — Auditoria 1A.2

**Escopo:** branch `validacao/remissoes-fase-1a-2` comparada com `correcao/remissoes-fase-1a-1`. Verificação restrita à confiabilidade da auditoria automatizada, sem repetir a auditoria geral e sem validar juridicamente as remissões.

## Descobertas e classificação das evidências

**Contagens documentalmente coerentes:** 329 arestas de 272 ocorrências elegíveis; 292 consistentes na verificação automatizada, 8 suspeitas, 29 inconclusivas e zero erros confirmados pelo auditor. O relatório registra 353 participações ocorrência–aresta. A amostra de rejeições contém 354 registros de 4.624 rejeições, distribuídos em 203 estratos de risco.

**Método parcialmente independente:** `scripts/audit-remissions/checks.mjs` aplica verificações lexicais próprias de identidade, número, escopo, proveniência, runs riscados, contexto e notas do destino, sem importar a gramática, o resolvedor ou a política do extrator. Contudo, o universo de arestas e seus metadados vêm do pipeline auditado. O auditor não detecta remissões nunca extraídas, nem substitui cotejo jurídico humano ou fontes oficiais.

### Oito suspeitas

- **Alertas históricos (5):** ADCT 107-A → ADCT 107; CLT 413 → CLT 384; CLT 461 → CLT 510; CPC 499 → CC 757; CPP 211 → CPP 561. Notas de revogação ou texto riscado no destino justificam revisão documental, mas não comprovam associação indevida ou vigência.
- **Antecedentes concorrentes (3):** ECA 161 → ECA 24; ECA 190-F → ECA 190-A; Licitações 1 → Licitações 178. A presença de outra lei anteriormente no parágrafo é alerta lexical; não invalida, por si, `desta Lei`. Possíveis falsos alarmes conservadores.

**29 inconclusivas:** referências parentéticas sem identidade normativa expressa no núcleo. A classificação é prudente, mas uniforme: não discrimina contexto local inequívoco de reprodução ambígua. Exige revisão individual; não se pode converter convenção local em prova independente.

**Erro confirmado nesta revisão:** nenhum defeito adicional demonstrado nos critérios e resultados examinados. **Suspeitas fundamentadas:** os oito alertas acima, sem qualificá-los como erros jurídicos. **Limitações do método:** dependência do universo extraído, triagem lexical e ausência de confronto humano integral. **Ausência de evidência de defeito:** não foram demonstradas regressões no conjunto elegível, o que não prova inexistência de falsos positivos ou falsos negativos.

## Rejeições e riscos residuais

A seleção determinística de até dois registros por estrato amplia cobertura de riscos; não é amostragem estatística para estimar precisão ou recall. Inclui 146 ocorrências A rejeitadas, 23 B, 93 C, 89 D e 3 E. Não abrange referências omitidas pelo extrator. Priorizar os casos de ambiguidade/limitação, reprodução, histórico e qualificadores compartilhados sem promover automaticamente vínculos.

Riscos residuais: classificações `consistente` excessivamente confiantes diante de contexto normativo não capturado; alertas conservadores de antecedentes e notas históricas; falsos negativos invisíveis ao universo auditado; ausência de certificação independente da integridade byte a byte e da reprodutibilidade.

## Evidência inspecionada versus executada

**Inspecionado por esta frente:** diff das branches; `docs/remissoes/fase-1a-2.md`; manifesto; código de `scripts/audit-remissions/{checks,run}.mjs`; testes `tests/node/remissions-audit.test.js`; contagens e lógica da amostragem; descrições dos 37 casos prioritários e artefatos arquivados.

**Relatado pela implementação, não reexecutado nesta revisão:** sete testes próprios de auditoria, 41 testes Node direcionados, build padrão, cinco grupos de integração de navegador, regeneração determinística e comparação de hashes/CSV. Não houve execução independente de testes, recomputação dos hashes do manifesto, regeneração dos inventários ou verificação programática exaustiva de todos os IDs e spans dos JSONs volumosos. Portanto, consistência e reprodutibilidade são **relatadas e parcialmente inspecionadas**, não certificadas por esta frente.

## Veredito e condições

**APROVAR COM RESSALVAS os artefatos como insumos para revisão documental posterior.** São estruturados e auditáveis, mas **não homologam** as 329 conexões nem autorizam sua apresentação no leitor.

Antes de qualquer liberação: (1) adjudicar individualmente as oito suspeitas; (2) revisar o contexto das 29 parentéticas; (3) conferir amostras de rejeições e riscos não capturados; (4) confirmar independentemente hashes, IDs, CSV e reprodução quando exigido pela Coordenação; (5) manter as quatro classes, `experimental-only` e a abstenção em qualquer identidade ou condição histórica incerta.

**Este parecer não autoriza merge, deploy, ativação de links ou avanço automático de fase.** Consistência automatizada não equivale a validação jurídica independente.
