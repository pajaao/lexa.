# Baseline de desempenho — etapa 1

Esta etapa instrumenta e testa o Lexa existente. Não altera `src/`, o build do aplicativo, os textos jurídicos, PDFs, capturas ou históricos. Não é uma rodada de otimizações nem uma previsão de desempenho em aparelhos ou redes reais.

## Estrutura analisada

| Área | Situação e responsabilidade |
| --- | --- |
| `src/` | SPA sem framework: `app.js` controla rotas/leitura; `loading.js` carrega/verifica JSONs; `collection-model.js` e `library-search.js` preparam texto e índices; `sw.js` mantém a edição offline íntegra. Nenhum desses arquivos foi modificado nesta etapa. |
| `scripts/` | Build modular, servidor estático e importadores/monitores. Acrescentados somente runner e requisitos Python de navegador. |
| `tests/node/` | Geração, integridade do pacote, catálogo, referências, busca, hierarquia e cópia. Todos preservados. |
| `tests/python/` | Importadores e monitores; quatro testes novos verificam a contagem de transferências e as estatísticas, sem depender de Playwright. |
| `tests/browser/` | Nove verificações funcionais existentes, antes executadas manualmente; benchmark ampliado e novo teste do contrato de cache/medição. |
| `.github/workflows/` | Publicação e monitores existentes; novo workflow de verificação de PRs e testes essenciais como condição para a publicação. |

## Protocolo

O benchmark continua em `tests/browser/performance.py`. Preserva o argumento posicional de diretório e os campos `runs_ms`/`median_ms` da abertura inicial com cache frio; o relatório expandido usa `schema_version: 2`.

- Cinco execuções por cenário, Chromium headless, CPU limitada por CDP com fator 4, viewport 375 × 812, idioma pt-BR e fuso America/Sao_Paulo.
- HTTP em loopback, sem compressão, TLS ou simulação de latência/banda. Não depende do Planalto, STF ou GitHub para carregar textos. O servidor do benchmark reproduz as regras de cache do servidor do projeto: JSONs com hash são imutáveis; demais arquivos usam `no-cache`. Usa Content-Length e não implementa respostas condicionais 304.
- Um processo de navegador é reutilizado, mas cada grupo usa um contexto novo. “Frio” significa cache HTTP e memória da aplicação vazios nesse contexto; não significa disco do sistema operacional ou processo Chromium recém-iniciado.
- Em **warm_http**, a preparação ocorre fora da medição. O documento é recarregado para zerar o modelo JavaScript mantendo o cache HTTP. O teste verifica que os dados não estão carregados antes da primeira busca ou abertura. O histórico de leitura é removido no preparo do leitor para evitar pré-carregamento por retomada.
- A primeira busca é `dignidade`; as posteriores são `educacao` e novamente `dignidade`. A condição de término confere a consulta atual e seus destaques, não apenas o número de grupos: ambas as consultas podem produzir a mesma quantidade de coleções.
- Código Civil, CPC e CLT são abertos em contextos independentes da busca global. Cada um tem abertura, próxima página e retorno à página anterior. A vista inicial é estabilizada antes de cronometrar a abertura, sem espera fixa por milissegundos.
- O tempo principal vai da navegação/ação até o estado funcional esperado no DOM. Inclui preenchimento, debounce, ação de clique/rolagem e viagens de automação. Não é o tempo puro de uma função JavaScript. `next_frame_ms` registra dois requestAnimationFrame após a prontidão; não representa o fim de todas as animações nem uma métrica Core Web Vitals.
- O timeout funcional de segurança interrompe um cenário travado. Nenhum tempo de carregamento absoluto é usado para aprovar/reprovar desempenho.

### Transferência e instalação offline

Nos cenários da interface, service workers ficam **bloqueados**. `network_bytes` vem de `Network.loadingFinished.encodedDataLength` e inclui headers de resposta, separando shell, JSONs e outros recursos. Respostas de cache não são somadas como download novo; o valor bruto informado pelo CDP também é preservado. Contagens de requisições, cache, falhas e requisições não concluídas acompanham cada amostra.

