# Redações anteriores — fluxo experimental consolidado

## Escopo aprovado

Exibir somente redações anteriores documentadas nos arquivos locais, associadas ao artigo correto. A redação atual permanece na consulta normal e não é repetida no painel. Não exigir substituta, datas, períodos de vigência, referência modificadora ou reconstrução do artigo. Não consultar a internet para preencher lacunas. O Histórico de versões é independente.

Todos os novos registros ficam `pending`. Os três estados `approved` herdados do piloto local são preservados, sem afirmar homologação jurídica independente. Publicação exige homologação humana aplicável e autorização expressa. PDFs, Câmara e reconstrução legislativa estão suspensos; os dados anteriores reaproveitados não autorizam reativar essas ferramentas.

## Fluxo ativo e classificação

| Grupo | Componentes | Tratamento |
| --- | --- | --- |
| Núcleo ativo | `scripts/extract_previous_html.py` (leitura e reconhecimento compartilhados) e `scripts/prepare_previous_only.py` (`previous_blocks`) | Manter; não executar o preparador antigo para substituir a fixture consolidada |
| Atualização controlada | `scripts/refresh_previous_html_sources.py`, `scripts/saved_html_source.py` | Atualização aditiva de CF/CPP/CPC e resolução da edição exata pelo hash |
| Salvaguarda | `scripts/audit_previous_html.py` | Manter ferramenta e fotografia anterior; não confundir seu inventário com a cobertura atual |
| Dependências já existentes | `scripts/check_official_sources.py`, `scripts/import_official.py`, `scripts/official_http.py` | Apenas funções compartilhadas, sem executar monitoramento ou rede |
| Aplicação | Módulos `src/legislative-history*.js`, integração em `src/reader.js`, estilos e build/prévia | Somente anteriores na apresentação; produção vazia |
| Testes e fixtures | Quatro suítes Python HTML, teste Node e navegador; quatro fixtures reais de `tests/fixtures/` | Necessários à reprodução e ao isolamento |
| Fontes e evidências | Treze HTMLs, arquivos de execução/manifestos, edições antigas necessárias por hash | Preservar integralmente, sem reprocessamento nesta consolidação |
| Implementações anteriores | CLI `prepare_document` do núcleo, materiais PDFs/Câmara e relatórios superados | Preservar; sem reativação. O CLI antigo permanece porque compartilha núcleo e tem testes de evidência; os materiais independentes ficam fora do commit proposto |

A documentação operacional é este arquivo. `HISTORICO-LEGISLATIVO.md` é uma referência de compatibilidade, e `EXTRATOR-REDACOES-HTML.md` descreve o núcleo e a diferença entre preparadores. As descrições antigas que exigiam substituta não se aplicam ao fluxo atual.

## Dados preservados e apresentação

As camadas são: 96 registros de referência em `experiments/html-history/existing-records.json`, 721 em `tests/fixtures/legislative-history-html.json` e 1.556 em `tests/fixtures/previous-wordings-html.json`. O piloto e o lote em fixtures compõem os mesmos 96 registros; não somá-los novamente.

Total armazenado: 2.373 registros, dos quais 1.994 são `previous` e 379 são candidatas atuais arquivadas. O painel filtra somente anteriores e apresenta 1.993 entradas em 639 artigos, incluindo ADCT. Uma repetição de caput contida em trecho integral de caput e pena é suprimida na apresentação. São trechos documentais, não versões históricas completas.

São preservados texto integral identificado, notas, referências disponíveis, links dos runs, fonte/hash e localização. Caput e pena no mesmo bloco permanecem explicitamente identificados como trecho conjunto. Não são combinados blocos para reconstruir artigos. Os dois caputs antigos do art. 216 não recebem o texto de superior hierárquico do art. 216-A.

`previousRecords()` seleciona a natureza anterior. `readingArticle()` separa apenas parágrafos integralmente riscados com correspondência textual e unidade inequívocas; não exige substituta. Incompletude, risco parcial e associação insegura permanecem preservados para conferência.

