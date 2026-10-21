# Extrator HTML — referência técnica

O fluxo ativo, seus limites e comandos estão em [REDACOES-ANTERIORES.md](REDACOES-ANTERIORES.md).

## Núcleo compartilhado

`scripts/extract_previous_html.py` fornece `EvidenceHTML`, `decode`, `unit`, `split_notes` e `inspect_source`. Reutiliza `OfficialHTML` e o reconhecimento de artigo do importador existente, sem executar coleta ou rede. Não depende de PyMuPDF. Mantém texto, runs, links, âncoras, localização e SHA-256.

O preparador inicial `prepare_document()` e seu CLI também permanecem nesse arquivo para reprodução e testes dos resultados antigos. Exigem anterior e substituta e **não definem o escopo atual**. Não executar seu CLI com `--preview-fixture` para atualizar o conjunto consolidado.

O fluxo atual utiliza `previous_blocks()` em `scripts/prepare_previous_only.py`. Não exige substituta ou referência normativa, e mantém os casos não associados nas exclusões. A atualização aditiva de CF/CPP/CPC usa `scripts/refresh_previous_html_sources.py`. O comando de preparação em lote recusa fontes diferentes de sua base registrada antes de escrever.

## Evidências anteriores

`experiments/html-history/results/` e `previous-only/` são fotografias de execuções anteriores, com seus próprios manifestos. Não sobrescrever para atualizar contagens. Para fontes substituídas, resolver a edição pelo hash com `scripts/saved_html_source.py` e os arquivos em `source-archives/`.

Fontes e evidências com hash têm conversão de quebras de linha desativada em `.gitattributes`. Isso mantém os bytes após versionamento; não certifica completude documental nem validade jurídica.

## Reinícios documentados

O preparador atual ativa `documented_restarts=True`: um reinício exige artigo já observado, cabeçalho estrutural nativo e âncora compatível; numeração ou nota isolada não bastam. Citações em `blockquote` não avançam a numeração nativa nem fornecem pais a unidades subsequentes. O limite próprio do ADCT é reconhecido antes desse filtro. A CLT distingue o decreto de aprovação da Consolidação.

`inspect_source()` mantém por padrão o modo histórico para reproduzir fotografias anteriores. `refresh_previous_html_sources.py --reprocess --codes ...` compara ambos os modos, impede perda de registros antes reconhecidos e acrescenta somente novas identidades textuais. Não substitui textos, notas, revisão ou evidências existentes.

## Correção de identidade normativa

Um reinício documentado não demonstra equivalência jurídica. O fluxo atual exclui da associação com o leitor toda a Parte Geral antiga do CP, mesmo quando o reinício posterior tem cabeçalho/âncora. A opção interna `allow_unmapped_general_part` existe apenas para reproduzir a execução histórica anterior à correção; não é exposta como opção de preparação. A reavaliação dirigida compara ID da ocorrência, texto, notas, fonte e evidência completos, nunca apenas o número ou igualdade textual. Os registros retidos não recebem notas de outras ocorrências.
