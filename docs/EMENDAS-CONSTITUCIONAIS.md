# Biblioteca de Emendas Constitucionais

Implementação local candidata. A validação técnica das 141 ECs não constitui
homologação jurídica. As seis Emendas de Revisão não integram esta biblioteca.
O build comum permanece sem as ECs enquanto `data/amendments/release.json`
mantiver a publicação bloqueada.

## Reprodução e fontes

Requisitos: Node >=22, Python >=3.12; Playwright/Chromium já utilizados pelo
projeto para a verificação independente de novas propostas.

```sh
node scripts/preview-amendments.mjs
node --test tests/node/amendments.test.js
python -m unittest discover -s tests -p test_amendments.py
python tests/browser/amendments.py
```

A prévia usa somente localhost, porta 3044 (sobrescrevível por `PORT`). Nunca
grave um build candidato em `dist/`: o empacotador recusa essa operação.
`LEXA_PYTHON` permite indicar o Python utilizado na geração dos vínculos.

`data/amendments/candidate/catalog.json` identifica documentos, hashes e estados
`pending`. Cada documento possui blocos literais e runs, artigos próprios,
citações constitucionais, ementa, preâmbulo, fecho, metadados e ressalvas.
`originals/` preserva os bytes da Câmara; `evidence/` preserva a revalidação
anterior e a origem no acervo independente. Nenhum arquivo original externo
foi alterado. O preparo inicial é reproduzível por:

```sh
python scripts/prepare_amendments.py --source D:/Projetos/Extracao-Emendas-Constitucionais
```

Esse comando prepara uma candidata a partir do acervo tecnicamente validado;
não o execute para sobrescrever uma candidata com revisões posteriores.

## Vínculos documentais

O build candidato executa `generate_amendment_links.py`, sem rede. O índice não
é uma tabela manual. Cada nota modificadora da CF/ADCT precisa de número/ano
correspondentes, snapshot constitucional compatível, unidade identificável e
comando modificador corroborado na publicação original da EC.

`candidate/links-audit.json` registra confirmação, incerteza, exclusão, sintaxe
não reconhecida e unidades originais não confirmadas nas notas da edição.
Os três controles preservam 31 notas para a EC58, 79 para a EC103 e 3 para a
EC115. A exceção “Emenda Constituição Constitucional” é aceita exclusivamente
para a EC58/2009. “Vide”, menções sem operação modificadora, títulos sem artigo
e marcações mistas não são transformados em links automáticos.

Notas em texto riscado têm estado próprio. Não são inseridas na consulta
principal; a relação na EC identifica referências a redações anteriores.
O índice não certifica vigência, não garante completude histórica e não
reconstrói dispositivos. A navegação utiliza artigos existentes, sem novas
âncoras de inciso/parágrafo. Para reproduzir o relatório integral:

```sh
python scripts/generate_amendment_links.py --output test-results/ec-links-audit.json
```

## Manutenção futura

1. `python scripts/maintain_amendments.py discover --collect --output monitor/run/amendments`
   consulta o quadro oficial independentemente de mudanças na CF. Preserva o
   índice, identifica números realmente listados e prepara até dez propostas
   por execução. Se o Planalto não oferecer ligação inequívoca para a publicação
   original da Câmara, registra `original_source_required`; não inventa URL.
2. Nessa exceção, forneça uma publicação original oficial:
   `python scripts/maintain_amendments.py prepare --number N --original-url URL --output monitor/run/amendments/ec-N`.
   `--file` permite reproduzir com HTML já preservado, sem afirmar coleta HTTP.
3. A proposta inclui HTML original, hash, texto estruturado, verificações e
   `review.json`. A conferência Chromium independente compara texto e ordem,
   com scripts/rede do HTML bloqueados. Identidade, fecho, codificação e sequência
   de artigos devem passar. Estruturas extraordinárias exigem revisão técnica;
   um resultado automático não demonstra sozinho classificação jurídica correta.
4. Após revisão humana **técnica** documentada, preencher em `review.json`
   `technicalApproved`, `reviewer` e `evidence`, mantendo `publicationAuthorized:false`.
   Executar `incorporate-candidate DIRETORIO_DA_PROPOSTA` inclui a EC como
   `pending` e regenera os vínculos. Não publica e não sobrescreve EC existente.
5. Conferir o diff e os testes. Homologação jurídica e autorização de publicação
   são decisões posteriores e independentes. O bloqueio de release exige registro
   expresso de revisão jurídica e números aprovados; não é alterado pelo monitor.

O workflow `monitor-amendments.yml` apenas guarda propostas em artefatos,
com permissão de leitura. Sua execução remota não foi autorizada nesta tarefa.
Exceções de acesso e de estrutura permanecem registradas para intervenção humana.
O teste com o original da EC115 preserva, como alerta, a linha 537 de pontilhados
terminada em `(NR)` sem aspas finais. Essa exceção visual não aceita texto
normativo com citação malformada nem dispensa a revisão da proposta.

## Desempenho e limitações

A homepage não baixa textos de ECs. Catálogo, índice e documentos são verificados
por SHA-256 e carregados sob demanda. O módulo de ECs não recebe preload; o cache
em memória mantém no máximo dois documentos. A preparação offline completa inclui
os textos estruturados das ECs; os HTMLs originais ficam preservados na candidata,
sem cópias base64 desnecessárias no pacote da aplicação. Uma EC
visitada pode ser lida offline, sem garantir que o link externo funcione sem rede.

Reutilizam-se leitor, busca interna, cópia, índice, foco e ajustes existentes.
As ECs não entram na busca geral das legislações nem nos favoritos/resumo de última
leitura, cujo catálogo anterior permanece preservado. A biblioteca possui sua
própria busca de metadados. Datas documentais não são apresentadas como vigência.
Cabeçalhos e ementas usam o documento integral da Câmara; não reproduzem os
encurtamentos ilustrativos dos protótipos. Conteúdo candidato não está publicado.

## Leitura simplificada (apresentação)

O leitor oculta por CSS apenas pontilhados identificados em blocos de citação.
Linhas puramente pontilhadas ficam recolhidas; linhas com identificadores e
marcadores documentais conservam esses elementos e ocultam somente os pontos.
A gramática é restrita a séries de pelo menos quatro pontos (ou duas reticências
Unicode), com identificadores documentais reconhecidos e, opcionalmente, NR/AC.
Palavras normativas, vetos, anotações desconhecidas, três pontos isolados e
situações ambíguas permanecem exibidos. Isso não classifica o alcance jurídico
de uma alteração. Artigos próprios nunca recebem esse tratamento.

“Exibir transcrição oficial integral” restaura todos os pontos no mesmo DOM,
sem reconstrução, segundo leitor ou alteração de dados/hashes. Cópia e busca
continuam usando os textos integrais armazenados. As transcrições mantêm somente
um filete lateral discreto, com tipografia e espaçamento do leitor existente.
Teste dirigido: `python tests/browser/amendment_reading.py`.