`origin_body_bytes` é uma auditoria independente do servidor: soma somente os corpos enviados, sem headers. Não é igual a bytes de rede nem inclui compressão. Recursos incidentais do navegador, como manifesto e favicon, podem aparecer como “outros”; não são atribuídos ao download de uma norma.

**offline_preparation** usa contextos novos separados, com service worker permitido, e termina quando a instalação completa prepara a leitura e assume o controle da página. Para esse cenário, use os bytes de corpo auditados no servidor: o CDP da página não captura todos os requests originados no worker. Esse total inclui a navegação inicial e a instalação; não se deve somá-lo às linhas de interface como se fosse uma única visita.

### Memória e limites

`js_heap_after_gc_bytes` usa o contador CDP JSHeapUsedSize do alvo da página após solicitar coleta de lixo. O snapshot e o GC ficam fora do tempo cronometrado. O delta é apenas a diferença entre snapshots; uma navegação pode substituir o documento e reduzir esse valor.

Esse contador não mede pico, RSS, memória total do navegador, DOM nativo, GPU ou heap do service worker. Não é uma estimativa de RAM total do dispositivo. Se CDP não fornecer a medição, o campo fica `null` e a limitação é registrada; não se transforma ausência de dados em zero. `--no-memory` permite omitir esses snapshots. O host é um contêiner compartilhado: frequência da CPU e carga de outros processos não estão controladas. Não compare tempos entre máquinas ou versões de navegador como se as condições fossem idênticas.

## Reproduzir

Requisitos: Node 22, Python 3.12, Playwright fixado e Chromium. Não há dependências npm novas. Recomenda-se ambiente virtual Python:

```sh
python3 -m venv /tmp/lexa-browser-venv
/tmp/lexa-browser-venv/bin/pip install -r scripts/requirements-browser.txt
/tmp/lexa-browser-venv/bin/python -m playwright install --with-deps chromium
npm test
python3 -m unittest discover -s tests -p 'test_*.py'
/tmp/lexa-browser-venv/bin/python scripts/run_browser_tests.py --suite essential
/tmp/lexa-browser-venv/bin/python tests/browser/performance.py --runs 5 --cpu 4 --output test-results/performance.json
```

O helper usa `LEXA_CHROMIUM`, se definido, depois um Chromium do sistema e, na ausência dele, o binário baixado pelo Playwright. Para reproduzir com um executável específico, defina `LEXA_CHROMIUM` com seu caminho. O Actions seleciona explicitamente o Chromium correspondente ao Playwright instalado.

O argumento de diretório continua disponível: `python tests/browser/performance.py /caminho/do/pacote --runs 5`. O pacote deve conter o catálogo e os JSONs modulares. `--skip-offline` omite a medição separada de instalação, sem liberar workers nos cenários da interface. Os grupos de busca esperados são derivados dos próprios JSONs do pacote.

Para todos os testes funcionais de navegador, use `python scripts/run_browser_tests.py --suite all`. O runner mantém logs separados e recolhe somente as capturas geradas naquela execução. Saída 1 indica falha funcional; os valores de duração não determinam sucesso.

## Integração no Actions

- **Verificar Lexa** (`verify.yml`): PRs executam Node, Python e oito verificações essenciais de navegador: interface, carga por norma/retry, leitura, busca global, favoritos, cópia, PWA e contrato do benchmark.
- Execução manual desse workflow com `benchmark=true`: coleta cinco rodadas e guarda os dados como artefato. A coleta não tem um orçamento absoluto de tempo como critério de regressão.
- **Publicar Lexa no GitHub Pages**: os mesmos testes essenciais passam antes de guardar/publicar o pacote. Uma falha funcional impede o deploy.
- A action local `setup-browser` evita duplicar a preparação de dependências e escolhe explicitamente o Chromium da versão fixada do Playwright.
- Logs e capturas são guardados por 14 dias, inclusive após falhas. Benchmark e relatórios avulsos ficam em `test-results/`, fora do Git. A baseline revisada é arquivada em `docs/baselines/`.

