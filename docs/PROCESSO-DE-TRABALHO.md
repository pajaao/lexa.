# Lexa — Governança v3 — Desenvolvimento Enxuto

Desenvolvimento orientado a entregas, com revisão proporcional ao impacto real. A governança não altera implementação nem decisões jurídicas já registradas e não exige pareceres sucessivos para tarefas rotineiras.

## 1. Funções e responsabilidades

- **Produto e Coordenação:** define problema, prioridades, escopo e critérios de aceite; resolve divergências e autoriza a integração.
- **Desenvolvimento:** implementa com Codex local, executa os testes correspondentes e prepara o PR.
- **Revisão e Qualidade:** realiza verificação técnica ou independente quando necessária, especialmente em alterações relevantes ou críticas.

Engenharia especializada, UX, Integridade Jurídica e Inovação são competências acionadas conforme a necessidade, não etapas administrativas permanentes. As funções não representam agentes humanos autônomos nem garantem independência da revisão. IA e testes não substituem homologação jurídica humana independente.

## 2. Classificação das tarefas

Classifique pelo impacto real, não pela quantidade de arquivos modificados. Uma alteração localizada pode ser crítica se afetar um mecanismo sensível.

| Nível | Exemplos e tratamento |
| --- | --- |
| **Simples** | Correções localizadas, textos de interface e pequenos ajustes visuais. Execução direta, testes pertinentes e PR conciso. |
| **Intermediário** | Novas funcionalidades e mudanças relevantes na navegação, acessibilidade ou experiência. Critérios de aceite claros, implementação, testes e revisão dirigida. |
| **Crítico** | Alterações em texto jurídico, fontes, extratores, integridade de dados, hashes, segurança, atualizações PWA ou mecanismos sensíveis. Análise de risco, testes rigorosos e revisão especializada; revisão humana independente quando a natureza jurídica exigir. |

## 3. Fluxo de uma entrega

1. **Definir:** Produto e Coordenação cria uma Issue ou autoriza uma solicitação pequena, delimitando problema, escopo e critérios de aceite. Identificar base e nível de risco; planejar apenas o necessário para esse nível.
2. **Implementar:** conferir o Git e trabalhar em branch de tarefa, com a menor alteração que satisfaça a entrega. Evitar múltiplos executores alterando a mesma árvore; preservar trabalho local e usar commits pequenos e reversíveis.
3. **Verificar e preparar o PR:** executar testes pertinentes, registrar resultados reais e revisar o diff. O GitHub Actions verifica o PR novamente. Não repetir auditorias concluídas quando o código relevante não mudou.
4. **Revisar e decidir:** aplicar revisão dirigida ou especializada conforme o risco. Produto e Coordenação decide corrigir, manter em experimento, encerrar ou autorizar a integração. Não exigir rodadas sucessivas de pareceres por rotina.

Abertura de PR não é merge; fechamento sem merge não incorpora conteúdo. PRs experimentais conservam sua base correta, sem redirecionamento para `main` por conveniência. Merge, publicação, alteração de credenciais e operações destrutivas exigem autorização expressa.

## 4. Registros e fonte de verdade

Issues e PRs são os registros principais de execução e decisão. O resumo habitual informa apenas alterações realizadas, testes efetivamente executados, riscos ou limitações e pendências reais.

| Pergunta | Fonte primária |
| --- | --- |
| O que está implementado? | Código e histórico da branch examinada, com SHA |
| O que está em produção? | `main` e execução de publicação do GitHub Pages |
| O que há para fazer? | Issues e critérios de aceite |
| Uma alteração foi proposta ou integrada? | PR: base, HEAD, checks e `merged_at` |
| Qual regra técnica está vigente? | [Estrutura](ESTRUTURA.md) e [Manutenção](MANUTENCAO.md) na branch correspondente |
| Quais evidências sustentam a entrega? | Resultados reais, commits e arquivos vinculados na Issue ou no PR |

Não produzir pareceres, auditorias, atas ou relatórios extensos por padrão. Evitar duplicação entre GitHub, Drive e Markdown, inclusive tabelas manuais de status de PR. Criar documentos adicionais somente para decisões duradouras, investigações complexas, evidência jurídica ou reprodução de testes. Vincular material existente quando necessário; não reescrever documentos históricos para alterar a situação registrada à época. Atualizar documentação corrente apenas quando seu conteúdo mudar. A simplificação não exige novos documentos, templates ou etapas de aprovação.

## 5. Proteções e verificações proporcionais

- **Integridade jurídica:** preservar texto, proveniência das fontes, identidade das edições, hashes, URLs, notas e histórico. Mudanças em texto jurídico, fontes, extratores ou remissões requerem revisão específica de Integridade Jurídica e homologação humana independente quando aplicável. Não inferir vigência por IA nem confundir testes ou parecer técnico com aprovação jurídica.
- **Remissões expressas:** temporariamente suspensas. Esta alteração documental não propõe sua reativação. Manter ambientes e branches experimentais separados da produção; material em branch, PR ou Drive não comprova publicação.
- **Segurança e qualidade:** preservar segurança, integridade, acessibilidade, comportamento offline e atualização consentida. Não desativar testes para obter aprovação, não descartar trabalho local sem verificação e não corrigir dados gerados à mão: corrigir a origem e conferir a saída. Tarefas de UX/estilo não alteram dados ou histórico jurídico.
- **Documentação:** verificar links, caminhos, consistência, diff e `git diff --check`; testes funcionais completos podem ser desnecessários.
- **UI/UX:** testes Node e verificações de navegador pertinentes, incluindo teclado, mobile, temas e offline quando afetados.
- **Infra/PWA/importadores:** build, testes Node, Python e navegador, com verificações de cache e versões relevantes ao risco.
- **Conteúdo jurídico:** evidências de procedência, testes de integridade e revisão humana independente antes da incorporação quando juridicamente necessária.

Executar os comandos aplicáveis de [AGENTS.md](../AGENTS.md) e [Manutenção](MANUTENCAO.md). Nunca declarar testes não executados como aprovados nem alegar execução local, certificação de acessibilidade ou aprovação jurídica sem evidência.

## 6. Operação com Codex local

- Código e testes residem no computador; GitHub preserva repositório e histórico. O chat não é a única memória do trabalho.
- Manter poucas instruções duráveis em `AGENTS.md`; consultar documentação específica sob demanda, sem reprocessar todo o histórico a cada sessão.
- Priorizar tarefas delimitadas e monitorar o limite de uso. Se ele terminar, continuar manualmente ou retomar pelo Git em outra sessão, sem depender de execuções remotas.
- Codex local utiliza modelos hospedados e autenticação; não é operação de IA inteiramente offline. A preparação do Windows permanece em [CODEX-LOCAL.md](CODEX-LOCAL.md).
