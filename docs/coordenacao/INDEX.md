# Índice da Coordenação Central — Lexa

**Base técnica conferida:** `main` `84c5bb5c5e28c08376e0bf40cf3f3f4b4fd783cf` (18/10/2026). Os pareceres históricos dos PRs encerrados **não foram incorporados à `main`**: suas cópias administrativas estão no Google Drive e os PRs/commits preservam a origem. A matriz seguinte apresenta o **estado posterior ao saneamento T1–T3**, não o retrato anterior à T3. [Conferência T3](https://docs.google.com/document/d/1qWamkDUgSPCnJs4X245ZyvNrZ06M0JjsIsfg8Vh-OhE/edit).

## Matriz de pareceres e decisões

| PR | Frente | Fase / finalidade | Documento (no PR) | Branch-base | Estado verificado |
|---|---|---|---|---|---|
| [#7](https://github.com/pajaao/lexa./pull/7) | Qualidade | 1A — parecer inicial | `04-qualidade-testes.md` | `main` | Encerrado sem merge; parecer no Drive |
| [#8](https://github.com/pajaao/lexa./pull/8) | Integridade Jurídica | 1A, adendos 1A.1/1A.2 | `02-integridade-juridica.md` | `main` | Encerrado sem merge; parecer no Drive |
| [#9](https://github.com/pajaao/lexa./pull/9) | Engenharia | 1A — arquitetura, SHA, PWA | `01-engenharia.md` | `main` | Encerrado sem merge; parecer no Drive |
| [#10](https://github.com/pajaao/lexa./pull/10) | UX e Produto | 1A — parecer de experiência | `03-ux-produto.md` | `main` | Encerrado sem merge |
| [#11](https://github.com/pajaao/lexa./pull/11) | Qualidade | 1A.1 — correções adversariais | `04-qualidade-testes-fase-1a-1.md` | `correcao/remissoes-fase-1a-1` | Encerrado sem merge; parecer no Drive |
| [#12](https://github.com/pajaao/lexa./pull/12) | Qualidade | 1A.2 — auditoria | `04-qualidade-testes-fase-1a-2.md` | `validacao/remissoes-fase-1a-2` | Encerrado sem merge; parecer no Drive |
| [#13](https://github.com/pajaao/lexa./pull/13) | Coordenação / execução | Fechamento 1A.2 — reprodução relatada | `05-execucao-independente-fechamento-1a-2.md` | `validacao/remissoes-fase-1a-2-fechamento` | Aberto |
| [#14](https://github.com/pajaao/lexa./pull/14) | Qualidade | Fechamento 1A.2 — parecer final | `04-qualidade-testes-fechamento-1a-2.md` | `validacao/remissoes-fase-1a-2-fechamento` | Encerrado sem merge; parecer no Drive |
| [#15](https://github.com/pajaao/lexa./pull/15) | Integridade Jurídica | 1A.3 — P1–P5 e parentéticas | `02-integridade-juridica-fase-1a-3.md` | `validacao/remissoes-fase-1a-2-fechamento` | Encerrado sem merge; parecer no Drive |
| [#16](https://github.com/pajaao/lexa./pull/16) | Coordenação Central | 1A.3 — deliberação metodológica | `00-decisoes-fase-1a-3.md` | `validacao/remissoes-fase-1a-2-fechamento` | Aberto |
| [#17](https://github.com/pajaao/lexa./pull/17) | Engenharia | O1 — auditoria estrutural | `01-engenharia-organizacao-o1.md` | `main` | Encerrado sem merge; parecer no Drive |

Os nomes de arquivo acima descrevem **arquivos de origem nas respectivas branches**, não caminhos presentes na `main`. Os pareceres históricos encerrados sem merge foram preservados no [Drive oficial do projeto](https://drive.google.com/drive/folders/1-UUemCijzHqp0vp1BzpMHATu7hvYzM3x); PRs e commits continuam como evidências técnicas. Os PRs #13 e #16 permanecem sob destinação técnica, e os PRs #18 e #19 seguem propostas de integração documental. O #19 tem base experimental, nunca `main`. Abrir um PR não equivale a incorporá-lo; retargetar #11–#16 para `main` poderia trazer código experimental por ancestralidade.

## Leitura recomendada por assunto
- **Organização:** [parecer O1 no Drive](https://docs.google.com/document/d/1uFfKWgjsr_PI0IGksg2JlgM46ZHfOBJX-cu-x8Jx7dE/edit) ([commit original](https://github.com/pajaao/lexa./blob/8c93c9dd9fabfa4296e1faff417f04a3ab2650da/docs/coordenacao/01-engenharia-organizacao-o1.md)) e [índice geral](../INDEX.md).
- **Engenharia / arquitetura:** [#9](https://github.com/pajaao/lexa./pull/9); **UX e Produto:** [#10](https://github.com/pajaao/lexa./pull/10).
- **Integridade Jurídica:** [#8](https://github.com/pajaao/lexa./pull/8) e [#15](https://github.com/pajaao/lexa./pull/15).
- **Qualidade e reprodução:** [#7](https://github.com/pajaao/lexa./pull/7), [#11](https://github.com/pajaao/lexa./pull/11), [#12](https://github.com/pajaao/lexa./pull/12), [#13](https://github.com/pajaao/lexa./pull/13), [#14](https://github.com/pajaao/lexa./pull/14).
- **Deliberação metodológica:** [#16](https://github.com/pajaao/lexa./pull/16), que conserva `experimental-only` e retém as 30 parentéticas para eventual revisão.

## Destinação documental após T3
- **Pareceres:** consultar o [Drive da Coordenação e das frentes](https://drive.google.com/drive/folders/1-UUemCijzHqp0vp1BzpMHATu7hvYzM3x), inclusive o [parecer O2 de Qualidade](https://docs.google.com/document/d/1Q-biANYskXdOR9fQ4NyqhvFDb9ZrsPtDEyO1u4bCDks/edit), referente ao PR #20 encerrado sem merge.
- **Evidência técnica ainda pendente:** [#13](https://github.com/pajaao/lexa./pull/13); **deliberação metodológica pendente de destinação técnica:** [#16](https://github.com/pajaao/lexa./pull/16).
- **Documentação proposta, ainda não incorporada às bases:** [#18, base `main`](https://github.com/pajaao/lexa./pull/18) e [#19, base experimental](https://github.com/pajaao/lexa./pull/19).
- **Rastreabilidade do saneamento:** [decisão T3](https://docs.google.com/document/d/1GE7kP_sJYZZE-XhC9qEyxpivmMmHcBXuc7_n0NBWCTw/edit), [execução do Lote A](https://docs.google.com/document/d/1HZROTbsgNkSJuEX2_bz5tP2uSaiTnIQOebGhnKVpM8o/edit) e [destinação dos remanescentes](https://docs.google.com/document/d/1DyWRaqs75iSIglF2oOb6k9NRx2tA8lohhV0zki_Phsg/edit).

## Governança
Decisões vinculantes pertencem exclusivamente à Coordenação Central. Pareceres assistidos por IA não são homologação humana; aprovação técnico-documental não ativa remissões. Preservar `docs/coordenacao/decisoes.md` sob responsabilidade exclusiva da Coordenação, caso seja criado. Atualizar esta matriz somente após conferir os estados reais dos PRs e suas bases.