O teste `benchmark_contract.py` verifica cache frio, reload com memória vazia e cache HTTP preservado, e buscas em memória sem novo download jurídico. Não exige que o navegador deixe de solicitar recursos incidentais nem impõe um tempo máximo de resposta. Os nove testes anteriores continuam disponíveis; ajustes neles limitam-se à seleção portátil do navegador e a uma espera funcional por foco em lugar de uma asserção imediata suscetível a corrida.

## Resultados

Os resultados e as medianas desta execução são apresentados abaixo, acompanhados do relatório bruto para auditoria.

Relatório bruto: [135 amostras e metadados](baselines/chromium-cpu4x-2026-10-17.json). Cinco amostras por linha. A revisão de instrumentação medida foi `fbaf46c`; o código do aplicativo é o da `main` em `54be7bd`. O JSON registra SHA-256 do benchmark, HTML e catálogo.

Ambiente efetivamente utilizado: Chromium **154.0.8037.57** do sistema (`/usr/bin/chromium`), Playwright **1.62.0**, Node **v22.23.3**, Python **3.12.14**, Linux x86_64/glibc 2.41, contêiner compartilhado com 5 CPUs lógicas reportadas. CPU da página limitada a 4×. O preparo offline inclui trabalho do service worker em outro alvo: sua CPU não foi limitada separadamente e sua memória não foi medida. Por isso não compare a duração de instalação diretamente com o tempo de busca.

Unidades: KiB = 1024 bytes; MiB = 1024² bytes. “Rede” inclui headers de resposta; “JSON” é o subconjunto jurídico. “Heap” é o snapshot JavaScript após GC e não a RAM total do navegador.

### Cache HTTP frio

| Cenário | Mediana (ms) | Rede (KiB) | JSON (KiB) | Heap (MiB) |
| --- | ---: | ---: | ---: | ---: |
| Biblioteca inicial | 392.4 | 132.91 | 0.00 | 1.27 |
| Primeira busca global (`dignidade`) | 1538.0 | 8736.41 | 8736.41 | 32.85 |
| Busca posterior (`educacao`) | 264.8 | 0.00 | 0.00 | 32.89 |
| Repetição (`dignidade`) | 259.1 | 0.00 | 0.00 | 32.90 |
| Abrir Código Civil | 526.9 | 1085.36 | 1084.90 | 4.95 |
| Civil: próxima página | 205.6 | 0.00 | 0.00 | 5.00 |
| Civil: página anterior | 208.4 | 0.00 | 0.00 | 5.04 |
| Abrir CPC | 452.9 | 956.14 | 955.69 | 4.36 |
| CPC: próxima página | 161.1 | 0.00 | 0.00 | 4.42 |
| CPC: página anterior | 162.6 | 0.00 | 0.00 | 4.45 |
| Abrir CLT | 504.3 | 1912.54 | 1912.08 | 6.10 |
| CLT: próxima página | 184.1 | 0.00 | 0.00 | 6.14 |
| CLT: página anterior | 158.6 | 0.00 | 0.00 | 6.18 |

### Cache HTTP aquecido; memória reiniciada antes da primeira ação

