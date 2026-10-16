# Monitor das súmulas vinculantes do STF

Workflow: **Verificar súmulas vinculantes do STF**, em `.github/workflows/monitor-sumulas.yml`.

- Agenda diária: `47 9 * * *`, aproximadamente 06:47 em São Paulo (UTC-3).
- Execução manual: GitHub → Actions → Verificar súmulas vinculantes do STF → Run workflow → main.
- Também executa quando a configuração, os importadores ou a interface relevante mudam na main.
- Branch da proposta: `automation/stf-source-review`; pull request em rascunho, sem merge, aprovação ou implantação automática.

A rotina consulta o índice de súmulas vinculantes e as páginas individuais do portal do STF. Novos números são descobertos pelo índice; não há um limite fixo de 63 entradas no coletor. Há um limite técnico de 300, sujeito a revisão, para manter a execução limitada. O workflow também acompanha a incorporação das versões do Planalto para regenerar a prévia sobre a main atual, pois os dois monitores produzem `index.html`. Os históricos permanecem em arquivos separados. O monitor é independente do Planalto: uma indisponibilidade do STF não impede a rotina das seis legislações.

## Dados e revisão

O PDF fornecido e `sumulas-content.js` ficam arquivados. Somente após mesclar uma proposta, `official-sumulas.js` passa a fornecer a edição do leitor. A primeira coleta oficial estabelece uma referência inicial no histórico, sem apresentar a migração entre PDF e HTML como uma nova alteração jurídica. O relatório da proposta compara essa coleta ao PDF para revisão humana.

As versões seguintes comparam enunciados, situações registradas, precedentes, jurisprudência e observações. As alterações aparecem em `sumulas-updates.js`, integrado à página Atualizações com filtros e comparação antes/depois. Cada versão inclui a situação e o material de aplicação; a tela identifica as entradas como súmulas vinculantes.

O bot prepara:

- `index.json`: índice validado e hash da coleção;
- `items/<número>.json`: texto estruturado, link individual, hashes e data da coleta de cada entrada;
- `official-sumulas.js`: edição candidata para o leitor;
- `sumulas-updates.js`: histórico independente, preservando o histórico das legislações;
- `index.html`: prévia autocontida com a edição candidata.

Os artefatos `verificacao-sumulas-stf-<execução>` e `previa-sumulas-stf-<execução>` ficam disponíveis por 30 dias. O primeiro contém `report.json`, o texto da proposta e o HTML bruto coletado; esse HTML é evidência, não é executado no site. A prévia mostra os dados extraídos e escapados. Confira enunciados, situações, precedentes e links antes de mesclar. Mesclar o PR incorpora os arquivos; a publicação depende da hospedagem configurada.

## Falhas e estabilidade

Falhas HTTP, bloqueios, páginas ambíguas, números ausentes e suspeita de truncamento impedem toda a proposta. Entradas conhecidas não são apagadas automaticamente quando desaparecem do índice. Uma súmula identificada como cancelada não pode perder essa indicação silenciosamente: tal divergência exige revisar o extrator e a fonte. Situações não são inferidas a partir de citações em outros precedentes, nem ausência é tratada como cancelamento.

O coletor exige um título inequívoco e delimitação entre enunciado, seções de aplicação e fim do conteúdo. Compara também o volume do material de aplicação com a edição anterior, bloqueando reduções suspeitas para revisão manual. Mudanças no formato do portal podem, portanto, exigir ajuste em `scripts/check_stf_sources.py`; não remova as validações para aceitar uma página de erro. Alterações no processamento exigem incrementar `CONVERTER` e revisar a proposta.

Coletas semanticamente iguais conservam datas e arquivos anteriores, sem PRs apenas por mudança de horário ou do menu do portal. A rotina compartilha o cliente HTTPS com o Planalto, mas usa uma lista explícita de hosts do STF, sem ampliar os destinos aceitos pelo monitor das legislações. TLS e validação de redirecionamentos permanecem habilitados.

Os testes de HTML usam fixtures sintéticas e não comprovam acesso real ao STF. O acesso permanece bloqueado pelo proxy do ambiente de desenvolvimento; a primeira execução no GitHub Actions é a validação da conectividade e do formato real da fonte. Se falhar, consulte a etapa de coleta e o relatório antes de ajustar o extrator. A base atual permanece intacta e não há fallback para fontes de terceiros.

O monitor não certifica vigência nem faz revisão jurídica. “Sem indicação especial no título da fonte” não significa confirmação de que um enunciado está vigente.
