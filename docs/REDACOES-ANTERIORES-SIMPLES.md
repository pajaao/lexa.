# Redações anteriores — fluxo HTML simples

Duas responsabilidades, sem reconstrução legislativa:

1. `scripts/extract_struck_html.py` lê os 13 HTMLs locais, identifica unidades integralmente riscadas, separa notas/links e conserva o HTML bruto, localização e hash. Reutiliza somente decodificação, captura de evidência e reconhecimento de marcadores do código anterior.
2. `scripts/present_struck_html.py` associa à prévia quando o contexto documental é compatível e o dispositivo no leitor contém o mesmo texto ou um caput não riscado do mesmo grupo documental. Número igual sozinho não autoriza associação. Notas são as da ocorrência extraída, sem empréstimo de outras ocorrências.

A Parte Geral antiga do CP, o decreto de aprovação da CLT e citações ficam fora do vínculo automático. CF e ADCT têm identificações distintas. Não se exigem substitutas para extrair um texto; a evidência adicional só condiciona sua associação automática ao leitor. Trechos não associados permanecem integralmente na extração.

## Resultado conjunto das 13 fontes

Execução final: `experiments/previous-wordings-simple/20261021-complete/`.

- 3.188 **blocos** com alguma marcação riscada (não quantidade de tags nem versões completas).
- 2.496 unidades anteriores extraídas integralmente.
- 1.903 associadas a 646 dispositivos, todas `pending`.
- 593 extraídas sem associação automática, incluindo dez duplicações documentais.
- 692 blocos sem unidade completa aproveitável; 1.285 blocos ao todo fora da apresentação.

Motivos de exclusão podem se sobrepor. Contexto incompatível, ausência de correspondência documental, fragmentos mistos/incompletos, unidade não identificada e marcadores de veto/revogação permanecem registrados por ocorrência em `presentation.json` e `extraction.json`. Civil e CDC não tiveram unidades aproveitáveis; isso não demonstra ausência de alterações.

## Reprodução e prévia

Requisitos: Python 3.12+ e Node 22+. Os testes Python não exigem pacotes externos.

```powershell
python -B scripts/extract_struck_html.py --output experiments/previous-wordings-simple/20261021-complete --verify
python -B scripts/present_struck_html.py --input experiments/previous-wordings-simple/20261021-complete --verify
python -B -m unittest discover -s tests/python -p test_simple_previous_wordings.py
npm test
$env:PORT='3012'
npm run preview:legislative-history -- --simple
```

Para preparar uma nova execução, selecionar diretório novo e omitir `--verify` nos dois primeiros comandos, na mesma ordem. A extração não sobrescreve evidências; a apresentação preserva a fixture anterior dentro da nova execução antes de substituir apenas a fixture simples. Os dados antigos não são mesclados à nova prévia. Não executar nova preparação para mera conferência.

Navegador (Playwright/Chromium previamente instalados): `python -B tests/browser/simple_previous_wordings.py`. Confere 11 legislações em 390/1280 px, texto integral, fontes, teclado e continuidade da leitura.

Produção não lê `previous-wordings-simple.json`; `--simple` é explícito, desativa PWA e é proibido para `dist/`. A interface existente é reutilizada. As flags antigas continuam disponíveis para reprodução, sem determinar os dados da prévia simples.

## Limitações

Tags `s`, `strike`, `del`, CSS inline e seletores simples de classe/id/tag em estilos incorporados são reconhecidos. Seletores complexos, condicionais ou cascata conflitante exigem conferência; CSS externo não é interpretado. As 13 fontes finais não contêm regras incorporadas de texto riscado. Quebras/espaços são normalizados no texto de apresentação, com original e runs preservados. Não se corrigem palavras, acentos ou pontuação por inferência.

Não se afirma completude nem equivalência normativa entre reorganizações. Datas de vigência, cadeias de alterações e versões integrais não são reconstruídas. Todo conteúdo continua pendente de homologação jurídica humana independente e autorização de publicação.
