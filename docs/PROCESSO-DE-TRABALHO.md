# Lexa — processo de trabalho e governança

**Aplicação:** este processo passa a reger a colaboração quando integrado à branch principal. Sua adoção não modifica implementação nem decisões jurídicas já registradas.

## 1. Modelo de trabalho
- **Coordenação Central (decisão):** prioriza tarefas, aprova escopos, resolve divergências e autoriza merges/publicações.
- **Engenharia (execução):** arquitetura, código, builds, importadores e testes técnicos. O Codex local é o executor preferencial de tarefas delimitadas.
- **Integridade Jurídica (revisão especializada):** fidelidade às fontes, remissões, critérios de versão e limites de conclusão jurídica. Parecer de IA não substitui revisão humana independente.
- **UX e Produto (desenho e validação de experiência):** usabilidade, acessibilidade, UX Writing, protótipos e especificações.
- **Qualidade e Testes (verificação):** critérios de aceite, regressões, evidências reproduzíveis, comportamento em navegadores/dispositivos.
- **Inovação (consultiva):** hipóteses e exploração, acionada quando existir decisão de produto que mereça investigação. Não é uma aprovação obrigatória.

As frentes são responsabilidades de trabalho, não agentes humanos autônomos nem garantia de independência epistêmica. Só convocar as pertinentes ao risco da tarefa.

## 2. Fonte de verdade
| Pergunta | Fonte primária |
| --- | --- |
| O que está implementado? | Código e histórico da branch efetivamente examinada, com SHA |
| O que está em produção? | `main` e execução de publicação do GitHub Pages |
| O que há para fazer? | GitHub Issues e respectivos critérios de aceite |
| Uma alteração foi proposta ou integrada? | GitHub Pull Requests: base, HEAD, checks e campo `merged_at` |
| Qual regra arquitetural/de manutenção está vigente? | `docs/ESTRUTURA.md` e `docs/MANUTENCAO.md` na branch correspondente |
| Quais evidências embasam uma conclusão? | Testes, commits, arquivos vinculados e pareceres identificados |
| Onde ficam pareceres administrativos e pesquisa? | Google Drive, com links estáveis do registro decisório |

Não manter tabelas manuais de status de PR repetidas em vários documentos; usar links e consultar o estado real no GitHub. Documento histórico conserva a situação da data de elaboração e não é reescrito retroativamente.

## 3. Ciclo de uma tarefa
1. **Abertura:** a Coordenação cria uma Issue ou autoriza uma solicitação pequena. Registrar problema, escopo, fora de escopo, branch-base, critérios de aceite, risco e verificações previstas.
2. **Planejamento proporcional:** atividade trivial vai diretamente à execução; mudança relevante de arquitetura, fontes, remissões, acessibilidade ou PWA exige plano curto e revisões dirigidas.
3. **Execução em branch de tarefa:** Codex local edita somente o escopo aprovado. Evitar múltiplos executores alterando a mesma árvore. Commits pequenos e reversíveis.
4. **Verificação:** executar os testes correspondentes e guardar resultados; separar evidência técnica de aprovação jurídica. O GitHub Actions verifica o PR novamente.
5. **Revisão:** Qualidade ou Integridade são chamadas conforme risco; a Coordenação decide corrigir, manter em experimento, encerrar ou integrar.
6. **Fechamento:** registrar no PR/Issue o que foi implementado, commit/branch, testes observados, ressalvas e decisão. Atualizar documentação corrente apenas quando o conteúdo realmente mudar.

Abertura de PR **não** é merge; fechamento sem merge **não** incorpora conteúdo. PRs com base experimental devem manter a base correta; não redirecionar para `main` por conveniência.

## 4. Verificações proporcionais
- **Documentação:** links, paths, consistência, `git diff --check` e natureza do arquivo; suíte completa opcional.
- **UI/UX:** teste Node + verificações browser dirigidas (incluindo teclado, mobile, claro/escuro e estados offline quando afetados).
- **Infra/PWA/importadores:** build, Node, Python, testes de navegador e políticas de cache/versões relevantes.
- **Conteúdo jurídico/remissões:** evidências de procedência, testes de integridade + revisão humana independente antes da incorporação jurídica. Não validar vigência por inferência de IA.

Não alegar execução local, certificação de acessibilidade ou aprovação jurídica sem evidência correspondente.

## 5. Regras para o Free e Codex local
- Código e testes residem no computador; GitHub preserva repositório e histórico; ChatGPT coordena, sem ser a única memória.
- `AGENTS.md` mantém poucas instruções duráveis; o restante fica em docs específicas, consultadas sob demanda.
- Priorizar tarefas objetivas (uma Issue/uma branch/um PR), não reprocessar o histórico em cada sessão e monitorar o limite do Codex.
- Se o limite de Codex terminar, trabalhar manualmente ou retomar outra sessão a partir do Git, sem depender de execuções remotas.
- Codex local utiliza modelos hospedados e autenticação; **não** é operação de IA inteiramente offline.

## 6. Segurança da transição
Esta migração altera apenas processo e documentação. Não muda `src/`, `data/`, `sources/`, `monitor/`, workflows, conteúdo publicado ou remissões. Qualquer mudança de produção terá autorização e PR próprios. Antes de executar a migração local, conservar uma cópia íntegra/clone do repositório e conferir `git status`; nunca descartar alterações locais sem verificação.

## 7. Critério de conclusão da migração
- Documento de governança e `AGENTS.md` revisados e integrados.
- Codex local instalado **pelo usuário**, autenticado e testado na cópia local com tarefa inicialmente somente de leitura.
- Fluxo de Issue → branch → PR → revisão → merge exercitado em uma tarefa real.
- Checks do GitHub verificados; comportamento em produção e dados jurídicos preservados.
- A Coordenação registra a mudança de processo como operacional somente após a validação acima.
