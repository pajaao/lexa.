# Atualização das fontes HTML — CF, CPP e CPC

21/10/2026 — preparação local de **Redações anteriores**, sem reconstrução legislativa.

## Fontes verificadas

Os três arquivos recebidos foram decodificados como **Windows-1252**, com origem salva em URL oficial do Planalto, marcações de riscados e encerramento HTML. Os cortes anteriores foram corrigidos nos pontos verificados:

| Fonte | Arquivo anterior | Novo arquivo |
| --- | --- | --- |
| CF | Interrompido no art. 201, § 9º-A | Contém art. 250, ADCT até art. 138 e encerramento |
| CPP | Interrompido na redação antiga do art. 363 | Contém art. 811 e encerramento |
| CPC | Terminava após introdução do art. 1.071 | Contém art. 1.072 e encerramento |

Isso comprova a recuperação dos trechos finais examinados, não a completude integral de cada documento.

**Particularidade do CPC:** a fonte nova é `l13105.htm`, enquanto a antiga era `l13105compilada.htm`. Portanto, o ganho de redações não deve ser atribuído apenas ao corte anterior: também foi recebida uma apresentação da página com redações riscadas. Para manter a identificação local existente, os bytes de `L13105.html` foram copiados para `HTML/L13105compilada.html`; o nome recebido, a URL efetiva e o hash novo estão registrados, sem atribuir os bytes à página compilada antiga.

As três fontes anteriores e as novas edições foram preservadas em `../source-archives/<SHA-256>/<arquivo>`. Os hashes completos das 13 fontes antes/depois e as URLs das três novas estão em [manifesto](20261021T151338664875Z/manifest.json) e [resultados](20261021T151338664875Z/results.json). Os arquivos enviados pelo usuário não foram alterados. As dez demais fontes permaneceram byte a byte iguais.

## Resultado do processamento das três legislações

| Legislação | Anteriores existentes preservadas | Mesmo texto e notas reencontrados | Novas anteriores `pending` | Blocos riscados ainda excluídos |
| --- | ---: | ---: | ---: | ---: |
| CF | 465 | 465 | 233 | 67 |
| CPP | 204 | 204 | 273 | 209 |
| CPC | 0 | 0 | 67 | 0 |
| **Total** | **669** | **669** | **573** | **276** |

Nenhuma redação anterior existente ficou sem correspondência textual nessa comparação. Não foram encontradas divergências de texto ou de notas nesses 669 registros. Seus IDs, estados, evidências e referências originais foram mantidos, vinculados às edições antigas preservadas. As candidatas atuais arquivadas dos experimentos anteriores também não foram modificadas e continuam fora do painel.

A fixture anterior foi preservada integralmente como prefixo da nova; somente os 573 acréscimos foram anexados. Todos são `pending` e de natureza `previous`. Não foram processadas novamente as outras dez legislações. Os arquivos brutos das três novas fontes e as entradas anteriores estão preservados na pasta da execução; os resultados são reproduzíveis offline.

O painel experimental passou de **1.420 para 1.993 entradas de redações anteriores**, em **639 artigos** no total, incluindo dispositivos do ADCT. Há 1.994 registros anteriores armazenados; uma repetição de caput contida em bloco integral de caput e pena permanece suprimida na apresentação. São trechos documentais, não versões históricas completas de artigos. Não houve mudança de interface nesta tarefa.

## Limitações e correção localizada

