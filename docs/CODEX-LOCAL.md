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

### Testes no Windows: UTF-8, fuso e artefatos

Use um ambiente virtual Python 3.12+ e prepare as dependências de teste:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r scripts/requirements-test.txt
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe -X utf8 -m unittest discover -s tests -p "test_*.py"
npm run build
.\.venv\Scripts\python.exe scripts/run_browser_tests.py --suite all --artifacts test-results/browser
```

`requirements-test.txt` inclui o Playwright fixado e `tzdata` somente no Windows, para resolver `America/Sao_Paulo`. Importar PDFs exige separadamente `scripts/requirements-import.txt`. O modo `-X utf8` é necessário nos testes Python que chamam ferramentas de manutenção com operações de texto dependentes do encoding padrão; essas ferramentas não são alteradas pela preparação dos testes. Para executar um teste de navegador individualmente, use também `-X utf8`.

O executor de navegador força UTF-8 nos subprocessos e logs. Screenshots são gravados diretamente em `--artifacts`, inclusive quando um teste falha; a execução individual usa `test-results/browser` ou a variável `LEXA_TEST_ARTIFACTS`. Use diretórios de artefatos diferentes para conservar execuções anteriores. Fixtures PWA são alteradas apenas em cópias temporárias, gravadas como bytes UTF-8, com SHA-256 calculado sobre o arquivo gravado.

Os testes usam `tempfile`, que respeita `TEMP` e `TMP`. Se o temporário do sandbox não permitir criar/remover subdiretórios, escolha um diretório gravável para esta sessão PowerShell antes de executar os testes:

```powershell
New-Item -ItemType Directory -Force test-results/tmp | Out-Null
$env:TEMP = (Resolve-Path test-results/tmp).Path
$env:TMP = $env:TEMP
```

Não versione `.venv/`, `dist/` nem os artefatos de teste. Os testes não certificam vigência ou homologação jurídica.

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

**Comprovação:** o estado da instalação é externo ao repositório e deve ser confirmado pelo mantenedor. A existência deste guia ou de um PR não comprova a instalação.
