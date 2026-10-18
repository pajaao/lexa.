# Fechamento documental da Fase 1A.2

## Resultado

Fechamento **documental e técnico**, sem homologação jurídica humana, mudança de arestas ou ativação no leitor.

- Inventário preservado: **329 arestas, 272 ocorrências, 353 participações** ocorrência–aresta.
- CSV de revisão humana: **683 registros**, campos de decisão/justificativa/evidência/adjudicação vazios.
- Amostra: **354 rejeições, 203 estratos**, população fornecida de **4.624 rejeições**.
- Verificador isolado: **sem divergências nos artefatos originais**.
- Duas execuções da auditoria existente: os **cinco arquivos gerados** são idênticos byte a byte entre si e aos aprovados.
- Parentéticas: **30 avaliadas individualmente; 0 candidatas, 0 bloqueadas por contradição demonstrada e 30 pendentes de decisão**.
- **10 testes direcionados aprovados**, incluindo corrupção simulada.

“Pendente” não significa erro comprovado nem exclusão do inventário experimental. Nenhuma das 329 arestas foi alterada. As quatro classes e `experimental-only` permanecem intactas.

## Bases e pareceres

Base: `validacao/remissoes-fase-1a-2`, commit **`316a979e32ef35ebc3d385b9e9a73e368806e1cf`**. Branch desta etapa: `validacao/remissoes-fase-1a-2-fechamento`.

Fontes lidas: relatório e artefatos 1A.2, `scripts/audit-remissions/`, adendo de Integridade e parecer de Qualidade específico:

| Fonte | Versão consultada |
|---|---|
| `docs/parecer-integridade`, seção 11 de `docs/coordenacao/02-integridade-juridica.md` | `0f84f8ebd6111b5140ed2b7e58d2a68778f0a9c7` |
| `docs/parecer-qualidade-fase-1a-2`, `docs/coordenacao/04-qualidade-testes-fase-1a-2.md` | `93557c005b38cc646fd2ec1e8863c88ca5e6abaf` |
| Conteúdo Git do PR #12, `refs/pull/12/head` | Mesmo commit `93557c005b38cc646fd2ec1e8863c88ca5e6abaf` |

Não foram presumidas decisões humanas a partir dos pareceres assistidos por IA. Não foram repetidas auditorias gerais.

## Consolidação das revisões

A triagem original **292 consistentes / 8 suspeitas / 29 inconclusivas** continua intacta. O adendo de Integridade faz uma leitura documental adicional das 37 prioritárias:

- **Sete correspondências documentalmente sustentadas**, sem liberação pública: ADCT 107-A → 107, CLT 413 → 384, CLT 461 → 510, CPC 499 → CC 757, ECA 161 → 24, ECA 190-F → 190-A e Licitações 1 → 178. Quatro têm alerta histórico no destino e três eram alertas conservadores de antecedente concorrente.
- **Trinta identidades insuficientemente demonstradas**: as 29 inconclusivas mais CPP 211 → CPP 561. A ausência de nome normativo não é suprida por coerência temática.
- Nenhuma associação indevida foi demonstrada pelos pareceres; isso não certifica todas as 329 relações.

Qualidade aprova os artefatos como insumo, com ressalvas: faltava executar conferência independente de hashes, IDs, CSV e reprodução. Esta etapa executa essa conferência computacional, mas **não converte** os pareceres em adjudicação jurídica humana e não reclassifica o inventário original.

## Critério proposto e aplicação às 30 parentéticas

O [protocolo](fase-1a-2-fechamento/protocolo-revisao.md) define cinco situações auditáveis:

1. **P1, autorreferência literal inequívoca:** identidade explícita ou expressão de autorreferência inequivocamente ancorada no diploma/edição, sem conflito. Pode ser candidata à revisão, sem autorização automática.
2. **P2, antecedente normativo próximo:** exigir antecedente explícito e ponte sintática documentada na mesma unidade textual. Proximidade em caracteres ou outra remissão numérica não bastam.
3. **P3, identidade não demonstrada/contraditória:** ausência de demonstração → pendente; contradição documental → bloqueada, sem substituição por número coincidente.
4. **P4, reprodução ou histórico:** evidência necessária riscada ou transcrição sem atribuição segura impede liberação. Nota histórica no destino é questão separada, não prova automática de erro da remissão.
5. **P5, semelhança temática apenas:** nunca evidência de elegibilidade. Número expresso sem norma é P3; não é prova temática que possa ser promovida.

Nenhuma das 30 expressões examinadas traz identificação normativa literal ou ponte inequívoca suficiente segundo essa proposta. A condição de pertencer ao mesmo arquivo, a existência do destino no acervo e a convenção local ainda não aprovada não satisfazem P1/P2. Isso inclui exemplos conhecidos como CC 927 → 186/187. “Ato ilícito” não é identificação de diploma.

