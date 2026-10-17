# Remissões — investigação 0.5

Extrator experimental determinístico, executado **apenas em Node**. Não é importado pelo build de produção, por `src/`, pelo leitor ou pela PWA. Não há dependências novas nem consultas a modelos, serviços semânticos ou fontes externas.

Relatório e limitações: [Fase 0.5](../../docs/remissoes/fase-0-5.md).

## Reprodução

Use Node 22 e Python 3.12 já utilizados pelo projeto. Nenhuma instalação adicional é necessária.

```bash
# Regressões do extrator e do avaliador:
node --test tests/node/remissions*.test.js

# Análise independente da comparação histórica:
node scripts/remissions/analyze.mjs --output test-results/remissions

# Comparação opcional com a PoC Python original:
python scripts/remissions/phase0-baseline.py test-results/remissions/corpus.json test-results/remissions/phase0.json
node scripts/remissions/analyze.mjs --baseline test-results/remissions/phase0.json --output test-results/remissions

# Reproduzir somente a seleção de fontes da avaliação, sem gerar expectativas:
node scripts/remissions/select-sample.mjs

# Verificações existentes:
npm test
python -m unittest discover -s tests -p 'test_*.py'
python scripts/run_browser_tests.py --suite essential
```

`test-results/` já é ignorado pelo Git. A CLI não permite gravar seus resultados nas pastas jurídicas ou publicadas. Não copie `bundle.json` para `dist/` ou para o site: **os candidatos A da varredura completa não foram integralmente revisados**.

Python serve exclusivamente à comparação histórica com o arquivo original da Fase 0; não é dependência do extrator Node, do build futuro ou do navegador.

## Contrato

Entrada: `{collections: [{code, sha256}]}`, com os mesmos JSONs jurídicos produzidos em memória por `buildPackage()`. O hash declarado deve corresponder a `JSON.stringify(code)`. Nenhum campo jurídico é alterado. Extração exclusivamente de `paragraphs[].runs[]`; sem súmulas/notas de jurisprudência.

`extractRemissions()` retorna ocorrências, proveniência UTF-16, resolução, condição de tachado, versões e diagnósticos. `relationGraph()` deduplica as conexões A atuais e deriva as inversas por índices da mesma tabela. `compactBundle()` é apenas uma representação de investigação.

Não é um resolvedor de subdispositivos. Qualificadores são preservados, mas não recebem identidades fictícias de parágrafo, inciso ou alínea. Referências implícitas/relativas são registradas como C; entradas agrupadas não são certificados de destino individual.

Amostras têm edição fixa. Se a legislação mudar, conferir conscientemente os fixtures e as expectativas; não regenerar destinos usando o extrator que está sendo avaliado. `sampling.json` registra a seleção e os hashes. A leitura/anotação foi feita pelo mesmo agente de desenvolvimento, sem revisão jurídica humana independente.
