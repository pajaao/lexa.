# Redações anteriores — candidata de lançamento

Situação: integração técnica preparada; publicação bloqueada. Branch `codex/historico-triagem-fontes`, base `d93120f15d0e94ed3e5340831bf5851a79c9a676`. Sem novo commit, push, merge ou publicação.

## Seleção final

| Legislação | Registros |
| --- | ---: |
| Constituição e ADCT | 666 |
| Código Penal | 270 |
| CPP | 366 |
| CLT | 1 |
| Código Civil | 0 |
| CPC | 65 |
| Licitações | 7 |
| CTN | 1 |
| LEP | 76 |
| ECA | 150 |
| CDC | 0 |
| Improbidade | 67 |
| Maria da Penha | 10 |
| **Total** | **1.679** |

São 560 dispositivos. Partimos dos 1.903 associados; 224 registros do CPP, em 88 artigos, foram excluídos conservadoramente da candidata. Os 593 não associados e os 692 blocos sem unidade completa não foram recuperados nem incorporados. Zero no Civil/CDC é resultado válido.

## Validação e revisão

`scripts/prepare_previous_release.py --verify` reproduz as 13 fontes e confere integralmente os 1.903 registros associados: texto, notas, referência, unidade, fonte/hash, localização, contexto e evidência de associação. Também compara integralmente os campos da candidata com os registros de origem, sem modificar estados. A comparação textual existente usa apenas normalização documentada de espaços; originais preservados.

A revisão independente por IA examinou 49 registros das 11 legislações com resultados, com seleção determinística e casos de maior risco. Um parser HTML separado e conferência direta de intervalos/hashes não encontraram divergências textuais ou de notas na amostra. Identificou, porém, associação circular no CPP antigo: o art. 439 sobre alistamento de jurados era tratado como redação do art. 439 posterior sobre exercício/idoneidade. Igualdade com o texto já agrupado no leitor não demonstrava continuidade normativa.

Excluímos o intervalo documental inteiro `[1559,1812)` de Del3689.html (antiga organização do júri entre as duas ocorrências do art. 406). Nenhuma equivalência foi reconstruída. Os 224 registros e suas evidências permanecem na execução experimental; 16 estavam na amostra. As outras 33 amostras permanecem na candidata. Lista e método: `experiments/previous-wordings-release/20261021/independent-sample.json`. Nenhuma conferência ou homologação jurídica humana foi realizada nesta tarefa.

Não foi localizado um protocolo anterior de validação por risco formalizado nos documentos consultados. O método executado está registrado para ratificação, sem alegar que substitui homologação humana. Reorganizações sem reinício numérico e problemas fora da amostra continuam como riscos residuais.

## Integração e autorização

- `data/previous-wordings/candidate.json`: somente os 1.679 selecionados, todos ainda `pending`; textos, notas e referências preservados. Evidências extensas ficam na execução original; a distribuição mantém fonte/hash/localização, links e identificação de auditoria.
- `data/previous-wordings/release.json`: IDs, quantidades, hashes dos dados/leitor/validação e campos separados de autorização.
- `scripts/previous-wordings-release.mjs`: build verifica integridade e seleção; nenhum `pending` vira homologado. `publicationAuthorized: false` mantém o build normal sem registros. A candidata utiliza a mesma aplicação e a PWA normal, sem desativá-la.
- A autorização efetiva exige decisões expressas registradas em `governanceDecision`, `riskReviewDecision` e `publicationDecision`, além de `publicationAuthorized: true`. Não preencher esses campos por resultado automatizado ou por inspeção de IA. A condição foi registrada no Processo de Trabalho, sem aprovar dispensa de homologação.

O leitor mantém a interface aprovada: caputs diretamente, demais unidades recolhidas, ou todas diretamente quando não há caput. Os arquivos legislativos do build são idênticos aos do build normal; parágrafos sem risco não são removidos. A separação visual de redações antigas continua limitada aos parágrafos integralmente riscados que correspondam inequivocamente a registros selecionados; nenhum texto atual é reescrito.

Reversão: registrar `publicationAuthorized: false`, gerar novamente o build e submeter a reversão à autorização de publicação. Isso desabilita os controles sem apagar fontes, registros, evidências ou estados de revisão. A PWA mantém seu mecanismo de atualização consentida.

## Testes e desempenho observados

- 10 testes Python da extração/apresentação, reprodução documental integral e validação de seleção aprovados.
- 81 testes Node aprovados, incluindo hashes, autorização separada de homologação, exclusões, preservação do leitor, build/PWA e regressões. A primeira execução detectou um contrato antigo sobre o módulo gerado; o contrato foi ajustado para conferir o manifesto e os testes repetidos, com os logs anteriores preservados.
- Navegador da candidata: desktop/celular, cinco cenários da interface, teclado, fechamento, expansão/recolhimento e posição de leitura aprovados. Regressões de busca global e navegação aprovadas.
- PWA real aprovada: subpasta, biblioteca offline, atualização consentida, favoritos/preferências e rejeição de recursos adulterados. Painel de redações anteriores também conferido após recarga offline.
- Cinco medições locais de build: mediana normal 129,27 ms; candidata 133,98 ms. Módulo de registros: 1.869.399 bytes, ou 193.625 bytes em gzip; o servidor local não aplica gzip.
- Cinco contextos Chromium novos, viewport 390 px, localhost e sem limitação de rede/CPU: mediana até o controle visível 314,51 ms; abertura do painel 77,25 ms. São observações locais, não estimativas de aparelho ou conexão móvel real.

Foram conferidos 127 arquivos protegidos sem alteração, incluindo os 13 HTMLs, as duas ferramentas simples e dados/evidências anteriores; os outros 99 arquivos também foram preservados. Manifesto de auditoria e logs em `experiments/previous-wordings-release/20261021/`.

## Execução local e pendências

```powershell
python -B scripts/prepare_previous_release.py --verify
npm test
node scripts/preview-previous-release.mjs
```

Candidata local: `http://127.0.0.1:3013/#/penal/215`. Para os testes de navegador existentes, `LEXA_TEST_SITE` pode apontar para `test-results/previous-wordings-release/site`. A candidata é impedida de substituir `dist/`; o build público continua bloqueado por manifesto.

Pendências de decisão: formalizar a aceitação do regime de validação por risco em substituição à homologação individual, definir/registrar a conferência humana exigida nesse regime e autorizar expressamente o lançamento. A candidata técnica está disponível para essa decisão; não está declarada juridicamente homologada nem autorizada para publicação.

### Integração do PR e portabilidade

O PR integra código, testes e candidata com publicação bloqueada. O merge na main aciona o pipeline normal de Pages, mas `publicationAuthorized: false` impede a disponibilização dos registros. A autorização de merge não é tratada como autorização de homologação ou de ativação do lote. Os hashes dos HTMLs/dados/evidências são byte a byte; hashes de código e da representação JS do leitor usam UTF-8 com quebras LF, explicitamente, para reprodução em Windows/Linux sem alterar os arquivos jurídicos. As rotinas novas também integram a suíte essencial de CI.
