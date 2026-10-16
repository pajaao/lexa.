# Estrutura do projeto

O Lexa é um site estático: o navegador recebe a interface e a base de leitura, sem servidor de aplicação ou cadastro. Execute os comandos na raiz do repositório.

## Onde encontrar cada parte

| Caminho | Responsabilidade | Como manter |
| --- | --- | --- |
| `src/index.html` | Estrutura da página | Editar a interface aqui |
| `src/styles.css` | Aparência e responsividade | Editar estilos aqui |
| `src/app.js` | Navegação e controles de leitura | Editar comportamentos aqui |
| `src/data.js` | Catálogo, busca e escolha das edições | Editar a lógica aqui |
| `src/history.js` | Comparação e filtros do histórico | Editar a lógica aqui |
| `public/` | Ícones e manifesto da PWA | Atualizar os recursos de instalação aqui |
| `src/pwa.js` e `src/sw.js` | Instalação, leitura offline e atualização da PWA | Editar o worker de origem; sua versão é gerada no build |
| `data/archive/` | Extrações dos PDFs de referência | Geradas pelos importadores de PDFs |
| `data/official/` | Edições de fontes oficiais | Geradas pelos coletores e conversores, incorporadas após revisão |
| `data/history/` | Versões e diferenças registradas | Geradas junto com as propostas de atualização |
| `sources/` | PDFs e manifestos de procedência | Preservar os originais e seus hashes |
| `monitor/official/` | Capturas estruturadas do Planalto | Geradas pelo monitor |
| `monitor/stf/` | Configuração e referências do STF | Coleta automática pausada |
| `scripts/` | Build, servidor, importação e coleta | Ferramentas de manutenção |
| `tests/node/` | Testes da aplicação e publicação | Executados com `npm test` |
| `tests/python/` | Testes dos importadores e monitores | Executados com `npm run test:python` |
| `.github/workflows/` | Publicação e verificações no Actions | Alterar com atenção aos gatilhos e permissões |

## Executar e publicar

- `npm start`: gera o pacote e serve `dist/` na porta 3000. Rode novamente após editar os arquivos; não há recarga automática.
- `npm run build`: recria `dist/`, incluindo HTML autocontido, ícones e PDFs. Requer Node.js 22 ou superior, sem dependências npm.
- `npm test`: gera o pacote e executa os testes JavaScript.
- `npm run test:python`: executa os testes Python sem consultar as fontes na rede. Use Python 3.12 ou superior.

`dist/` é descartável e fica fora do Git. O arquivo `dist/index.html` incorpora estilos, JavaScript e textos para funcionar também na prévia isolada. Edite os arquivos de origem em `src/`, e gere o pacote novamente. A publicação inclui somente os arquivos permitidos pelo gerador, sem expor o checkout inteiro.

Ao incorporar mudanças à `main`, o workflow `deploy-pages.yml` testa o projeto e publica `dist/` no GitHub Pages. Os caminhos públicos, os favoritos do navegador e os links para artigos permanecem os mesmos.

## Atualização dos textos

O monitor do Planalto prepara os dados oficiais, o histórico e uma proposta em rascunho. A prévia gerada fica como artefato do Actions, sem versionar o HTML compilado. Após revisão e merge, o workflow de publicação atualiza o site.

As súmulas continuam com atualização manual; a rotina de coleta do STF permanece disponível somente para diagnóstico manual. Esta organização não reativa a coleta.

Consulte [Manutenção](MANUTENCAO.md), o [monitor das legislações](../monitor/README.md) e o [monitor do STF](../monitor/stf/README.md) para procedimentos e limites das fontes. Não edite diretamente os dados gerados para corrigir o processamento: ajuste o importador e confira a saída e a procedência.
