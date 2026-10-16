<div align="center">

# § Lexa

### A lei, mais perto. A consulta, mais simples.

Códigos brasileiros, Constituição e súmulas vinculantes do STF, com leitura no próprio site.

**[Acessar o Lexa](https://pajaao.github.io/lexa./)** · **[Ver atualizações](https://pajaao.github.io/lexa./#/atualizacoes)** · **[Relatar um problema](https://github.com/pajaao/lexa./issues)**

[![Publicação no GitHub Pages](https://github.com/pajaao/lexa./actions/workflows/deploy-pages.yml/badge.svg)](https://github.com/pajaao/lexa./actions/workflows/deploy-pages.yml)

</div>

---

## O que é o Lexa?

O Lexa é uma biblioteca jurídica gratuita para encontrar e ler alguns dos textos federais mais utilizados no Brasil. Você pode abrir uma coleção, ir direto a um artigo, pesquisar uma expressão e compartilhar o link do trecho que está consultando.

O projeto foi pensado para estudantes, profissionais e qualquer pessoa que queira consultar esses textos com uma navegação simples. O acesso é livre, sem cadastro, no computador ou no celular.

## O que você encontra

| Coleção | Sigla | Acesso |
| --- | --- | --- |
| Constituição Federal de 1988 | CF | [Ler a Constituição](https://pajaao.github.io/lexa./#/cf) |
| Ato das Disposições Constitucionais Transitórias | ADCT | [Ler o ADCT](https://pajaao.github.io/lexa./#/cf/adct-1) |
| Código Civil | CC | [Ler o código](https://pajaao.github.io/lexa./#/civil) |
| Código Penal | CP | [Ler o código](https://pajaao.github.io/lexa./#/penal) |
| Código de Processo Civil | CPC | [Ler o código](https://pajaao.github.io/lexa./#/cpc) |
| Código de Defesa do Consumidor | CDC | [Ler o código](https://pajaao.github.io/lexa./#/cdc) |
| Código Tributário Nacional | CTN | [Ler o código](https://pajaao.github.io/lexa./#/ctn) |
| Súmulas Vinculantes do STF | SV | [Consultar as súmulas](https://pajaao.github.io/lexa./#/sv) |

O **ADCT** reúne disposições transitórias da Constituição e tem numeração própria. As **súmulas vinculantes** são enunciados do Supremo Tribunal Federal que consolidam entendimentos sobre questões constitucionais, com efeito vinculante nos termos da Constituição.

## Encontre o que precisa

Na busca da página inicial, digite o nome ou a sigla de uma coleção, ou indique uma referência completa:

| Você pode escrever | O que será encontrado |
| --- | --- |
| `Art. 60 CF` ou `CF art. 60` | Artigo 60 da Constituição Federal |
| `Art. 186 CC` | Artigo 186 do Código Civil |
| `Art. 1.022 CPC` | Artigo 1.022 do Código de Processo Civil |
| `Art. 54-A CDC` | Artigo 54-A do Código de Defesa do Consumidor |
| `ADCT art. 1` | Artigo 1 do ADCT |
| `SV 13` | Súmula Vinculante 13 |

Clique no resultado para abrir o texto. Quando houver apenas uma referência encontrada, você também pode pressionar **Enter**.

Dentro de cada coleção, a busca aceita números e expressões do texto, como `superendividamento`. Ela ignora diferenças entre letras maiúsculas, minúsculas e acentos. Na página inicial, buscas por palavras filtram as coleções pelo nome, área, sigla ou descrição.

## Uma leitura mais confortável

- **Navegação por capítulos e intervalos:** encontre seu lugar no texto e avance entre os resultados.
- **Tema claro ou escuro:** escolha o que fica mais confortável para você.
- **Fonte ajustável:** aumente ou diminua o tamanho durante a leitura.
- **Favoritos:** use a estrela para guardar uma entrada no navegador atual.
- **Links diretos:** compartilhe um artigo ou uma súmula sem precisar explicar o caminho.
- **Contexto das súmulas:** abra a seção de precedentes, jurisprudência e observações quando precisar aprofundar a consulta.
- **Histórico de versões:** acompanhe as edições incorporadas e compare as diferenças registradas.

Os favoritos ficam no seu dispositivo e navegador. Eles não são sincronizados entre aparelhos e podem ser perdidos ao limpar os dados do navegador.

## De onde vêm os textos?

As edições dos códigos e da Constituição são extraídas das páginas oficiais do **Planalto**, incorporadas ao site após revisão. Os PDFs utilizados na formação da base permanecem arquivados no repositório.

As súmulas vinculantes usam o PDF fornecido ao projeto, que declara consulta ao STF em **16/10/2026** e contém **63 entradas**, numeradas de 1 a 63. O site preserva as indicações desse documento, incluindo a **SV 9 como cancelada** e a **SV 30 como pendente de publicação**.

Cada coleção mostra sua edição e procedência em **“Sobre esta versão e a fonte de origem”**, com links para conferência.

> **Para utilizar os textos:** confira a edição consultada, a redação e as notas na fonte oficial. A data de coleta indica quando uma fonte foi consultada; o sistema não calcula automaticamente a vigência ou o início dos efeitos de cada alteração.

## Como as atualizações funcionam?

**Códigos e Constituição:** uma rotina diária consulta as fontes do Planalto. Quando detecta diferenças, prepara uma proposta de atualização no GitHub — chamada *pull request* — com relatório e prévia. A incorporação depende de revisão e aceitação pelo mantenedor. Depois disso, o site é publicado automaticamente.

**Súmulas vinculantes:** a atualização é periódica e manual, a partir de uma nova edição conferida pelo mantenedor. A coleta automática do STF está pausada por dificuldades de acesso ao portal.

Na página **[Atualizações](https://pajaao.github.io/lexa./#/atualizacoes)**, o primeiro registro estabelece a referência inicial. As versões seguintes mostram as diferenças registradas. Os destaques descrevem mudanças no texto; a classificação jurídica de seus efeitos depende de conferência na fonte.

## Encontrou algo que podemos melhorar?

Abra um registro na aba **[Issues](https://github.com/pajaao/lexa./issues)** do repositório. Conte o que você tentou fazer, qual resultado esperava e o que apareceu. Para um problema de conteúdo, inclua o número do artigo ou da súmula e o link da fonte oficial, se tiver.

Sugestões para melhorar a navegação e a leitura também são bem-vindas.

<details>
<summary><strong>Para quem quer executar ou manter o projeto</strong></summary>

### Executar no computador

Use **Node.js 22 ou superior**, sem necessidade de instalar dependências npm. Depois de baixar o repositório, abra um terminal na pasta do projeto e execute:

```sh
npm start
```

O terminal informa a porta local do servidor. Para gerar o pacote de publicação e executar os testes da aplicação:

```sh
npm run build:pages
npm test
```

A hospedagem usa GitHub Pages. Cada mudança incorporada na `main` passa pelas verificações do workflow antes da publicação.

Consulte a **[documentação de manutenção](docs/MANUTENCAO.md)** para detalhes sobre fontes, importação de PDFs, testes, estrutura dos arquivos e configuração do Pages. Veja também o **[monitor das legislações](monitor/README.md)** e a documentação da **[coleta pausada do STF](monitor/stf/README.md)**.

</details>
