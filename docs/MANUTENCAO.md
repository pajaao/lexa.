# Manutenção do Lexa

Biblioteca de legislação federal brasileira com leitura dentro do site. Inclui Código Civil, Código Penal, CPC, CDC, CTN e Constituição Federal com ADCT.

Os comandos abaixo devem ser executados na raiz do repositório. Para uma apresentação do site, veja o [README principal](../README.md).

## Executar e validar

Use Node.js 22 ou superior, sem dependências npm:

```sh
npm start
npm test
```

O servidor usa a porta 3000 (`PORT` permite substituí-la). `npm run build` gera `index.html` com CSS, dados e JavaScript incorporados, para que a leitura funcione também na prévia isolada do arquivo, sem requisições externas. Os PDFs de origem estão disponíveis quando o site é servido completo; não são incorporados ao HTML.

Edite o HTML-base em `scripts/index.template.html`, os estilos em `style.css`, o catálogo e a busca em `data.js` e o comportamento em `app.js`. `npm start` e `npm run dev` também geram o HTML antes de iniciar. O código usa fontes locais.

## Conteúdo e proveniência

Os seis PDFs fornecidos pelo usuário estão preservados em `sources/`. `sources/manifest.json` registra o nome original, número de páginas, data de importação e SHA-256 de cada documento. `content.js` preserva a extração dos PDFs. `official-content.js` recebe as edições extraídas das fontes oficiais, depois de geradas e mescladas por proposta revisada; quando existe uma edição oficial para uma legislação, o leitor a utiliza. `sources/official-manifest.json`, quando gerado, registra a procedência dessas edições. `sources/import-report.json` registra a cobertura e possíveis linhas sem atribuição; a importação falha quando há números-base ausentes ou linhas não atribuídas.

Os PDFs de referência dos cinco códigos foram impressos do Planalto em 15/10/2026. O PDF da Constituição é a 69ª edição da Câmara (2026), até a EC 138/2025. Essas referências continuam arquivadas. Nas edições HTML incorporadas por revisão, o leitor informa a página oficial, a data de coleta e o hash do texto extraído. **Nenhuma dessas datas certifica a redação vigente ou o início dos efeitos de uma alteração.** Constituição e ADCT permanecem separados; o importador não mistura as emendas ou os tratados anexos aos artigos constitucionais.

A extração preserva parágrafos, incisos, alíneas, notas de alterações e redações riscadas. Artigos com letras têm identificadores próprios, inclusive sufixos como `359-M-A`. Revogações agrupadas são mantidas como no documento: buscar o art. 55 do CTN abre a referência aos arts. 52 a 58, sem inventar uma redação para cada dispositivo revogado.

Nas edições PDF, o leitor informa o arquivo e a página inicial; nas edições oficiais HTML, informa fonte e data da coleta, com referências internas ao bloco original para rastreabilidade. Houve validação automatizada e conferência de casos representativos; **não houve revisão jurídica integral nem comparação com alterações posteriores aos PDFs**. A presença de notas de vigência no arquivo não significa que o sistema tenha calculado automaticamente seus efeitos.

## Navegação

- Busca por expressão, sem distinção de acentos, ou número (`186`, `Art. 1.022`, `54-A`).
- Links diretos: `#/civil/186`, `#/cpc/1022`, `#/cf/5`, `#/cf/adct-1`.
- Índice de capítulos, leitura em grupos de 15 entradas e navegação anterior/próxima.
- Constituição e ADCT com buscas separadas. `ADCT 1` também busca diretamente no ADCT.
- Destaque de resultados, tamanho da fonte e tema escuro.
- Favoritos armazenados somente no navegador atual, acessíveis pelo filtro “Meus favoritos”.
- Página “Atualizações” (`#/atualizacoes`), com registros por legislação, filtros por artigo e comparação lado a lado. O verde destaca diferenças na versão coletada; o rosa, na anterior. Riscados já existentes na fonte continuam riscados.

O histórico persistente é gerado em `updates.js` junto com cada proposta de textos oficiais. O primeiro registro estabelece uma referência inicial, sem tratar a conversão de PDFs para HTML como mudança legislativa. As versões seguintes guardam os textos anterior e novo dos artigos modificados. Mudanças apenas de espaços ou quebras de parágrafo não contam como alteração de artigo. Ausência de artigo, adição de texto e alteração de redação são descrições da comparação, não decisões sobre revogação ou vigência. A página não usa dados fictícios para preencher o histórico inicial.

## Reimportação e manutenção

A rotina diária prepara propostas com os textos do leitor, testes e prévia; não faz merge nem implantação automática. Consulte `monitor/README.md`. O procedimento abaixo continua disponível para reconstruir a base PDF arquivada; ele não substitui edições HTML já incorporadas em `official-content.js`:

