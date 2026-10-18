# Lexa — Fase O2: entrega de organização documental

**Frente:** Engenharia · **Data:** 18/10/2026 · **Natureza:** saneamento exclusivamente documental.  
**Base principal confirmada:** `main` @ `84c5bb5c5e28c08376e0bf40cf3f3f4b4fd783cf`. Branch `organizacao/o2-documentacao`.  
**Base experimental confirmada:** `validacao/remissoes-fase-1a-2-fechamento` @ `64862b4b47811ab886396b9b22d4888af49aa4db`. Branch `docs/engenharia-o2-remissoes`.  
**Referência:** [auditoria O1 — PR #17](https://github.com/pajaao/lexa./pull/17), lida integralmente em sua versão publicada. O PR #17 ainda estava aberto. A O2 não pressupõe que O1 ou os pareceres estejam incorporados à `main`.

## 1. Resumo e situação verificada

- Em `main` foram adicionados [`docs/INDEX.md`](../INDEX.md) e [`docs/coordenacao/INDEX.md`](INDEX.md); o [`README.md`](../../README.md) recebeu **somente um parágrafo de navegação**.
- Em **branch experimental separada**, [`docs/remissoes/INDEX.md`](https://github.com/pajaao/lexa./blob/docs/engenharia-o2-remissoes/docs/remissoes/INDEX.md) organiza a cadeia 0.5–1A.3; [`fase-0-5.md`](https://github.com/pajaao/lexa./blob/docs/engenharia-o2-remissoes/docs/remissoes/fase-0-5.md) recebeu a correção ORG-A01 `phase 0.json` → `phase0.json` **somente no link Markdown**. O fixture, hash e bytes originais permanecem iguais.
- Na verificação de abertura da O2, os PRs **#7–#17 estavam abertos**, com o **#10 em draft**. #7–#10 e #17 tinham base `main`; #11 na 1A.1; #12 na 1A.2; #13–#16 no fechamento 1A.2. Nenhum foi retargetado, rebased, mesclado ou encerrado.
- `main` auditada não continha `docs/remissoes/` nem `docs/coordenacao/` antes desta O2; as remissões e pareceres foram vinculados por URLs explícitas de branch/PR e status. **Não houve incorporação do extrator**.

## 2. Arquivos criados e modificados

| Branch | Caminho | Operação | Limite |
|---|---|---|---|
| `organizacao/o2-documentacao` | `docs/INDEX.md` | criação | indexa documentação corrente, histórica e externa |
| mesma | `docs/coordenacao/INDEX.md` | criação | matriz #7–#17 por frente, fase, documento, base e estado |
| mesma | `README.md` | adição pontual | dois links de entrada para os índices |
| `docs/engenharia-o2-remissoes` | `docs/remissoes/INDEX.md` | criação | índice cronológico, artefatos e comandos de reprodução |
| mesma | `docs/remissoes/fase-0-5.md` | correção de um link | ORG-A01; não renomeia fixture |

Este relatório `docs/coordenacao/01-engenharia-organizacao-o2.md` é o **quarto arquivo Markdown alterado na branch principal**, criado apenas para documentar a execução. Não houve escrita fora desses conjuntos.

## 3. Navegação resultante

O [índice geral](../INDEX.md) distingue arquitetura, operação, fontes jurídicas e proveniência, histórico de desempenho, UX, testes, remissões experimentais e Coordenação. O [índice de Coordenação](INDEX.md) dirige cada parecer à sua branch/PR e alerta que PR aberto não significa merge. O índice experimental direciona para os relatórios das fases, dados de auditoria, protocolo, reprodutor e verificadores. Relatórios históricos permanecem em seus caminhos.

**Arquivos protegidos mantidos:** `src/`, `public/`, `data/{archive,official,history}/`, `sources/`, `monitor/`, `scripts/`, `tests/`, `.github/`, `package.json`, `.gitignore`; no experimental, `docs/remissoes/fase-1a-2/{arestas.json,arestas.csv,manifesto.json,rejeicoes-amostra.json,revisao-humana.csv,validacoes.json}`, `docs/remissoes/fase-1a-2-fechamento/{parenteticas.csv,verificacao.json,protocolo-revisao.md}` e todas as fixtures, edições, hashes e versões de regras. Esses arquivos não aparecem no diff. Permanecem quatro classes, `experimental-only`, 329 arestas e 30 parentéticas pendentes.

## 4. Verificações realmente executadas

1. **Leitura GitHub** dos heads, árvores completas e PRs abertos (metadados e bases). Parecer O1 lido integralmente.
2. **Diff por comparação GitHub**: branch principal inicialmente com **3 alterações Markdown** (`README.md`, dois índices); branch experimental com **2 alterações Markdown** (índice novo e uma substituição no relatório 0.5). Após este relatório, o diff esperado da branch principal soma **4 caminhos Markdown**. Não há arquivos protegidos alterados.
3. **Verificação estática de links relativos via árvore Git**: **38 referências internas válidas de 38 examinadas** entre `README.md`, `docs/INDEX.md`, `docs/coordenacao/INDEX.md`; na experimental, **43 de 43** entre `docs/remissoes/INDEX.md` e `fase-0-5.md`. Links absolutos para PRs/commits foram construídos sobre refs identificados; **não** foi executado crawler HTTP de cada URL externa.
4. **Não executados:** `npm test`, `npm run test:python`, Chromium/Playwright, benchmarks, testes físicos de PWA e reprodução dos inventários. Justificativa: modificações exclusivamente Markdown, sem build de código, fonte ou regra. Permanecem como gate recomendado antes de qualquer merge em `main` e em fases técnicas.
5. **GitHub Pages:** o workflow de deploy em `main` é conhecido pela O1; **não** foi comprovado nesta execução o SHA efetivamente servido ao público. Não há alegação de deploy.

## 5. Relação com o plano O1 e diferenças

Foi cumprida a etapa documental O2, com redução de escopo: **não** movemos `ESTRUTURA.md` ou `MANUTENCAO.md`, não incluímos dados experimentais em `main`, não copiamos pareceres de outros PRs e não alteramos interfaces. A criação do índice experimental e a correção ORG-A01 foram isoladas num PR com base própria, conforme instrução O2. A ordem de integração dos PRs anteriores continua responsabilidade da Coordenação.

## 6. Riscos, recomendações e pendências O3

- **Risco de ancestralidade:** não apontar #11–#16 à `main` sem PR novo independente; eles descendem de código experimental. Os índices devem continuar oferecendo links externos enquanto os arquivos não existirem em `main`.
- **Risco de links temporais:** alterações futuras em branches/PRs podem tornar a matriz desatualizada; preferir links por SHA para evidências congeladas e revalidar estado do PR no dia da decisão.
- **O3:** fixar manifesto dos arquivos protegidos, confirmar reprodução byte a byte dos cinco artefatos de 1A.2, validar SHA e conservação das 30 parentéticas, estudar política de armazenamento sem alterar bytes. Não tomar a existência do índice como homologação jurídica.
- **Coordenação:** deliberar PRs documentais e a fase O3; validar eventual integração isolada de índices; manter aprovação humana de elegibilidade e relações separada de verificações computacionais; decidir como certificar versão publicada.
- **Reversão:** reverter separadamente cada PR documental; nenhuma migração de caminhos, corpus, cache ou regras precisa ser desfeita.

**Veredito:** O2 concluída quanto ao saneamento e navegação documental, sujeita à revisão/integração dos PRs pela Coordenação. Nenhum merge, deploy, edição legislativa, remissão nova ou mudança de elegibilidade.
