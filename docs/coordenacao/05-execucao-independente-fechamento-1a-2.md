# Parecer de execução independente — fechamento da Fase 1A.2

**Data:** 18/10/2026  
**Responsável pela execução:** Coordenação Central, com apoio do ChatGPT  
**Objeto:** execução dos três comandos solicitados pela frente de Qualidade e Testes  
**Base:** `validacao/remissoes-fase-1a-2-fechamento` (ZIP da branch fornecido pelo responsável do projeto)  
**Natureza:** verificação computacional independente da execução relatada pelo agente de implementação; **não** é auditoria jurídica humana.

## Ambiente e procedimento

- Ambiente isolado, extração temporária do ZIP, sem alteração no repositório remoto nem nos artefatos aprovados.
- Python **3.13.5**; Node.js **v22.16.0**.
- Execução no diretório-raiz extraído do projeto.
- Diretório temporário de reprodução: `/tmp/lexa-closure-repro`.
- A execução foi realizada após o recebimento do ZIP nesta conversa, não inferida dos registros de testes presentes no Git.

## Comandos e resultados efetivamente obtidos

### 1. Testes unitários do fechamento

```sh
python -m unittest discover -s tests -p 'test_remissions_closure.py'
```

**Resultado:** exit code 0; **10 testes aprovados**, sem falhas.

```text
Ran 10 tests in 2.767s

OK
```

### 2. Reprodução de artefatos

```sh
node scripts/reproduce_remissions_closure.mjs /tmp/lexa-closure-repro
```

**Resultado:** exit code 0. Saída textual observada:

```text
Two runs identical to each other and to all five approved artifacts.
```

### 3. Verificação com snapshot da população

```sh
python scripts/verify_remissions_closure.py docs/remissoes/fase-1a-2 --snapshot /tmp/lexa-closure-repro/snapshot.json
```

**Resultado:** exit code 0; saída JSON analisada, `ok: true`, `divergences: []`. Para facilitar a leitura, a saída foi redirecionada a um arquivo temporário e seus campos de resultado foram exibidos separadamente; o comando Python e seus parâmetros são os mesmos solicitados.

Contagens observadas:

| Métrica | Quantidade |
|---|---:|
| Arestas | 329 |
| Ocorrências | 272 |
| Participações ocorrência–aresta | 353 |
| Rejeições amostradas | 354 |
| Registros do CSV de revisão humana | 683 |
| Estratos | 203 |
| Divergências apontadas | **0** |

## Conclusão técnica

**Os três comandos solicitados passaram em execução separada do agente de implementação**, utilizando cópia integral da branch enviada pelo usuário. Não foram detectadas divergências nas invariantes verificadas nem na reprodução dos cinco artefatos.

**Limites:** a verificação utiliza o corpus e a população produzidos pelo pipeline incluído na própria cópia, de modo que não certifica a autenticidade externa das edições, a correção semântica de cada remissão ou a completude das referências do acervo. Não foi executada revisão jurídica humana das 329 arestas; tampouco foram executadas suítes gerais ou testes adicionais de aparelho físico. Este parecer confirma exclusivamente os três comandos e os resultados explicitados.

**Encaminhamento:** frente de Qualidade e Testes deve revisar este registro e decidir sobre o aceite técnico documental do fechamento. Permanecem `experimental-only`, ausência de ativação no leitor e a exigência de decisão central expressa antes de mudanças na política ou publicação.

**Alterações permitidas neste PR:** apenas este parecer. Sem merge, deploy ou mudança em código, inventários, legislação e decisões humanas.
