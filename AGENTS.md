# Lexa — instruções permanentes para agentes de programação

## Missão e limites
O Lexa é uma PWA estática de consulta à legislação brasileira. Princípio: **"A complexidade está no Direito, não na sua consulta."** Não é ferramenta de interpretação jurídica nem utiliza IA na consulta ao usuário.

Este arquivo reúne as instruções operacionais essenciais do Lexa. A **Governança v3 — Desenvolvimento Enxuto** está detalhada em [docs/PROCESSO-DE-TRABALHO.md](docs/PROCESSO-DE-TRABALHO.md) e deve ser consultada quando houver dúvidas sobre procedimentos, classificação de risco ou mudanças nas regras do projeto. **Não é necessário reler o documento completo a cada tarefa**: aplique as regras aqui descritas e consulte apenas o contexto complementar relevante. Para configuração do Codex no Windows, consulte [docs/CODEX-LOCAL.md](docs/CODEX-LOCAL.md).

## Como trabalhar
- Produto e Coordenação define problema, escopo, aceite e autoriza a integração; Desenvolvimento implementa com Codex local, testa e prepara o PR; Revisão e Qualidade verifica conforme o risco. Engenharia especializada, UX, Integridade Jurídica e Inovação são competências acionadas quando necessárias, sem etapas administrativas permanentes.
- Classifique pelo impacto real: simples (execução direta, testes pertinentes e PR conciso), intermediário (critérios de aceite e revisão dirigida) ou crítico (análise de risco, testes rigorosos e revisão especializada). A quantidade de arquivos não determina o nível.
- Identifique a branch, o commit-base e o escopo da tarefa. Antes de alterar, inspecione o estado local do Git para não sobrescrever trabalho alheio.
- Leia só os documentos relevantes: `docs/ESTRUTURA.md` para arquitetura; `docs/MANUTENCAO.md` para importação, PWA e testes; `monitor/README.md` para fontes; documentos de UX para modificações de interface. Não leia todo o histórico sem necessidade.
- Realize a menor alteração que satisfaça os critérios de aceite. Evite refatorações, dependências, automações e reestruturações não solicitadas.
- Não modifique `data/`, `sources/`, `monitor/official/` ou histórico jurídico em tarefas apenas de UX/estilo. Não corrija arquivos gerados à mão: corrija a origem e confira a saída.
- Preserve fidelidade do texto jurídico, proveniência das fontes, identidade das edições, hashes, URLs, segurança, integridade, acessibilidade, comportamento offline e atualização consentida; qualquer exceção exige escopo explícito e evidências.
- Mudança de texto jurídico, fonte, extrator ou remissões requer revisão específica da Integridade Jurídica e **homologação humana independente** quando aplicável. IA, teste automatizado e parecer técnico não equivalem a homologação jurídica.
- As remissões expressas estão temporariamente suspensas; não proponha sua reativação nesta alteração documental. Mantenha experimentos separados da produção e verifique as branches-base. Não presuma que material em branch, PR ou Drive esteja publicado.
- Não faça merge, publicação, alteração de credenciais nem ações destrutivas sem autorização expressa. Não desative testes para obter aprovação.

Use Issues e PRs como registros principais. Não produza pareceres, auditorias, atas ou relatórios extensos por padrão, nem duplique registros entre GitHub, Drive e Markdown. Documentos adicionais só quando necessários para decisões duradouras, investigações complexas, evidência jurídica ou reprodução de testes. Não repita auditorias concluídas se o código relevante não mudou.

## Verificação e entrega
- Aplicação: Node.js >=22; `npm test` executa build e testes Node.
- Monitores/importadores: Python >=3.12; `python -m unittest discover -s tests -p 'test_*.py'` (ou comando equivalente do ambiente).
- Fluxos de navegador, quando relevantes e com dependências instaladas: `python scripts/run_browser_tests.py --suite essential`.
- Se a tarefa for documental, verifique links, paths, diferenças e consistência; testes funcionais completos podem ser desnecessários.
- Entregue apenas: alterações realizadas, testes efetivamente executados, riscos ou limitações e pendências reais.
- Nunca descreva testes não executados como aprovados, nem confunda fechamento de PR com merge.
