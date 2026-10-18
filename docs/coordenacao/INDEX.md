# Índice da Coordenação Central — Lexa

**Corte verificado:** 18/10/2026 · `main` `84c5bb5c5e28c08376e0bf40cf3f3f4b4fd783cf`. **Nenhum dos PRs #7–#17 estava incorporado à `main` na consulta.** Os documentos estão nas branches dos respectivos PRs; links externos apontam diretamente para cada PR. Este índice não reproduz seus conteúdos.

## Matriz de pareceres e decisões

| PR | Frente | Fase / finalidade | Documento (no PR) | Branch-base | Estado verificado |
|---|---|---|---|---|---|
| [#7](https://github.com/pajaao/lexa./pull/7) | Qualidade | 1A — parecer inicial | `04-qualidade-testes.md` | `main` | Aberto |
| [#8](https://github.com/pajaao/lexa./pull/8) | Integridade Jurídica | 1A, adendos 1A.1/1A.2 | `02-integridade-juridica.md` | `main` | Aberto |
| [#9](https://github.com/pajaao/lexa./pull/9) | Engenharia | 1A — arquitetura, SHA, PWA | `01-engenharia.md` | `main` | Aberto |
| [#10](https://github.com/pajaao/lexa./pull/10) | UX e Produto | 1A — parecer de experiência | `03-ux-produto.md` | `main` | **Aberto, draft** |
| [#11](https://github.com/pajaao/lexa./pull/11) | Qualidade | 1A.1 — correções adversariais | `04-qualidade-testes-fase-1a-1.md` | `correcao/remissoes-fase-1a-1` | Aberto |
| [#12](https://github.com/pajaao/lexa./pull/12) | Qualidade | 1A.2 — auditoria | `04-qualidade-testes-fase-1a-2.md` | `validacao/remissoes-fase-1a-2` | Aberto |
| [#13](https://github.com/pajaao/lexa./pull/13) | Coordenação / execução | Fechamento 1A.2 — reprodução relatada | `05-execucao-independente-fechamento-1a-2.md` | `validacao/remissoes-fase-1a-2-fechamento` | Aberto |
| [#14](https://github.com/pajaao/lexa./pull/14) | Qualidade | Fechamento 1A.2 — parecer final | `04-qualidade-testes-fechamento-1a-2.md` | `validacao/remissoes-fase-1a-2-fechamento` | Aberto |
| [#15](https://github.com/pajaao/lexa./pull/15) | Integridade Jurídica | 1A.3 — P1–P5 e parentéticas | `02-integridade-juridica-fase-1a-3.md` | `validacao/remissoes-fase-1a-2-fechamento` | Aberto |
| [#16](https://github.com/pajaao/lexa./pull/16) | Coordenação Central | 1A.3 — deliberação metodológica | `00-decisoes-fase-1a-3.md` | `validacao/remissoes-fase-1a-2-fechamento` | Aberto |
| [#17](https://github.com/pajaao/lexa./pull/17) | Engenharia | O1 — auditoria estrutural | `01-engenharia-organizacao-o1.md` | `main` | Aberto |

Todos os caminhos acima são relativos a `docs/coordenacao/` **na respectiva branch**, não arquivos presentes na `main`. Abrir um PR não equivale a incorporá-lo; retargetar #11–#16 para `main` poderia trazer código experimental por ancestralidade.

## Leitura recomendada por assunto
- **Organização:** [parecer O1](https://github.com/pajaao/lexa./blob/8c93c9dd9fabfa4296e1faff417f04a3ab2650da/docs/coordenacao/01-engenharia-organizacao-o1.md) e [índice geral](../INDEX.md).
- **Engenharia / arquitetura:** [#9](https://github.com/pajaao/lexa./pull/9); **UX e Produto:** [#10](https://github.com/pajaao/lexa./pull/10).
- **Integridade Jurídica:** [#8](https://github.com/pajaao/lexa./pull/8) e [#15](https://github.com/pajaao/lexa./pull/15).
- **Qualidade e reprodução:** [#7](https://github.com/pajaao/lexa./pull/7), [#11](https://github.com/pajaao/lexa./pull/11), [#12](https://github.com/pajaao/lexa./pull/12), [#13](https://github.com/pajaao/lexa./pull/13), [#14](https://github.com/pajaao/lexa./pull/14).
- **Deliberação metodológica:** [#16](https://github.com/pajaao/lexa./pull/16), que conserva `experimental-only` e retém as 30 parentéticas para eventual revisão.

## Governança
Decisões vinculantes pertencem exclusivamente à Coordenação Central. Pareceres assistidos por IA não são homologação humana; aprovação técnico-documental não ativa remissões. Preservar `docs/coordenacao/decisoes.md` sob responsabilidade exclusiva da Coordenação, caso seja criado. Atualizar esta matriz somente após conferir os estados reais dos PRs e suas bases.