**Distribuição por origem:** CC 16, CPP 9 (incluindo CPP 211 → 561), LEP 3 e CP 2. São **30 arestas de 26 ocorrências**, não 30 ocorrências independentes. Todas permanecem pendentes de decisão. Não há contradição demonstrada que justifique bloqueá-las definitivamente nem evidência suficiente para promovê-las como candidatas confirmadas.

[Parentéticas CSV](fase-1a-2-fechamento/parenteticas.csv) contém 30 linhas, IDs originais, identificação e hashes de origem/destino, parágrafo/offsets, literal, prefixo/sufixo, histórico informado, cabeçalho do destino, aplicação do critério, nota individual e conclusão provisória. Cada destino de uma lista tem linha própria e conserva o mesmo ID de ocorrência quando pertinente.

As notas distinguem, entre outros: “artigos antecedentes” em CC 1243, que não nomeia diploma; a expressão genérica “na forma da lei” em CC 985; notas editoriais posteriores em CPP 143 e CP 97; outras remissões numéricas sem diploma em CPP 68/211/597; e CPP 211 → 561 com alerta histórico no destino. Nenhum desses elementos é usado para resolver identidade por tema. O CSV novo é uma proposta assistida, não preenchimento dos campos de revisão humana originais.

## Verificador isolado: alcance e resultados

`scripts/verify_remissions_closure.py` usa **somente biblioteca padrão Python** (`csv`, `json`, `hashlib` etc.). Não importa nem chama o extrator, resolvedor normativo, elegibilidade ou funções do auditor anterior. Não regenera CSV para depois confiar no mesmo serializador: lê-o com `csv.DictReader` e reconstrói a correspondência dos campos a partir dos JSONs.

[verificacao.json](fase-1a-2-fechamento/verificacao.json) registra contadores, divergências, duas modalidades de execução, hashes dos métodos, resultados de reprodução, versões consultadas e testes.

### Efetivamente independentes dos algoritmos do pipeline

- SHA-256 e tamanho dos quatro arquivos listados em `manifesto.json`, conferidos contra seus bytes. A integridade do próprio manifesto é ancorada na comparação Git e na reprodução; ele não é uma assinatura externa.
- Contagem/unicidade das 329 arestas e suas tuplas; derivação dos IDs pela geração e origem/destino.
- 272 IDs de ocorrência distintos, derivação dos IDs e consistência das repetições; 353 participações, sem duplicação dentro de uma aresta.
- Correspondência de **todos os campos** de 329 linhas do CSV de arestas e 683 do CSV humano com os respectivos JSONs; IDs únicos e campos humanos vazios.
- 354 rejeições distintas, disjuntas das elegíveis; metadados, IDs, facetas, estratos, ranks e quotas. Somatório das populações declaradas por estrato: 4.624.
- SHA de cada cópia de artigo contida nos artefatos; parágrafos reconstruídos pelos runs; **1.395 spans UTF-16** de núcleo/qualificador/identidade conferidos, incluindo os registros rejeitados. Consistência entre runs e texto literal, localização e metadados.
- Correspondência entre metadados dos dois JSONs, contagens/status declarados e contrato experimental de quatro classes.

Sem o universo completo de rejeições, esses arquivos permitem confirmar os ranks e quotas selecionados, **mas não demonstrar que um registro omitido não teria rank menor**. A execução `artifactOnly` registra explicitamente essa limitação.

### Verificação computacional com insumos suplementares do pipeline

`scripts/reproduce_remissions_closure.mjs` executa o auditor aprovado em dois diretórios externos e exporta temporariamente o corpus e a população completa de candidatas/decisões para `snapshot.json`. Esse helper é o único que chama o pipeline; **não é o verificador independente**.

Com esse insumo, o Python:

- Recalcula o hash do corpus e os hashes integrais das **13 normas** presentes nas arestas/amostra, confrontando artigos com o corpus suplementar.
- Reconstitui, sem a função de amostragem do pipeline, os **203 estratos da população de 4.624 rejeições** e a seleção dos menores dois hashes por estrato.
- Confirma exatamente os **354 IDs selecionados** e a correspondência da população elegível com os 272 IDs inventariados.

Resultado: **zero divergências** nas duas modalidades. As contagens 329/272/353/354/683/203 foram conferidas, não apenas copiadas do relatório. Ainda assim, **universo, classificações e motivos** vêm do pipeline; não foram homologados semanticamente. Os hashes certificam correspondência dos dados fornecidos, não autenticidade externa da legislação ou vigência.

## Reprodutibilidade e preservação

Foram executadas duas auditorias completas com Node 22.23.3, em `/tmp/lexa-closure/repro/run-a` e `run-b`. Para cada um dos cinco resultados — `arestas.json`, `arestas.csv`, `rejeicoes-amostra.json`, `revisao-humana.csv`, `manifesto.json` — bytes e SHA são idênticos entre as duas execuções e aos aprovados. `validacoes.json` é registro histórico, não saída regenerada pelo auditor; permaneceu preservado no Git.