- **CPP — obstáculo do extrator:** a fonte contém uma seção antiga seguida de redação com reinício de numeração. A partir do reinício no art. 406, o mecanismo conservador de regressão de numeração mantém candidatos posteriores excluídos. Há 151 blocos com esse motivo, entre os 209 excluídos; os motivos coexistem. O arquivo novo chega ao art. 811, mas o extrator não aproveita integralmente suas redações posteriores. Essa proteção não foi relaxada nesta tarefa.
- **CF — exclusões remanescentes:** blocos sem identificação suficiente, mistura de unidades, ausência de delimitação final e riscados parciais. Cada ocorrência e seu HTML bruto estão nos resultados.
- Foi corrigida uma limitação reproduzida: um marcador de unidade sem risco, como `c)` ou `IX -`, fazia o corpo normativo inteiramente riscado ser confundido com texto misto. O teste de natureza passou a considerar o corpo após o marcador explícito. Isso não aceita palavras normativas apenas parcialmente riscadas; há teste negativo preservado. A alteração foi aplicada somente no reprocessamento das três fontes autorizadas.
- O comando antigo de preparação em lote agora recusa fontes diferentes de sua base registrada antes de escrever resultados. Atualizações devem usar o fluxo controlado para não substituir silenciosamente fixtures antigas.
- CSS externo, marcações não suportadas e documentos eventualmente incompletos continuam limites gerais. Zero exclusões no CPC não prova recuperação de todas as redações juridicamente existentes. Não houve consulta à internet nem investigação de atos modificadores.

## Verificações e reprodução

- **35 testes Python aprovados:** 21 do extrator anterior, quatro de salvaguarda, seis de redações anteriores e quatro novos de atualização/preservação. Os testes resolvem a edição exata da fonte pelo hash, usando o arquivo arquivado quando a fonte ativa foi substituída; não comparam evidência antiga com bytes novos.
- **72 testes Node aprovados**, incluindo isolamento dos registros experimentais no build normal.
- **Navegador aprovado:** demonstração em 320/390/1280 px; prévia real em 390/1280 px, incluindo novos casos do CPC, CPP além do corte antigo e ADCT, texto integral, fontes, foco, fechamento e posição de leitura.
- **Reprodução offline das três fontes e hashes da execução aprovada**, sem modificar fontes ou fixtures durante a verificação.
- `git diff --check` limpo; ausência de diferenças rastreadas em `data/`, `sources/` e `monitor/official/`.

Ocorrências durante a verificação: a primeira execução dos testes novos encontrou restrição de acesso à pasta temporária do ambiente; os testes passaram após usar temporários dentro de `test-results/`. Uma primeira importação do teste de proteção do comando antigo falhou enquanto a função ainda não estava aplicada; foi corrigida e a execução final passou. Nenhuma falha foi ocultada ou teste desativado.

```powershell
python scripts/refresh_previous_html_sources.py --verify experiments/html-history/source-refresh/20261021T151338664875Z
python -m unittest discover -s tests/python -p test_refresh_previous_html_sources.py
```

**Conclusão:** as três fontes são adequadas para continuar a preparação experimental, com aumento efetivo de cobertura e preservação dos registros anteriores. O CPP ainda exige correção localizada do reconhecimento de regiões com numeração reiniciada antes de afirmar aproveitamento integral. As demais exclusões permanecem documentadas. Não houve retomada do coletor, reconstrução histórica, alteração de homologação, commit, push, merge ou publicação. Homologação jurídica humana e autorização de publicação continuam independentes.


## Validação dirigida de numeração — 21/10/2026

Execução preservada: `20261021T175224964205Z`; somente CP, CPP, CLT e Licitações reprocessados. As 13 fontes foram inspecionadas, sem mudança em seus bytes.

| Fonte | Anteriores existentes preservadas | Novas | Exclusões antes → depois |
| --- | ---: | ---: | ---: |
| CP | 435 | 426 | 776 → 346 |
| CPP | 477 | 139 | 209 → 70 |
| CLT | 0 | 1 | 6 → 5 |
| Licitações | 6 | 2 | 26 → 24 |

Causas: CP reinicia a Parte Geral em 1 após 120; CPP reinicia seção do júri em 406 após 497. Exige-se cabeçalho e âncora nativos, além de artigo previamente observado. CLT contém decreto de aprovação separado; Licitações cita artigos de outra lei em blockquote. CF separa ADCT; Civil, CPC, CTN, LEP, ECA, CDC, Improbidade e Maria da Penha não apresentaram regressões imediatas na numeração. Nenhum candidato permaneceu bloqueado por numeração na inspeção final; isso não demonstra cobertura textual integral.

