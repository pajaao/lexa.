# Extrator HTML — responsabilidades

O fluxo corrente está em [Redações anteriores — HTML simples](REDACOES-ANTERIORES-SIMPLES.md).

- `scripts/extract_struck_html.py`: identificação documental e extração de texto riscado, notas, localização e evidências dos 13 HTMLs locais.
- `scripts/present_struck_html.py`: associação ao dispositivo documental e preparação da fixture experimental, preservando exclusões e estados `pending`.
- `scripts/prepare_previous_release.py --verify`: reprodução do lote corrigido e conferência da distribuição e dos hashes, sem modificar a autorização de lançamento.
- `scripts/extract_previous_html.py`: parser e utilitários compartilhados pelos fluxos. Seu CLI antigo não é o preparador corrente; preservar seus bytes, fixados em manifestos históricos.

`prepare_previous_only.py`, `refresh_previous_html_sources.py`, `revalidate_previous_associations.py` e os snapshots de `experiments/html-history/` são dependências de reprodução e regressão dos experimentos anteriores. Seus critérios não substituem os da implementação corrente. Consulte o [registro histórico](REDACOES-ANTERIORES.md) somente para reproduzir essas execuções.

Nenhum desses fluxos reconstrói a vigência jurídica. A autorização de consulta e os estados documentais são independentes; ver [lançamento](REDACOES-ANTERIORES-LANCAMENTO.md).