O helper rejeita como destino o diretório original aprovado. O verificador é somente leitura; seu CLI rejeita saída no diretório dos artefatos aprovados. O snapshot temporário não integra o pacote público ou os arquivos legais; sua função é expor a dependência de população/edição, sem apresentá-la como evidência jurídica independente.

Nenhum arquivo preexistente foi modificado. Extrator 0.5.2, elegibilidade 1a.1, corpus, histórico, PDFs, interface, PWA e scripts do auditor anterior continuam com os mesmos bytes. Não foi necessária nova rodada de benchmarks ou testes gerais de navegador para uma alteração isolada em documentos/verificação.

## Testes direcionados

`tests/test_remissions_closure.py`: **10 testes finais aprovados**, zero falhas. Incluem:

- Artefatos originais válidos e contagens.
- Hash corrompido.
- ID alterado e aresta duplicada.
- CSV divergente e decisão humana indevidamente preenchida.
- Span UTF-16 corrompido e distinção entre unidade UTF-16 e ponto de código (emoji).
- Rank da amostra adulterado.
- Correspondência das 30 parentéticas e ausência de promoção.

Exceto no teste específico de hash, os ataques atualizam tamanho/SHA no manifesto temporário: isso evita que o teste passe apenas porque o checksum detectou qualquer mudança, sem exercitar as invariantes semânticas de integridade.

**Problema encontrado no desenvolvimento do verificador:** a primeira comparação de unicidade conferia apenas a cardinalidade esperada do conjunto, sem exigir igualdade ao número total de linhas. A duplicação simulada revelou essa lacuna. Um helper de teste também sobrepunha indevidamente `TestCase.fail`, causando recursão no diagnóstico e encerramento da primeira rodada. Ambos foram corrigidos exclusivamente nos novos arquivos. A rodada final passou os dez testes; o resultado de verificação dos artefatos originais permaneceu sem divergências. Não se ocultou nem corrigiu o inventário para satisfazer o verificador.

### Reprodução

```sh
# Gera proposta documental separada, sem tocar no inventário:
python scripts/document_parenthetical_closure.py docs/remissoes/fase-1a-2/arestas.json /tmp/parenteticas.csv
# Verificação apenas dos artefatos:
python scripts/verify_remissions_closure.py docs/remissoes/fase-1a-2 --output /tmp/artefatos-verificados.json
# Duas execuções da auditoria aprovada em diretórios temporários:
node scripts/reproduce_remissions_closure.mjs /tmp/lexa-closure-repro
# Verificação da seleção com toda a população suplementar:
python scripts/verify_remissions_closure.py docs/remissoes/fase-1a-2 --snapshot /tmp/lexa-closure-repro/snapshot.json --output /tmp/verificacao-com-populacao.json
python -m unittest discover -s tests -p 'test_remissions_closure.py'
```

Sem dependências novas. Manter corpus e versões da base para reproduzir os hashes. As saídas temporárias não devem substituir os originais aprovados.

## Protocolo restante e decisões pendentes

[protocolo-revisao.md](fase-1a-2-fechamento/protocolo-revisao.md) define prioridade, ficha de evidência, revisão independente, adjudicação e critérios de aceite:

1. Deliberar sobre as sete correspondências sustentadas pelos pareceres e as ressalvas históricas, sem tratá-los como decisão humana já tomada.
2. Aprovar ou ajustar P1–P5 e revisar individualmente as 30 parentéticas, mantendo pendente quando faltar identidade inequívoca.
3. Conferir as 292 consistentes por identidade/escopo/edição, com decisões rastreáveis por ID; não aprovar em lote por testes verdes.
4. Revisar as 354 rejeições, priorizando os 78 casos de limitação/ambiguidade e sintaxes compartilhadas; separar omissão deliberada de defeito demonstrável. Não promover automaticamente.
5. Para referências não detectadas, congelar uma amostra de **texto bruto** antes de consultar a saída do extrator, incluindo parágrafos sem candidatas. Anotação humana independente e confronto posterior, com denominadores e limites próprios. A amostra de rejeições não estima cobertura global.

Revisor e adjudicador devem registrar norma/edição, fonte oficial e data, literal/ponte sintática, localização/runs, condição histórica, justificativa e divergências. Manter os dois pareceres em caso de discordância; sem adjudicação, não liberar. Erro confirmado exige tarefa separada de correção: não editar as arestas originais nesta fase.

**Aceite técnico proposto:** hashes/IDs/CSV/spans sem divergências, reprodução byte a byte, campos humanos originais vazios e nenhum arquivo protegido alterado. **Aceite documental/jurídico ainda pendente:** designação de pessoas independentes, decisão sobre P1–P5 e convenção local, adjudicação dos casos e autorização expressa para qualquer futura exposição pública.

As limitações incluem dependência do corpus/metadados do próprio pipeline, ausência de confronto oficial integral e de homologação humana. A verificação de dados pode ser independente do algoritmo que os gerou sem constituir independência jurídica. Esta entrega não autoriza a Fase 1B, ampliação de classes, retirada de `experimental-only`, merge ou deploy.
