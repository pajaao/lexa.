# Parecer independente — Qualidade e Testes — Fase 1A.1

**Data:** 18/10/2026. **Base:** `funcionalidade/remissoes-fase-1a` (`3bb3c412e06f23a7be27458669ddd1448f35a130`). **Revisada:** `correcao/remissoes-fase-1a-1`. **Escopo:** apenas o delta 1A → 1A.1; sem auditoria geral.

## Correções verificadas

A inspeção do código em `scripts/remissions/{norms,extract,eligibility,context}.mjs`, do diff e de `docs/remissoes/fase-1a-1.md` sustenta:
- **A01:** qualificador `desta Lei` com número/ano contraditórios não deve herdar a norma de origem. A elegibilidade revalida a identidade e a extensão da evidência.
- **A02:** reprodução de diploma não identificado recebe bloqueio lexical conservador, sem inferir remissão local.
- **B01:** ADCT com ano explícito diferente de 1988 é externo, não ADCT/1988. CF e ADCT mantêm escopos distintos; B03 permanece fora da classe elegível.
- **B02:** `historical.context=mixed` não é mais reduzido a `clear`; variantes com `consultar`, `aplicar` e `considerar` deixam de atravessar o gate.
- **C01:** a guarda de reprodução examina todos os parágrafos e mantém a exclusão conservadora do artigo.
- **CPP 13-A:** referência não qualificada em coordenação com identidade concorrente deixa de ser atribuída a CPP 158; não se inventa CP 158.

**Evidência de execução apenas relatada:** os arquivos `docs/remissoes/fase-1a-1/{adversarial-before,adversarial-after,eligibility-delta,metrics-before,metrics-after}.json` registram 14 casos centrais, variantes B02, 18 testes adversariais aprovados, 127 testes Node, 46 Python e 12 verificações essenciais de navegador. **Esta frente não reexecutou suítes**; inspecionou código, testes, relatório e resultados arquivados. A comparação relata 329 arestas elegíveis antes/depois, sem inclusão ou remoção, e build padrão idêntico.

## Falhas ou regressões demonstradas

**Nenhuma falha adicional demonstrada na versão final** pela evidência examinada. Antes das correções, os artefatos registram associações indevidas aceitas em A01, A02, B01 e C01; B02 tem variantes que atravessavam o gate, enquanto a frase original com `ver` já era rejeitada. CPP 13-A era erro de resolução bruta bloqueado pela política. Depois, esses casos são rejeitados ou classificados conservadoramente. C03 e C04 preservam destinos positivos esperados.

A ausência de regressão no conjunto de 329 arestas e nos fixtures **não demonstra** ausência universal de falsos positivos jurídicos.

## Riscos não comprovados

- Formulações de reprodução não cobertas pela guarda lexical; exclusão de artigo inteiro pode causar falsos negativos.
- Outras identidades históricas, anáforas e coordenações normativas não contempladas.
- Sem revisão jurídica humana independente e sem medição em Android físico ou teste prolongado de múltiplas atualizações.
- Custos de build experimental aumentaram segundo métricas relatadas; não há evidência de novo download no build padrão.

## Bloqueios e critérios para avançar

1. Manter `experimental-only`, as quatro classes de elegibilidade e a abstenção ante norma, edição, escopo ou histórico incertos.
2. Exigir revisão humana independente das relações e adjudicação de divergências antes de ativar apresentação.
3. Confirmar em testes dirigidos, quando necessário, os negativos A01/A02/B01/B02/C01/CPP13A, os positivos C03/C04 e a integridade dos hashes/edições.
4. Submeter à Coordenação Central os critérios de desempenho móvel, isolamento offline de edições e autorização de qualquer próxima fase.

## Veredito

**APROVAR COM RESSALVAS** a correção **isolada e experimental** da Fase 1A.1. A inspeção do código é consistente com os resultados adversariais arquivados: os erros prioritários foram tratados por resolução mais estrita ou abstenção, sem ampliação das classes autorizadas. **Não aprovar, por este parecer, Fase 1B, ativação de links, merge ou deploy.** Nenhuma conexão juridicamente incerta deve ser liberada para aumentar cobertura.
