# Lexa — Codex local no Windows

Guia de preparação e operação. **Documentação não instala o Codex no computador do usuário nem comprova sua autenticação.**

## O que é e o que não é
Codex local inspeciona e modifica arquivos do seu repositório e executa comandos no Windows (PowerShell) ou WSL. O modelo continua sendo atendido pela OpenAI: requer autenticação/conectividade e obedece aos limites de uso do plano. O plano Free inclui Codex local sujeito a limite; Codex Cloud não está disponível no Free.

Documentação: https://developers.openai.com/codex/cli e https://help.openai.com/pt-br/articles/11369540-using-codex-with-your-chatgpt-plan.

## Pré-requisitos
- Git for Windows.
- Node.js 22 ou mais recente (`node --version`) e npm (`npm --version`).
- Python 3.12+ (`python --version`) para testes/importadores.
- VS Code opcional; Windows PowerShell é suficiente.
- Espaço em disco para repositório, PDFs e dependências de testes do navegador.

## Primeira instalação — PowerShell
Execute os comandos em uma pasta de desenvolvimento sua, não dentro de `dist/`. Se algum programa já estiver instalado, não reinstale sem necessidade.

```powershell
git --version
node --version
npm --version
python --version

npm install -g @openai/codex@latest
codex --version
```

Para fazer o primeiro clone em uma pasta chamada `lexa`:

```powershell
git clone "https://github.com/pajaao/lexa..git" lexa
cd lexa
git status --short --branch
git remote -v
```

Se já tiver um clone com alterações próprias, reutilize-o; **não** clone por cima da pasta e não descarte o trabalho existente.

Inicie com `codex` no diretório do repositório. Na primeira abertura, escolha **entrar com ChatGPT** em vez de configurar uma chave da API sem necessidade. Uma chave da API tem faturamento separado. Verifique no Codex `/status` para observar os limites da conta.

## Teste inicial seguro
Peça ao Codex: “Leia `AGENTS.md`, `docs/ESTRUTURA.md` e `package.json`. Explique os comandos de build e testes do Lexa, sem alterar arquivos nem executar ações externas.” Verifique a resposta contra os arquivos.

Em seguida, execute manualmente:
```powershell
npm test
python -m unittest discover -s tests -p "test_*.py"
```
Os testes de navegador dependem de configuração própria descrita em `docs/MANUTENCAO.md`. Após preparar as dependências, podem ser executados com:
```powershell
python scripts/run_browser_tests.py --suite essential
```

## Fluxo habitual
1. Escolha uma Issue com critérios de aceite e verifique `git status`.
2. Atualize a branch-base com cuidado e crie branch própria: `git switch -c tarefa/descricao-curta`.
3. Passe ao Codex somente a Issue, as restrições e os arquivos pertinentes. Mantenha sandbox e pedidos de aprovação habilitados; não use comandos de acesso irrestrito.
4. Leia `git diff` e os resultados efetivos dos testes; execute verificações apropriadas.
5. Faça commit, push e abra PR depois de revisar o diff e confirmar que não há arquivos/senhas acidentais. Merge/publicação só após autorização da Coordenação.
6. Se o limite do Codex acabar, retome manualmente com Git, Issues e documentação. Não é necessário recriar projeto em nuvem.

## Diagnóstico
- `codex --version`: confirma que o executável está no PATH.
- `codex doctor` quando suportado pelo cliente instalado: diagnóstico do Codex.
- `/status` dentro do Codex CLI: limites/uso.
- Verifique permissões de sandbox do Windows e solicitações de confirmação antes de conceder acesso fora da pasta.
- Se a versão instalada alterar comandos ou autenticação, consulte a documentação oficial atual; não introduza chaves da API apenas para contornar o Free.

**Status da migração local:** pendente de execução e validação no computador do mantenedor. A existência deste guia ou de um PR não significa que a instalação ocorreu.
