# Validação de portabilidade dos testes no Windows

Escopo autorizado: testes, executor de navegador, dependências de testes e documentação. Base: `main`, commit `e57e04a`; branch de trabalho: `codex/windows-test-portability`. Esta evidência técnica não constitui homologação jurídica.

## Alterações

- Fixtures PWA: HTML e worker escritos como bytes UTF-8; o SHA-256 do HTML é calculado sobre o arquivo efetivamente gravado. Nenhuma mudança nos timeouts ou nas verificações de integridade.
- Operações de texto dos testes com encoding UTF-8 explícito. Executor com logs UTF-8 e `PYTHONUTF8=1`/`PYTHONIOENCODING=utf-8` nos subprocessos.
- Screenshots gravados diretamente no diretório de artefatos configurado; remoção dos caminhos `/tmp` e da coleta posterior dependente desse caminho.
- `scripts/requirements-test.txt` reúne o requisito existente de navegador e declara `tzdata` condicional ao Windows. Não altera as dependências específicas de coleta do STF.
- Preparação e execução PowerShell documentadas em `CODEX-LOCAL.md`.

## Comandos e evidências

Ambiente observado: Windows, Node v24.19.0, Python 3.12.10 do `.venv`, Playwright 1.62.0 e tzdata 2026.5. npm indisponível neste terminal; foram executados diretamente os comandos Node equivalentes ao script `npm test`.

| Verificação | Resultado |
| --- | --- |
| `node scripts/build-pages.mjs` | Passou: pacote com 49 arquivos de dados e 14 PDFs |
| `node --test tests/node/*.test.js` | 52 testes passaram |
| `.venv/Scripts/python.exe -X utf8 -m unittest discover -s tests -p 'test_*.py'` | 46 testes passaram com TEMP/TMP graváveis |
| `.venv/Scripts/python.exe -X utf8 -m pip check` | Sem requisitos incompatíveis |
| `pip install --dry-run --no-index -r scripts/requirements-test.txt` | Requisitos já instalados; avisos de limpeza do temporário do sandbox |
| Resolução de `America/Sao_Paulo` | Passou; conversão de UTC preserva a data local anterior quando aplicável |
| Análise sintática dos arquivos Python em `tests/` e do executor | 28 arquivos válidos |
| `git diff --check` | Passou |
| `.venv/Scripts/python.exe scripts/run_browser_tests.py --suite all --artifacts test-results/portability/browser` | 16 verificações passaram, zero falhas; incluindo PWA, atualização parcial e resumos de edição |
| Teste `tests/browser/pwa.py` isolado com `PYTHONUTF8=0` e captura UTF-8 explícita | Passou; leitura padrão cp1252 não afeta os bytes UTF-8 explícitos das fixtures |

A primeira tentativa Python, com o temporário padrão do sandbox, terminou com 13 erros de permissão em 46 testes. A repetição usou `TEMP` e `TMP` apontando para `test-results/portability/tmp`, sem modificar os testes ou ferramentas de produção para contornar permissões.

A primeira tentativa de navegador ficou sem progresso na inicialização do driver dentro do sandbox e foi interrompida. A execução fora do sandbox utiliza o mesmo código e os mesmos limites de tempo, com servidores locais e cópias temporárias.

O teste PWA antes registrado com timeout no aviso de atualização passou após a correção das fixtures, sem mudanças na aplicação. Também passaram as verificações de rejeição de shell incompleto e JSON adulterado, preservação de favoritos/preferências, atualização consentida, reutilização de JSONs inalterados e funcionamento offline. Não foi necessário acrescentar diagnóstico PWA nem aumentar timeouts. O executor preservou screenshots diretamente no diretório configurado.

Na captura adicional do teste isolado em cp1252, a primeira redireção do PowerShell perdeu acentos; o teste passou. Uma tentativa de captura por `runpy` falhou por não incluir `tests/browser` no caminho de importação. A captura final corrigiu apenas o comando de verificação, usou stdout UTF-8 explícito e passou com `utf8_mode: 0` e locale cp1252. Esses ajustes não alteraram arquivos de testes nem produção.

Logs locais ficam em `test-results/portability/`; esses artefatos são ignorados pelo Git. O `.venv/` preexistente permanece não rastreado e não integra a alteração.

## Limites

Não foram executadas instalação limpa, validação Linux, instalação da PWA pela interface do sistema ou homologação jurídica. Ferramentas de manutenção continuam com suas operações de texto originais; sua execução nos testes Python requer `-X utf8`, conforme documentado. Nenhum arquivo de produção, dado ou fonte jurídica deve integrar o diff desta tarefa.
