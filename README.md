# Lexa

Biblioteca de legislação federal brasileira com leitura dentro do site. Inclui Código Civil, Código Penal, CPC, CDC, CTN e Constituição Federal com ADCT.

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

O monitor consulta as fontes, `scripts/import_official.py` prepara as seis edições para o leitor e o workflow gera os testes e a prévia antes de propor a atualização. A primeira conversão e as alterações posteriores entram somente após revisão e merge. A implantação pública depende da hospedagem e não é executada por esse workflow. Veja [ativação, revisão e limites](monitor/README.md).
