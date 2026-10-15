# Monitoramento das fontes oficiais

Esta implementação prepara **verificação diária e propostas de revisão**. Ela ainda não está ativa no GitHub e **não substitui automaticamente os artigos publicados no leitor**. O site continua usando a extração dos PDFs recebidos. A comparação e conversão de uma coleta HTML real para uma nova edição do leitor é uma etapa posterior, que depende de validar a coleta fora deste ambiente.

## O que está implementado

- Consulta HTTPS às seis páginas do Planalto em `sources.json`, com verificação TLS e destinos restritos ao Planalto. Não precisa de chave ou token para baixar as páginas públicas.
- Detecção de mudanças no texto, nas redações riscadas e em estilos de exclusão, ignorando diferenças simples de espaços e marcação visual.
- Verificação da identidade da legislação, tamanho mínimo e presença dos artigos-base, incluindo ADCT separado. Páginas de erro ou extrações incompletas fazem a execução falhar.
- Referências versionadas em `monitor/official/*.json`. A primeira coleta fica explicitamente identificada; não é considerada equivalente à edição dos PDFs.
- Evidências, hashes, diferenças textuais e relatório de cada execução em `monitor/run/`. Downloads são tratados como dados, nunca executados. A pasta é gerada e seus arquivos de evidência anteriores são substituídos a cada execução.
- Nenhum avanço das referências quando alguma das seis fontes falha. Datas de coleta em relatórios não alteram arquivos versionados em dias sem mudança de conteúdo.
- Propostas em rascunho na branch reservada `automation/official-source-review`, sem aprovação ou merge automático. O workflow gerencia apenas essa branch; não a use para trabalho manual.

**Aceitar uma proposta deste monitor atualiza a referência de comparação, não o conteúdo do site.** A data da coleta também não comprova a data de início de vigência. Comparar textos consolidados detecta o que a fonte incorporou; não equivale a acompanhar todas as publicações do Diário Oficial.

## Ativar no GitHub

1. Envie o projeto e `.github/workflows/monitor-legislation.yml` para a branch padrão de `pajaao/siteteste`. Os arquivos desta sessão ainda não foram enviados. Publicar o ambiente na nuvem não envia commits ao GitHub.
2. No repositório, habilite **Actions**. Em **Settings → Actions → General**, a política deve permitir os actions utilizados e a criação de pull requests pelo `GITHUB_TOKEN`. Se houver uma política da organização, ela também precisa permitir essas operações. O token é fornecido pelo GitHub durante a execução; não coloque tokens no código ou no chat.
3. Em **Actions → Verificar fontes da legislação**, use **Run workflow** para testar a primeira coleta. Ainda não foi comprovado acesso ao Planalto a partir do runner do GitHub. Se a fonte continuar indisponível, o job falhará com evidências e não registrará uma referência válida.
4. Confira os seis resultados e os artefatos. A primeira proposta precisa ser comparada com os PDFs que sustentam o site; não marque os textos como atualizados apenas por aceitar a referência.
5. Depois de ativado na branch padrão, o agendamento tentará executar diariamente por volta de **06:17 em São Paulo** (09:17 UTC). O GitHub pode atrasar tarefas agendadas; não é um horário garantido.

O workflow usa o token do GitHub com `contents: write` e `pull-requests: write` para manter a branch de revisão. Usa actions de checkout, Python, upload de artefatos e criação de PR. Não envia mensagens por Slack ou email; notificações de falha seguem as configurações de notificações do próprio GitHub.

## Conferir uma alteração

1. Abra a proposta e a execução correspondente. Confirme que a coleta mais recente passou para todas as fontes e leia as diferenças nos JSONs e nos artefatos `.diff.txt`.
2. Confira redações anteriores, revogações, notas de alterações e regras de início de vigência. Mudanças de CSS de exclusão também exigem revisão do HTML de origem, disponível como `.html.txt` no artefato.
3. Para atualizar o leitor nesta fase, obtenha o PDF consolidado correspondente e siga o procedimento de reimportação em `../README.md`. Atualize a edição e a data de referência sem confundi-las com a data da coleta. Revise o diff, rode os testes e gere o HTML antes de publicar.
4. Preserve a versão anterior para permitir reversão. Os originais e hashes ficam em `sources/`; o histórico dependerá de os commits do projeto serem enviados e mantidos no GitHub.

Um futuro importador HTML poderá preparar também os textos do leitor na mesma proposta, após validarmos a estrutura das páginas reais e compararmos o resultado com os PDFs. O monitor atual deliberadamente não anuncia essa conversão como implementada.

## Executar e testar localmente

Python 3.12 ou superior, somente biblioteca padrão:

```sh
python3 -m unittest discover -s scripts -p 'test_monitor.py' -v
python3 scripts/check_official_sources.py
```

`--only civil` (ou `penal`, `cpc`, `cdc`, `ctn`, `cf`) limita uma verificação manual. O workflow agendado sempre consulta as seis fontes. O comando retorna código 1 se houver falha e mantém as referências anteriores. Os testes usam respostas simuladas, cenários de falha e HTML sintético construído com o corpus real extraído dos PDFs; eles não comprovam conectividade externa.

Os artefatos do GitHub ficam disponíveis por 30 dias. Referências aceitas permanecem no histórico Git. Monitore falhas em Actions; um job sem sucesso não significa “nenhuma mudança na lei”.
