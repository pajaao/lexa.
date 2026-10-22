# Redações anteriores — fluxo HTML simples

## Implementação local corrigida

O fluxo existente separa identificação documental, conteúdo riscado e apresentação. Não reconstrói sucessões legislativas nem exige correspondência com o texto atual.

1. `scripts/extract_struck_html.py` lê os 13 HTMLs de `HTML/`, identifica o artigo por caput, âncoras e contexto, separa notas e preserva HTML bruto, localização e hash. Referências internas, falta de inciso-pai ou pontuação não invalidam o artigo. Notas malformadas não apagam o prefixo normativo recuperável. `blockquote` de formatação requer evidência nativa do artigo.
2. `scripts/present_struck_html.py` prepara registros `pending` na fixture experimental quando artigo e conteúdo estão identificados. Fragmentos separados por texto não riscado permanecem separados. Rubricas usam posição estrutural; títulos, capítulos, seções, ementas, marcadores isolados e duplicatas não viram redações anteriores.

Na Parte Geral antiga do CP e na região antiga do júri do CPP, conserva-se a numeração documental. O painel informa que a correspondência ao conteúdo do dispositivo atual não está estabelecida. CF e ADCT permanecem distintos. O leitor principal remove os runs riscados sem depender de registros disponíveis no painel; os dados originais e os runs não riscados não são reescritos.

## Dados de referência necessários aos testes

Diretório: `experiments/previous-wordings-simple/20261021-associations-corrected/`.

- `extraction.json`: 3.188 ocorrências, textos/runs/HTML bruto, localização, hashes e contexto documental.
- `presentation.json`: todas as decisões; 3.034 ocorrências associadas e 154 excluídas, com motivos.
- `reader.json`: leitor usado como referência de existência dos dispositivos, sem exigir igualdade com a redação atual. Seu conteúdo é idêntico ao snapshot já preservado em `20261021-complete/reader.json`.
- `tests/fixtures/previous-wordings-simple.json`: 3.036 registros `pending`; uma ocorrência da CLT gera três fragmentos separados. Não são versões completas de artigos.

Os 1.680 IDs anteriores, seus textos, notas, referências, fontes e estados foram preservados. Quatro vínculos documentais foram corrigidos de CP 333 para CP 334 após reconhecer o marcador `A rt. 334`, sem modificar sua grafia na transcrição.

As 154 exclusões são: 85 estruturas supra-artigo, duas ementas, 37 ocorrências sem texto normativo antigo, 17 indicações de veto/revogação e 13 duplicatas. Todas as decisões estão no snapshot de apresentação.

As fontes originais já versionadas em `HTML/` permitem reproduzir a execução. Cópias duplicadas de HTML, preview duplicado, backup de fixture, logs, relatórios temporários e manifesto da execução local completa não integram este conjunto mínimo. Permanecem preservados localmente. Os três JSONs acima são referências de teste, não um diretório completo para executar `--verify` diretamente.

## Testes e prévia

Requisitos: Python 3.12+ e Node 22+. Testes Python não exigem pacotes externos.

```powershell
python -B -m unittest discover -s tests/python -p test_simple_previous_wordings.py
npm test
$env:PORT='3012'
npm run preview:legislative-history -- --simple
```

Com Playwright/Chromium instalados: `python -B tests/browser/simple_previous_wordings.py`. Confere 20 dispositivos nas 13 legislações, em 390/1280 px, incluindo CP 215/65/234-A/334, CF 7, CPC 1.042/1.063 e ECA 4/233; texto, fontes, teclado, fechamento e posição de leitura.

Para reprodução integral a partir dos HTMLs, escolher um diretório **ainda inexistente** dentro da mesma árvore experimental:

```powershell
python -B scripts/extract_struck_html.py --output experiments/previous-wordings-simple/reproducao-local
python -B scripts/present_struck_html.py --input experiments/previous-wordings-simple/reproducao-local
python -B scripts/extract_struck_html.py --output experiments/previous-wordings-simple/reproducao-local --verify
python -B scripts/present_struck_html.py --input experiments/previous-wordings-simple/reproducao-local --verify
```

A apresentação salva a fixture anterior no novo diretório antes de atualizar somente a fixture experimental. Essa reprodução cria arquivos locais; não é necessária para mera conferência dos snapshots. Execuções anteriores continuam preservadas e devem ser reproduzidas com o código do commit correspondente, sem reescrever resultados antigos.

## Isolamento e limites

O build normal não incorpora `tests/fixtures/previous-wordings-simple.json`. A flag `--simple` é explícita, desativa a PWA na prévia e é proibida para `dist/`. O lote corrigido tem autorização expressa registrada em `data/previous-wordings/release.json`, vinculada à decisão e amostra em `REDACOES-ANTERIORES-LANCAMENTO.md`. A prévia não concede autorização por si só e os registros continuam `pending`, sem homologação automática.

Tags `s`, `strike`, `del`, CSS inline e seletores simples incorporados são reconhecidos. CSS externo e regras complexas/conflitantes exigem conferência. Espaços são normalizados apenas na apresentação; evidências originais são preservadas. Não se corrigem palavras, acentos ou pontuação por inferência.

A preparação não certifica vigência nem equivalência normativa. Publicação exige validação humana/decisão de governança aplicável e autorização expressa, independentes deste commit experimental.

## Integridade dos arquivos de referência

SHA-256 dos bytes versionados (JSONs preservados com `-text` em `.gitattributes`):

- `experiments/previous-wordings-simple/20261021-associations-corrected/extraction.json`: `efd9d07f9e83be49550c9a398343e33b09a6d95d7aa2199521e9100a021ff892`.
- `experiments/previous-wordings-simple/20261021-associations-corrected/presentation.json`: `eefafc565893cef8f96c239886a9567efcfb2cc1095afa556e3921a5b9c2e332`.
- `experiments/previous-wordings-simple/20261021-associations-corrected/reader.json`: `18cdf5320b330264b79054cac4f36413a8177ea88b52dc0ffe9273c5d7f018f9`.
- `tests/fixtures/previous-wordings-simple.json`: `dcd8571f3a0465255c2521016a19f1c8a2467477ce7081298d1c26a6e980bb32`.
