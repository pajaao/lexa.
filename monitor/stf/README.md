# Monitor das súmulas vinculantes do STF

**Situação atual: automação pausada.** Após falhas de acesso ao STF, o mantenedor optou por atualizar periodicamente a coleção com novos documentos. O workflow tem somente `workflow_dispatch`, sem agenda nem execução por push. As regras abaixo documentam o diagnóstico manual e uma eventual retomada futura. A atualização das legislações do Planalto continua ativa.

Workflow: **Verificar súmulas vinculantes do STF**, em `.github/workflows/monitor-sumulas.yml`.

- Agenda diária: desativada.
- Execução manual: GitHub → Actions → Verificar súmulas vinculantes do STF → Run workflow → main.
- Execução por alterações na main: desativada.
- Branch da proposta: `automation/stf-source-review`; pull request em rascunho, sem merge, aprovação ou implantação automática.

A rotina consulta o índice de súmulas vinculantes e as páginas individuais do portal do STF. Novos números são descobertos pelo índice; não há um limite fixo de 63 entradas no coletor. Há um limite técnico de 300, sujeito a revisão, para manter a execução limitada. O gatilho anterior que regenerava a prévia após incorporar versões do Planalto também está pausado. Os históricos permanecem em arquivos separados. O monitor é independente do Planalto: uma indisponibilidade do STF não impede a rotina das seis legislações.

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

Falhas HTTP, inclusive 403 no navegador, bloqueios, páginas ambíguas, números ausentes e suspeita de truncamento impedem toda a proposta. Entradas conhecidas não são apagadas automaticamente quando desaparecem do índice. Uma súmula identificada como cancelada não pode perder essa indicação silenciosamente: tal divergência exige revisar o extrator e a fonte. Situações não são inferidas a partir de citações em outros precedentes, nem ausência é tratada como cancelamento.

O coletor exige um título inequívoco e delimitação entre enunciado, seções de aplicação e fim do conteúdo. Compara também o volume do material de aplicação com a edição anterior, bloqueando reduções suspeitas para revisão manual. Mudanças no formato do portal podem, portanto, exigir ajuste em `scripts/check_stf_sources.py`; não remova as validações para aceitar uma página de erro. Alterações no processamento exigem incrementar `CONVERTER` e revisar a proposta.

Coletas semanticamente iguais conservam datas e arquivos anteriores, sem PRs apenas por mudança de horário ou do menu do portal. O Actions usa Chromium com JavaScript habilitado e um contexto temporário próprio, por meio de `scripts/stf_browser.py` e da versão fixada em `scripts/requirements-stf.txt`. Não usa o navegador pessoal do usuário. Requisições e redirecionamentos ficam restritos aos hosts oficiais configurados do STF, sem ignorar erros de TLS. Respostas 403 são rejeitadas; não há resolução automática de CAPTCHA nem técnicas de disfarce do navegador. O modo HTTP de diagnóstico continua disponível, compartilhando o cliente HTTPS do Planalto sem ampliar os destinos aceitos pela rotina das legislações.

Os testes de HTML usam fixtures sintéticas e não comprovam acesso real ao STF. O proxy do ambiente de desenvolvimento bloqueia o STF, e a tentativa com o cliente HTTP no GitHub Actions também retornou 403. A execução com Chromium é uma tentativa adicional e ainda precisa validar acesso e formato no servidor do GitHub. Se falhar, consulte a etapa de coleta, `report.json` e `access-diagnostic.json` no artefato: o diagnóstico inclui o endereço, o status HTTP, o título, a versão do navegador e os hosts de recursos bloqueados. Quando possível, `access-diagnostic.html` e `access-diagnostic.png` mostram a resposta recebida. A instalação ou a inicialização do navegador também podem falhar antes de haver uma página para capturar. A base atual permanece intacta e não há fallback para fontes de terceiros.

O monitor não certifica vigência nem faz revisão jurídica. “Sem indicação especial no título da fonte” não significa confirmação de que um enunciado está vigente.

## Executar com navegador local

Para testar em uma máquina autorizada com acesso ao STF, instale `python -m pip install -r scripts/requirements-stf.txt` e `python -m playwright install --with-deps chromium`; execute `python scripts/check_stf_sources.py --transport browser`. O contexto de navegação é novo a cada execução e não aproveita logins, cookies ou o perfil do navegador pessoal. `--transport http` mantém a consulta por curl para diagnóstico. Ambos os modos aplicam as mesmas validações antes de gerar candidatos.
