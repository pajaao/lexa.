# Redações anteriores — integração e liberação do lote corrigido

## Governanca

O responsável por Produto solicitou integrar à main o lote corrigido após relatar avaliação favorável de um conjunto determinístico de artigos difíceis e pediu um ponto de restauração. A avaliação e a lista da amostra foram informadas pelo próprio responsável nesta conversa em 21/10/2026.

A liberação é registrada como decisão de Produto por avaliação de risco/amostragem. Não é uma declaração de homologação individual dos 3.036 registros nem de revisão jurídica humana independente de todo o lote. Os estados documentais permanecem pending. A autorização de consulta pública é distinta desses estados e não os transforma em approved.

## Avaliacao do responsavel

Declaração recebida: "Fiz uma avaliação de um conjunto determinístico com o histórico em artigos que são realmente dificultosos [...] em todos". O responsável solicitou colocar o conjunto na main e informou a seguinte amostra e os pontos de conferência:

| Legislação | Artigo | Escopo informado |
|---|---|---|
| Código Penal | 215 | Caput, penas, parágrafo único e rubrica anteriores |
| Código Penal | 334 | Quatro registros antes associados ao art. 333 |
| Código Penal | 234-A | Incisos III/IV e associação ao artigo |
| Código Penal | 65 | Redação antiga identificada no HTML |
| Constituição | 7 | Oito registros anteriores |
| CPC | 1.042 | Associação das redações anteriores |
| CPC | 1.063 | Associação das redações anteriores |
| ECA | 4 | Recuperação dos dispositivos antigos |
| ECA | 233 | Texto antigo próximo de nota editorial malformada |
| CPP | 406 | Numeração e contexto documental do procedimento do júri |

Protocolo registrado: amostra determinística de dez artigos, dirigida aos defeitos corrigidos e estruturas difíceis, com avaliação favorável relatada pelo responsável. Não há afirmação de que todos os demais artigos tenham recebido conferência individual. A lista recebida não detalha cada operação de confronto documental; não se presume uma auditoria integral dos 13 HTMLs pelo usuário.

Riscos residuais: casos fora da amostra, semântica de rubricas, associação documental em reorganizações e diferenças de apresentação. A funcionalidade não reconstrói sucessões nem comprova equivalência entre os textos antigos e atuais. Nos blocos antigos do CP/CPP, a interface mostra explicitamente essa ausência de equivalência estabelecida.

## Autorizacao de publicacao

A solicitação de integrar o lote completo à main, feita após a avaliação acima, autoriza este lançamento. Os campos governanceDecision, riskReviewDecision e publicationDecision do manifesto apontam para este registro humano; não foram preenchidos em razão apenas dos testes ou de parecer de IA. publicationAuthorized habilita consulta pública, preservando todos os estados pending.

O lote contém 3.034 ocorrências associadas e 3.036 registros. Foram preservadas 154 exclusões: estruturas supra-artigo/ementas, riscos sem texto normativo antigo, indicações de veto/revogação e duplicatas. As fontes, o texto vigente e os três registros aprovados do piloto original permanecem preservados em seus arquivos; nenhuma aprovação é transferida automaticamente aos novos IDs.

A distribuição deriva integralmente da fixture validada. O site transporta textos, notas, referências, fonte/hash/localização, contexto documental e identificadores das evidências. O HTML bruto permanece nos snapshots versionados; não é duplicado no pacote público.

A interface mantém caputs visíveis e a seção inicialmente recolhida "Outras redações anteriores", com contagem das demais unidades. Artigos sem caput anterior mostram diretamente as outras unidades. Não se altera o Histórico de versões.

## Ponto de restauracao

Tag remota anterior à integração: restore/redacoes-anteriores-20261021-f712d32.

Commit preservado: f712d32fed8a88d834c9a9b27bcc1bb5b8df531d.

Se surgir um problema relevante, preparar um PR que reverta o commit de integração e publique a versão restaurada. Não usar reset destrutivo ou force-push. Alternativamente, publicationAuthorized: false desativa o lote novo e restaura o piloto aprovado no build, sem apagar evidências ou alterar estados documentais. A PWA conserva a atualização consentida.

## Verificacao e reproducao

- scripts/prepare_previous_release.py --verify reproduz os 13 HTMLs, a associação completa, os fragmentos, as 154 exclusões e os hashes do lote público.
- npm test confere integridade, estados, autorização, leitura e isolamento das prévias.
- A suíte essencial de navegador valida desktop/celular, painel, agrupamento, teclado, posição de leitura e PWA antes do merge e da publicação.

Os resultados efetivamente executados desta integração ficam registrados no PR. Os documentos/validações anteriores em experiments/previous-wordings-release/20261021 permanecem preservados; seus números não são os deste lote.
