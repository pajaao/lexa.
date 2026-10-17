# Revisão de carregamento por norma

A refatoração separa a base jurídica do shell do Lexa, sem alterar fontes ou dados gerados. Depende das correções da branch `melhorias/interface-e-seguranca`; revisar e incorporar esse conjunto primeiro.

## Medição local

Cinco visitas novas por compilação, Chromium, largura 375 px, CPU com fator 4, service worker bloqueado, sem cache prévio e com arquivos servidos por HTTP local. Medida: tempo de navegação até os 14 cartões estarem presentes no DOM. Não é uma previsão para redes reais ou todos os aparelhos.

| Medida | Antes (`53bc3f0`) | Depois |
| --- | --- | --- |
| HTML em bytes | 9.059.856 | aproximadamente 135.000 |
| Visitas em ms | 4728, 3611, 3781, 2793, 3057 | 589, 576, 520, 510, 430 |
| Mediana em ms | 3611 | 520 |
| Busca “dignidade” | 52 entradas / 12 coleções | Mesmas entradas e ordem |

Reprodução: `npm run build` e `python3 tests/browser/performance.py`. Para medir uma compilação anterior, passe o caminho do diretório com seus arquivos como argumento. O limite de 300 KB é verificado por `npm test`.

## Comportamento e limites

- Home usa catálogo e contagens; leitor carrega apenas a norma escolhida. Favoritos carregam as normas salvas e o histórico tem arquivo próprio.
- Primeira busca textual ou referência sem sigla carrega o conjunto; índices são montados sob demanda. Há indicador acessível, limite de concorrência, repetição após falha e descarte de respostas de páginas/consultas anteriores.
- A primeira instalação offline ainda transfere a base completa, agora em arquivos separados. Aguarde a confirmação de preparo. A economia nas atualizações vem da reutilização dos arquivos imutáveis de normas inalteradas.
- Shell, catálogo, ícones e todos os JSONs têm hash verificado na instalação. Um arquivo ausente ou adulterado rejeita a instalação inteira, apaga o cache parcial e preserva a edição ativa. Não há ativação sem consentimento.
- A prévia precisa do diretório `dist/` inteiro e de HTTP; abrir somente o HTML por `file:` não é mais suportado. Não há dependências npm novas.

## Verificação

`npm test` cobre geração, catálogo, hashes, preservação dos JSONs após alteração exclusiva de CSS, escape HTML, referências e busca. A suíte Python de importadores e monitores permanece obrigatória.

As verificações Playwright cobrem leitura, favoritos, cópia, hierarquia em todas as coleções, busca, interface móvel, carga seletiva, integridade/retry e PWA. O teste da PWA simula modo offline, atualização consentida, zero downloads dos JSONs inalterados na atualização do shell, shell indisponível e JSON adulterado; confirma a preservação de favoritos, preferências e caches de outros projetos.

O catálogo jurídico, os PDFs, as capturas oficiais e os históricos gerados não foram editados. Status de súmulas, endereço e inclusão de novas normas continuam sendo decisões do mantenedor.