## Reprodução sem ampliar cobertura

Requisitos: Python 3.12+ (biblioteca padrão) e Node 22+. Navegador requer Playwright e Chromium; localmente existe `.venv`. As quatro suítes HTML não exigem PyMuPDF.

```powershell
python -m unittest discover -s tests/python -p 'test_*previous_html.py'
python -m unittest discover -s tests/python -p test_prepare_previous_only.py
python -m unittest discover -s tests/python -p test_refresh_previous_html_sources.py
npm test
.venv\Scripts\python.exe tests/browser/legislative_history.py
python scripts/refresh_previous_html_sources.py --verify experiments/html-history/source-refresh/20261021T151338664875Z
```

Os três comandos Python de teste correspondem a 25 + 6 + 4 testes na base consolidada. Não usar seleção ampla de testes anteriores de PDFs/Câmara para validar este escopo. `--verify` reproduz a execução existente sem substituir fontes ou fixtures. Não executar os comandos de preparação/atualização com escrita durante a consolidação.

```powershell
$env:PORT='3012'
npm run preview:legislative-history -- --pilot
```

Esse último comando gera somente a prévia ignorada em `test-results/legislative-history-demo/`. O build normal mantém `src/legislative-history-data.js` vazio, não lê fixtures e não incorpora registros `pending`. A prévia desativa o registro de PWA e não pode substituir `dist/`. Fechamento, teclado e retorno à posição de leitura são cobertos pelo teste de navegador.

## Fontes, hashes e preservação

A atualização de CF/CPP/CPC e suas limitações estão em `experiments/html-history/source-refresh/RELATORIO.md`. Ela acrescentou 573 anteriores, reencontrou as 669 anteriores existentes dessas fontes com mesmo texto e notas e preservou as outras dez fontes. As edições antigas são resolvidas por `saved_html_source.py`; nunca comparar evidências antigas com bytes de edição nova.

O CPC recebido como `L13105.html` mantém o nome ativo local `L13105compilada.html`, com URL e nome recebido registrados. São apresentações diferentes da página do Planalto, além da correção de corte.

`.gitattributes` desativa conversão de quebras de linha para fontes, evidências, fixtures e o núcleo cujo hash está fixado no manifesto. Não renormalizar esses arquivos. O commit proposto inclui arquivos volumosos somente quando necessários às fontes, manifestos e testes; ambientes, builds, caches e screenshots permanecem fora.

Os HTMLs possuem pastas auxiliares de recursos, preservadas localmente, mas não lidas pelo extrator. Cópias novas em `source-archives/` que duplicam exatamente as fontes ativas e os arquivos `incoming/` podem ficar fora do commit; as três edições antigas requeridas pelos testes devem ser incluídas. Relatórios anteriores e experimentos suspensos também ficam preservados fora do commit. A seleção exata deve ser revisada antes de autorizar o commit; não usar `git add .`.

## Pendências, sem correções nesta consolidação

- CPP: a numeração volta de 497 a 406 em seção legítima. A proteção atual exclui candidatos posteriores; a inspeção dirigida das 13 fontes e a correção pertencem à próxima etapa.
- CSS externo não é interpretado; unidades parciais ou mal delimitadas continuam excluídas. A parte geral antiga do CP não é automaticamente remapeada.
- O inventário de 2.416 blocos é uma fotografia anterior à atualização das três fontes, não uma contagem atual de cobertura.
- Referências e links são preservados nas evidências, mas os novos registros não preenchem automaticamente `reference` a partir das notas.
- Não há comprovação de completude jurídica nem homologação independente do conjunto. Os pacotes antigos de revisão não representam o conteúdo consolidado atual.

A consolidação não muda conteúdo jurídico, revisão, cobertura ou reconhecimento de artigos. O commit depende de autorização expressa; push, merge, publicação e remoção de branches não estão autorizados.
