# Lexa — instruções permanentes para agentes de programação

## Missão e limites
O Lexa é uma PWA estática de consulta à legislação brasileira. Princípio: **"A complexidade está no Direito, não na sua consulta."** Não é ferramenta de interpretação jurídica nem utiliza IA na consulta ao usuário.

Use o processo definido em [docs/PROCESSO-DE-TRABALHO.md](docs/PROCESSO-DE-TRABALHO.md). Para configuração do Codex no Windows, consulte [docs/CODEX-LOCAL.md](docs/CODEX-LOCAL.md).

## Como trabalhar
- Identifique a branch, o commit-base e o escopo da tarefa. Antes de alterar, inspecione o estado local do Git para não sobrescrever trabalho alheio.
- Leia só os documentos relevantes: `docs/ESTRUTURA.md` para arquitetura; `docs/MANUTENCAO.md` para importação, PWA e testes; `monitor/README.md` para fontes; documentos de UX para modificações de interface. Não leia todo o histórico sem necessidade.
- Realize a menor alteração que satisfaça os critérios de aceite. Evite refatorações, dependências, automações e reestruturações não solicitadas.
- Não modifique `data/`, `sources/`, `monitor/official/` ou histórico jurídico em tarefas apenas de UX/estilo. Não corrija arquivos gerados à mão: corrija a origem e confira a saída.
- Preserve texto jurídico, identidade das edições, hashes, URLs, acessibilidade, comportamento offline e atualização consentida; qualquer exceção exige escopo explícito e evidências.
- Mudança de texto jurídico, fonte, extrator ou remissões requer revisão específica da Integridade Jurídica e **homologação humana independente** quando aplicável. IA, teste automatizado e parecer técnico não equivalem a homologação jurídica.
- Não misture experimentos de remissões com `main`: verifique as branches-base. Não presuma que material em branch, PR ou Drive esteja publicado.
- Não faça merge, publicação, alteração de credenciais nem ações destrutivas sem autorização expressa. Não desative testes para obter aprovação.

## Verificação e entrega
- Aplicação: Node.js >=22; `npm test` executa build e testes Node.
- Monitores/importadores: Python >=3.12; `python -m unittest discover -s tests -p 'test_*.py'` (ou comando equivalente do ambiente).
- Fluxos de navegador, quando relevantes e com dependências instaladas: `python scripts/run_browser_tests.py --suite essential`.
- Se a tarefa for documental, verifique links, paths, diferenças e consistência; testes funcionais completos podem ser desnecessários.
- Entregue: resumo objetivo, arquivos alterados, comandos e resultados efetivamente observados, limites não verificados, riscos e link para Issue/PR.
- Nunca descreva testes não executados como aprovados, nem confunda fechamento de PR com merge.