1. Obtenha nova edição consolidada em fonte oficial. Confirme sua data de referência e guarde a versão anterior em histórico de Git ou armazenamento versionado antes da substituição.
2. Compare os arquivos e as alterações de redação. A Constituição desta importação tem limites de páginas específicos (texto constitucional nas páginas PDF 8–142 e ADCT nas páginas 143–193). Antes de importar outra edição, revise esses limites, o ano, a referência às emendas e os números finais em `scripts/import_pdfs.py`. Não reutilize os metadados antigos em outra edição.
3. Substitua os PDFs correspondentes em `sources/` e atualize os metadados do importador. Os nomes internos são `civil.pdf`, `penal.pdf`, `cpc.pdf`, `cdc.pdf`, `ctn.pdf`, `cf.pdf`.
4. Em ambiente Python com PyMuPDF, execute:

```sh
python3 -m venv /tmp/lexa-import-venv
/tmp/lexa-import-venv/bin/pip install -r scripts/requirements-import.txt
/tmp/lexa-import-venv/bin/python scripts/import_pdfs.py
npm test
npm run build
```

5. Revise o relatório, o diff dos textos, as redações riscadas, as regras de vigência e a interface antes de publicar. Falhas de validação bloqueiam a importação; não remova essas verificações apenas para aceitar uma nova edição.

O monitor consulta as fontes, `scripts/import_official.py` prepara as seis edições para o leitor e o workflow gera os testes e a prévia antes de propor a atualização. A primeira conversão e as alterações posteriores entram somente após revisão e merge. A implantação pública depende da hospedagem e não é executada por esse workflow. Veja [ativação, revisão e limites](../monitor/README.md).

### Súmulas vinculantes do STF

A biblioteca inclui uma coleção própria em `#/sv`, com links como `#/sv/13`, busca por `SV 13`, `Súmula Vinculante 13` ou expressão, favoritos e navegação por intervalos. O enunciado aparece primeiro; precedentes, jurisprudência e observações ficam em uma seção expansível. A busca também alcança esse material de aplicação.

A fonte desta importação é **somente** `sources/Sumulas_Vinculantes_STF_Completo.pdf`, com 236 páginas e 63 entradas numeradas de 1 a 63. O PDF declara consulta em 16/10/2026; isso não equivale a uma conferência ao vivo pelo importador. A SV 9 permanece identificada como cancelada e a SV 30 como pendente de publicação, conforme o documento. O arquivo `revsum.pdf` foi descartado e não integra esta base.

`python3 scripts/import_sumulas.py` reconstrói `sumulas-content.js` usando PyMuPDF (mesma dependência de `scripts/requirements-import.txt`). O processo valida o SHA-256 registrado em `sources/sumulas-manifest.json`, a numeração, os cabeçalhos e os links individuais do STF. Uma nova edição exige revisão do manifesto e das regras de extração; não substitua a fonte apenas para iniciar o site.

A consulta automática das súmulas está **pausada** por decisão do mantenedor, após falhas de acesso ao STF. O arquivo de workflow mantém somente a execução manual para diagnóstico futuro. Não há agenda nem execução por push para as súmulas. A coleção permanece baseada no PDF fornecido e deve ser revista ao receber nova edição. A rotina automática das seis legislações do Planalto continua independente.

## Publicar no GitHub Pages

O repositório público inclui o workflow **Publicar Lexa no GitHub Pages**, que testa e publica cada mudança incorporada na `main`. Pull requests em rascunho dos monitores não são publicados até serem revisados e mesclados.

1. Em **Settings → Pages → Build and deployment → Source**, escolha **GitHub Actions**.
2. Em **Actions → Publicar Lexa no GitHub Pages**, execute **Run workflow** na `main` se não houver uma execução em andamento após a ativação.
3. A etapa de publicação informa o endereço real do site; para o nome atual do repositório, o endereço esperado é `https://pajaao.github.io/lexa./`.

`npm run build:pages` gera `_site/` com o HTML autocontido, `.nojekyll` e os sete PDFs arquivados. Somente esse pacote é enviado ao Pages; scripts de manutenção, capturas brutas, relatórios e arquivos Git não fazem parte da publicação. O pacote é gerado novamente a cada execução e não é versionado. Nenhum token pessoal é necessário: o workflow usa as permissões oficiais do GitHub Pages.

As rotas usam fragmentos, como `/lexa./#/civil/186` e `/lexa./#/sv/13`, e os PDFs usam caminhos relativos, funcionando tanto em uma subpasta do projeto quanto em um domínio próprio. Favoritos continuam locais ao navegador. A interface informa a fonte e a edição de cada base e traz um aviso de consulta no rodapé. A publicação não executa coletas de fontes na rede: falhas do Planalto ou do STF não impedem publicar uma versão já revisada e testada.
