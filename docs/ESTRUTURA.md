# Estrutura do projeto

O Lexa é um site estático: o navegador recebe a interface e a base de leitura, sem servidor de aplicação ou cadastro. Execute os comandos na raiz do repositório.

## Onde encontrar cada parte

| Caminho | Responsabilidade | Como manter |
| --- | --- | --- |
| `src/index.html` | Estrutura da página | Editar a interface aqui |
| `src/styles.css` | Aparência e responsividade | Editar estilos aqui |
| `src/app.js` | Rotas e coordenação dos fluxos | Editar comportamentos aqui |
| `src/reader.js` e `src/reader-model.js` | Leitor, seleção e modelos reutilizados | Preservar paginação, IDs e hierarquia |
| `src/search-index.js` e `src/library-search.js` | Índice compacto e busca global | Índices são derivados fielmente no build |
| `src/collection-cache.js` | Conjunto limitado de leitores completos | Protege o leitor ativo |
| `src/presentation.js` e `src/clipboard.js` | Apresentação e cópia | Funções separadas do roteamento |
| `src/catalog.js` | Metadados das legislações | Editar o catálogo aqui |
| `src/data.js` | Referências e busca por artigo | Editar a lógica aqui |
| `src/collections.js` | Escolha das edições para ferramentas e testes Node | Usa bases geradas; não integra o shell do navegador |
| `src/collection-model.js` | Preparação de uma norma e índice textual sob demanda | Preservar os textos e construir a busca apenas quando usada |
| `src/loading.js` | Carregamento assíncrono, integridade e repetição de tentativas | Editar a lógica aqui |
| `src/history.js` | Comparação e filtros do histórico | Editar a lógica aqui |
| `public/` | Ícones e manifesto da PWA | Atualizar os recursos de instalação aqui |
| `src/pwa.js` e `src/sw.js` | Instalação, leitura offline e atualização da PWA | Editar o worker de origem; sua versão é gerada no build |
| `data/archive/` | Dados derivados dos PDFs de referência | Preservar para comparação e testes; não são cópias redundantes da edição oficial |
| `data/official/` | Dados derivados oficiais usados pelo leitor | Gerados pelos conversores e incorporados após revisão |
| `data/history/` | Versões e diferenças registradas | Geradas junto com as propostas de atualização |
| `sources/` | PDFs e manifestos de procedência | Preservar os originais e seus hashes |
| `monitor/official/` | Capturas estruturadas primárias do monitor | Texto, blocos e hashes usados na conversão; não equivalem aos HTMLs locais |
| `monitor/stf/` | Configuração e referências do STF | Coleta automática pausada |
| `HTML/` | 13 documentos primários salvos do Planalto para Redações anteriores | Preservar bytes, nomes, codificação e proveniência |
| `data/previous-wordings/` | Distribuição derivada e manifesto de autorização | Não editar textos ou promover estados manualmente |
| `tests/fixtures/` | Dados de demonstração e corpora de regressão | Nem toda fixture integra o build; o lote público é controlado pelo manifesto |
| `experiments/` | Evidências e snapshots ainda usados em reprodução/testes | Preservar dependências; execuções substituídas estão inventariadas em `PRESERVACAO.json` |
| `scripts/` | Build, servidor, importação e coleta | Ferramentas de manutenção |
| `tests/node/` | Testes da aplicação e publicação | Executados com `npm test` |
| `tests/browser/` | Fluxos reais e benchmark Chromium | Executar com `scripts/run_browser_tests.py`; ver [baseline](BASELINE-DESEMPENHO.md) |
| `tests/python/` | Testes dos importadores e monitores | Executados com `npm run test:python` |
| `.github/workflows/` | Publicação e verificações no Actions | Alterar com atenção aos gatilhos e permissões |

## Executar e publicar

- `npm start`: gera o pacote e serve `dist/` na porta 3000. Rode novamente após editar os arquivos; não há recarga automática.
- `npm run build`: recria `dist/`, incluindo shell HTML, catálogo, JSONs por norma, ícones e PDFs. Requer Node.js 22 ou superior, sem dependências npm.
- `npm test`: gera o pacote e executa os testes JavaScript.
- `npm run test:python`: executa os testes Python sem consultar as fontes na rede. Use Python 3.12 ou superior.

`dist/` é descartável e fica fora do Git. O arquivo `dist/index.html` incorpora estilos e referencia módulos ESM nativos em `dist/app/<sha256>/`. O catálogo leve integra um adaptador; imports/exports não são removidos por expressões regulares. Os textos ficam em `dist/data/<id>.<sha256>.json`; os índices compactos de busca e o histórico também são JSONs com hash. `dist/catalog.json` descreve a edição e os arquivos. Sirva a pasta inteira por HTTP (`npm start`), inclusive para conferir uma prévia; o HTML isolado não contém os textos. Edite os arquivos de origem em `src/`, e gere o pacote novamente. A publicação inclui somente os arquivos permitidos pelo gerador, sem expor o checkout inteiro.

Ao incorporar mudanças à `main`, o workflow `deploy-pages.yml` testa o projeto e publica `dist/` no GitHub Pages. Os caminhos públicos, os favoritos do navegador e os links para artigos permanecem os mesmos.

## Atualização dos textos

O monitor do Planalto prepara os dados oficiais, o histórico e uma proposta em rascunho. A prévia gerada, com a pasta `dist/` inteira, fica como artefato do Actions, sem versionar o HTML compilado. Após revisão e merge, o workflow de publicação atualiza o site.

As súmulas continuam com atualização manual; a rotina de coleta do STF permanece disponível somente para diagnóstico manual. Esta organização não reativa a coleta.

Consulte [Manutenção](MANUTENCAO.md), o [monitor das legislações](../monitor/README.md) e o [monitor do STF](../monitor/stf/README.md) para procedimentos e limites das fontes. Não edite diretamente os dados gerados para corrigir o processamento: ajuste o importador e confira a saída e a procedência.

## Redações anteriores e preservação

O fluxo corrente e seus comandos estão em [REDACOES-ANTERIORES-SIMPLES.md](REDACOES-ANTERIORES-SIMPLES.md). `experiments/html-history/existing-records.json` é a base de 96 registros usada pelos testes dos fluxos anteriores; não é um log descartável. O snapshot `experiments/previous-wordings-simple/20261021-associations-corrected/` contém extração, apresentação e leitor de referência do lote corrente. `experiments/previous-wordings-release/20261021-associations/validation.json` é dependência do controle de integridade do build.

As cópias locais retiradas do índice estão em [experiments/PRESERVACAO.json](../experiments/PRESERVACAO.json), com SHA-256, ZIP externo e commit-base. Elas continuam no histórico Git; o saneamento reduz o checkout futuro, não o histórico já armazenado. Não apagar evidências nem sobrescrever fontes para economizar espaço.

## Licenciamento

[LICENSE](../LICENSE) contém uma minuta proprietária, pendente de revisão jurídica e confirmação da titularidade. Não constitui aprovação definitiva nem muda os direitos sobre textos oficiais ou materiais de terceiros.
