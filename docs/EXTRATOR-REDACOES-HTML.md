# Extrator HTML — referência técnica

O fluxo ativo, seus limites e comandos estão em [REDACOES-ANTERIORES.md](REDACOES-ANTERIORES.md).

## Núcleo compartilhado

`scripts/extract_previous_html.py` fornece `EvidenceHTML`, `decode`, `unit`, `split_notes` e `inspect_source`. Reutiliza `OfficialHTML` e o reconhecimento de artigo do importador existente, sem executar coleta ou rede. Não depende de PyMuPDF. Mantém texto, runs, links, âncoras, localização e SHA-256.

O preparador inicial `prepare_document()` e seu CLI também permanecem nesse arquivo para reprodução e testes dos resultados antigos. Exigem anterior e substituta e **não definem o escopo atual**. Não executar seu CLI com `--preview-fixture` para atualizar o conjunto consolidado.

O fluxo atual utiliza `previous_blocks()` em `scripts/prepare_previous_only.py`. Não exige substituta ou referência normativa, e mantém os casos não associados nas exclusões. A atualização aditiva de CF/CPP/CPC usa `scripts/refresh_previous_html_sources.py`. O comando de preparação em lote recusa fontes diferentes de sua base registrada antes de escrever.

## Evidências anteriores

`experiments/html-history/results/` e `previous-only/` são fotografias de execuções anteriores, com seus próprios manifestos. Não sobrescrever para atualizar contagens. Para fontes substituídas, resolver a edição pelo hash com `scripts/saved_html_source.py` e os arquivos em `source-archives/`.

Fontes e evidências com hash têm conversão de quebras de linha desativada em `.gitattributes`. Isso mantém os bytes após versionamento; não certifica completude documental nem validade jurídica.