| Cenário | Mediana (ms) | Rede (KiB) | JSON (KiB) | Heap (MiB) |
| --- | ---: | ---: | ---: | ---: |
| Biblioteca inicial | 182.9 | 132.91 | 0.00 | 1.40 |
| Primeira busca global (`dignidade`) | 1494.2 | 0.00 | 0.00 | 32.85 |
| Busca posterior (`educacao`) | 267.5 | 0.00 | 0.00 | 32.89 |
| Repetição (`dignidade`) | 274.3 | 0.00 | 0.00 | 32.91 |
| Abrir Código Civil | 447.6 | 0.46 | 0.00 | 4.96 |
| Civil: próxima página | 193.4 | 0.00 | 0.00 | 5.01 |
| Civil: página anterior | 209.9 | 0.00 | 0.00 | 5.06 |
| Abrir CPC | 356.5 | 0.46 | 0.00 | 4.37 |
| CPC: próxima página | 152.4 | 0.00 | 0.00 | 4.42 |
| CPC: página anterior | 152.9 | 0.00 | 0.00 | 4.45 |
| Abrir CLT | 451.7 | 0.46 | 0.00 | 6.11 |
| CLT: próxima página | 202.9 | 0.00 | 0.00 | 6.15 |
| CLT: página anterior | 162.8 | 0.00 | 0.00 | 6.18 |

### Preparação offline — cenário separado

| Mediana de preparo (ms) | Corpos enviados pela origem (bytes) | Corpos (MiB) | Heap da página após GC (MiB) |
| ---: | ---: | ---: | ---: |
| 412.3 | 9272819 | 8.84 | 1.28 |

Essa é a transferência do preparo completo, incluindo a navegação inicial e as requisições da instalação. Não é o volume necessário para mostrar os cartões. O número não inclui headers e não é comparável diretamente à coluna “Rede” dos outros cenários. O heap não inclui o worker.

### Achados para as próximas etapas

1. **A primeira busca é o maior custo de interação medido.** Ela prepara 14 coleções e transfere 8.946.085 bytes de rede no cache frio. O heap JavaScript retido da página passa de aproximadamente 1,27 MiB na biblioteca para 32,85 MiB após a busca. Isso não demonstra vazamento; o aplicativo conserva dados e índices para reutilização.
2. **Cache HTTP e índice em memória são benefícios diferentes.** Após reload, o cache elimina a transferência jurídica, mas a primeira busca continua perto de 1,49 s, contra 1,54 s no frio. Nesse teste local, parse, preparação e indexação ainda precisam acontecer. Investigar essa etapa é uma hipótese para a próxima rodada, não uma conclusão sobre redes reais.
3. **Buscas posteriores e paginação não baixam normas.** Foram observados zero bytes de rede nas buscas posteriores e na paginação desta coleta. Aberturas com cache quente podem mostrar 468 bytes de outros recursos, como o manifesto, mesmo com zero bytes jurídicos; não são falhas do cache da norma.
4. **O preparo offline é independente do custo inicial de renderização.** A biblioteca fria transfere 136.100 bytes de rede, enquanto o preparo offline envia 9.272.819 bytes de corpos pela origem. Contabilizar ambos como download necessário para mostrar a home seria incorreto.
5. **Não há orçamento de regressão estabelecido ainda.** Medianas locais com host compartilhado não justificam falhar CI por alguns milissegundos. Esta etapa registra dados e verifica correção; limites ou novas estratégias de índice/carga devem ser discutidos após outras medições.

### Verificações executadas

- `npm test` passou com Node 22.23.3.
- `python3 -m unittest discover -s tests -p 'test_*.py'`: **46 testes passaram**, incluindo os quatro novos testes da contabilidade do benchmark.
- Os **nove testes funcionais de navegador existentes** passaram pelo runner; o novo contrato de medição também passou. Há dez verificações na suíte completa e oito na essencial.
- Coleta completa: **135 amostras**, sem erros JavaScript, falhas de requisição ou requisições medidas pendentes. Heap disponível em todas as amostras; limitações de escopo descritas acima.
- Os YAMLs da action local e dos workflows novos/alterados foram analisados localmente. A execução real do Actions deve ser confirmada no PR; não foi simulada como se já tivesse ocorrido no GitHub.
- Comparação com a base confirma ausência de alterações em `src/`, `data/`, `sources/` e capturas oficiais. O script de build do aplicativo permanece igual.