Os 2.373 registros anteriores à tarefa foram preservados integralmente. Nenhum registro antes reconhecido perdeu reconhecimento; dois antigos do CP já não eram reconhecidos pelas regras anteriores (332-caput-01 e 234-A-batch-pdf-p57-b18), permanecendo intactos. Todos os 568 acréscimos são previous/pending. Total armazenado: 2.941; 2.562 anteriores, 379 candidatas atuais arquivadas; painel: 2.561 entradas em 806 artigos.

A comparação sinalizou 19 diferenças de notas no CP, sem alteração nos registros: 16 já existiam antes da correção (quebras de linha ou notas editoriais do piloto); três, nos arts. 116 e 117, decorrem da seleção da primeira ocorrência de texto idêntico na Parte Geral original, sem a nota da ocorrência posterior. As evidências antigas e novas fontes foram preservadas. Não são mudanças de texto normativo nem autorização para remover notas existentes.

Verificações desta tarefa: 43 testes Python direcionados aprovados (25+12+6), 72 testes Node aprovados; navegador aprovado em 390/1280 px com exemplos recuperados e demonstração também em 320 px; reproduções offline da execução anterior e desta execução aprovadas, incluindo hashes. A seleção ampla inicial encontrou erro de importação de fitz em teste PDF fora do escopo; o conjunto HTML direcionado não depende desse módulo. Nenhum teste PDF foi apresentado como aprovado.

Persistem exclusões por risco parcial, unidade/associação incerta, contêiner citado ou ausência de correspondência segura no leitor. CSS externo não é interpretado. Conferência técnica assistida por IA não é homologação jurídica humana; não foi medida conferência humana independente dos 568 acréscimos. Recomenda-se revisão dirigida dos reinícios, exemplos recuperados e notas antes de homologação/publicação. Sem novo commit, push ou publicação nesta tarefa.


## Correção bloqueante de associação — revisão incremental

A seção anterior registra o resultado então produzido, não o estado atual de aceitação. A revisão identificou que os 426 registros da Parte Geral antiga do CP haviam sido associados à organização posterior apenas por numeração. Cabeçalho/âncora comprovavam reinício documental, mas não continuidade normativa. A preparação atual volta a separar essa região e não tenta determinar equivalências.

Dos 426: zero mantidos na prévia e 426 inconclusivos em quarentena documental, sem alterar texto, evidências ou estado pending. Nenhum é declarado juridicamente válido por esta correção. Os arts. 4º e 5º estão abrangidos pela exclusão integral. Os 2.373 anteriores à execução permanecem integralmente preservados. A execução de 568 continua arquivada e reproduzível no modo histórico; não sobrescrevemos manifestos nem resultados anteriores.

Mantidos 139 CPP, um CLT e dois Licitações, nas mesmas ocorrências (ID, texto, notas, fonte e evidência integralmente iguais). O CPP mantém seu contexto nativo posterior ao reinício, a CLT separa seu decreto de aprovação e Licitações não toma artigos citados por próprios. Isso é verificação documental dirigida, não homologação ou prova de completude histórica.

Das 19 diferenças editoriais, 16 preexistentes permanecem (13 notas explicativas do piloto e três diferenças de quebra de linha); as três dos arts. 116/117 deixam de ocorrer com a seleção da região documental correta. Não houve transferência nem alteração de notas armazenadas.

Estado atual: 2.515 registros armazenados, 2.136 anteriores e 379 candidatas atuais arquivadas; prévia com 2.135 entradas em 707 artigos; fixture previous-wordings-html com 1.698. Quarentena e decisões individuais em association-review/20261021/results.json, com snapshot anterior e manifesto próprios. O script revalidate_previous_associations.py --verify reproduz a avaliação sem alterar registros.

Testes desta correção: 46 Python (25 núcleo, 13 preparação, seis atualização, dois de revisão dirigida), 72 Node, reprodução offline histórica e dirigida. O navegador inclui ausência dos trechos em quarentena nos arts. 4º/5º, além dos casos CPP/CLT/Licitações. Resultados finais e logs acompanham o pacote incremental. Não foi executada homologação jurídica humana. Nenhum commit, push ou publicação autorizado nesta tarefa.
