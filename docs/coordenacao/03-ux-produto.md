# Parecer técnico — UX e Produto | Lexa

**Frente:** UX e Produto  
**Data:** 18/10/2026  
**Status:** parecer documental para apreciação da Coordenação Central; sem implementação ou validação jurídica independente.

## 1. Identificação e referências examinadas

- **Repositório:** [pajaao/lexa.](https://github.com/pajaao/lexa.)
- **main examinada:** [84c5bb5c5e28c08376e0bf40cf3f3f4b4fd783cf](https://github.com/pajaao/lexa./commit/84c5bb5c5e28c08376e0bf40cf3f3f4b4fd783cf).
- **Investigação Fase 0.5:** branch **investigacao/remissoes-fase-0-5**, [b414204aadf24d0a0d213365060bc347b3f3847d](https://github.com/pajaao/lexa./commit/b414204aadf24d0a0d213365060bc347b3f3847d).
- **Infraestrutura experimental Fase 1A:** branch **funcionalidade/remissoes-fase-1a**, [3bb3c412e06f23a7be27458669ddd1448f35a130](https://github.com/pajaao/lexa./commit/3bb3c412e06f23a7be27458669ddd1448f35a130).
- **Estado das branches na verificação documental:** ambas as branches de remissões estavam à frente da **main** (respectivamente 6 e 9 commits), não incorporadas nela. A branch documental **docs/parecer-ux** foi criada a partir do commit de **main** acima.

Os arquivos examinados na avaliação original incluem [src/app.js](https://github.com/pajaao/lexa./blob/84c5bb5c5e28c08376e0bf40cf3f3f4b4fd783cf/src/app.js), [src/reader.js](https://github.com/pajaao/lexa./blob/84c5bb5c5e28c08376e0bf40cf3f3f4b4fd783cf/src/reader.js), [src/data.js](https://github.com/pajaao/lexa./blob/84c5bb5c5e28c08376e0bf40cf3f3f4b4fd783cf/src/data.js), [src/loading.js](https://github.com/pajaao/lexa./blob/84c5bb5c5e28c08376e0bf40cf3f3f4b4fd783cf/src/loading.js), [src/pwa.js](https://github.com/pajaao/lexa./blob/84c5bb5c5e28c08376e0bf40cf3f3f4b4fd783cf/src/pwa.js), [src/sw.js](https://github.com/pajaao/lexa./blob/84c5bb5c5e28c08376e0bf40cf3f3f4b4fd783cf/src/sw.js), [docs/remissoes/fase-0-5.md](https://github.com/pajaao/lexa./blob/b414204aadf24d0a0d213365060bc347b3f3847d/docs/remissoes/fase-0-5.md), [docs/remissoes/fase-1a.md](https://github.com/pajaao/lexa./blob/3bb3c412e06f23a7be27458669ddd1448f35a130/docs/remissoes/fase-1a.md) e [src/optional/remissions-contract.js](https://github.com/pajaao/lexa./blob/3bb3c412e06f23a7be27458669ddd1448f35a130/src/optional/remissions-contract.js).

Não houve nova auditoria, teste físico de usabilidade, execução de suítes ou alteração de código durante o registro deste parecer. Identificadores de outras frentes (A01, B01, B02, C01) não se aplicam às constatações originalmente registradas por UX e Produto.

## 2. Escopo

Avaliar a futura apresentação de **remissões textuais expressas, verificadas e vinculadas à edição jurídica**, ao final de cada artigo e recolhidas por padrão; examinar separação de relações inversas, ida ao destino, retorno à origem, mobile, foco, teclado, acessibilidade, modo offline e estados vazios/de falha. A análise respeita os princípios de simplicidade e fidelidade ao texto legal, sem IA integrada, conexões por semelhança temática ou interpretação jurídica automatizada.

O parecer **não** aprova a precisão jurídica do extrator, a política experimental ou a publicação de quaisquer vínculos.

## 3. Evidências verificadas

1. **Leitor e rotas existentes.** O roteamento utiliza a URL com hash, resolve a norma e reconstitui o leitor na mudança de rota; o leitor pagina em blocos de 15 artigos. O artigo solicitado é deslocado para a área visível por **scrollIntoView**. Referências: [src/app.js, linhas 215–258](https://github.com/pajaao/lexa./blob/84c5bb5c5e28c08376e0bf40cf3f3f4b4fd783cf/src/app.js#L215-L258), [src/reader.js, linhas 7–14 e 160–173](https://github.com/pajaao/lexa./blob/84c5bb5c5e28c08376e0bf40cf3f3f4b4fd783cf/src/reader.js#L160-L173).
2. **Estado de leitura principalmente local.** Página, divisão selecionada e painel do leitor são estados locais; há preferência de tipografia e registro de último artigo lido, mas não há contrato específico de ida-e-volta por remissão com restauração de posição/foco/expansão. Referências: [src/reader.js, linhas 7–14, 26–34 e 103–121](https://github.com/pajaao/lexa./blob/84c5bb5c5e28c08376e0bf40cf3f3f4b4fd783cf/src/reader.js), [src/app.js, linhas 215–258](https://github.com/pajaao/lexa./blob/84c5bb5c5e28c08376e0bf40cf3f3f4b4fd783cf/src/app.js#L215-L258).
3. **CF/ADCT diferenciados.** O leitor separa os escopos, e as referências ADCT têm identificador próprio. Referências: [src/reader.js, linhas 7–18](https://github.com/pajaao/lexa./blob/84c5bb5c5e28c08376e0bf40cf3f3f4b4fd783cf/src/reader.js#L7-L18), [src/data.js](https://github.com/pajaao/lexa./blob/84c5bb5c5e28c08376e0bf40cf3f3f4b4fd783cf/src/data.js).
4. **Acessibilidade existente.** Há link para pular ao conteúdo, estrutura de artigo, controle de modo de foco, índice recolhível e deslocamento compensado pela barra de leitura. A implementação atual de navegação entre artigos **não realiza foco programático no artigo de destino** no fluxo de rota identificado. Referências: [src/index.html](https://github.com/pajaao/lexa./blob/84c5bb5c5e28c08376e0bf40cf3f3f4b4fd783cf/src/index.html), [src/reader.js, linhas 103–121 e 160–173](https://github.com/pajaao/lexa./blob/84c5bb5c5e28c08376e0bf40cf3f3f4b4fd783cf/src/reader.js), [src/styles.css](https://github.com/pajaao/lexa./blob/84c5bb5c5e28c08376e0bf40cf3f3f4b4fd783cf/src/styles.css).
5. **Infraestrutura 1A deliberadamente inativa.** O relatório declara zero UI, nenhum consumidor no leitor, modo apenas experimental, política independente de elegibilidade e revisão humana jurídica independente pendente. São descritas 272 ocorrências elegíveis e 329 arestas experimentais únicas, números **não auditados juridicamente na íntegra**. O índice experimental mede 54.795 bytes sem compressão (18.728 gzip local). A home não inicia download do índice; o carregamento é sob demanda. Referências: [fase-1a.md — resultado, política, contrato, PWA e medições](https://github.com/pajaao/lexa./blob/3bb3c412e06f23a7be27458669ddd1448f35a130/docs/remissoes/fase-1a.md), [src/optional/remissions-contract.js](https://github.com/pajaao/lexa./blob/3bb3c412e06f23a7be27458669ddd1448f35a130/src/optional/remissions-contract.js).
6. **Invariantes de edição e offline.** O contrato experimental confere hashes e conjunto de edições, recusa incompatibilidades, deriva inversas das mesmas arestas e distingue índice disponível de texto de destino armazenado. A PWA já possui preparo completo explícito e verificação de integridade de recursos. Referências: [remissions-contract.js](https://github.com/pajaao/lexa./blob/3bb3c412e06f23a7be27458669ddd1448f35a130/src/optional/remissions-contract.js), [fase-1a.md — PWA e distribuição](https://github.com/pajaao/lexa./blob/3bb3c412e06f23a7be27458669ddd1448f35a130/docs/remissoes/fase-1a.md), [src/sw.js](https://github.com/pajaao/lexa./blob/84c5bb5c5e28c08376e0bf40cf3f3f4b4fd783cf/src/sw.js).

## 4. Problemas confirmados: gravidade, reprodução e impacto

Estes problemas são **lacunas constatadas no código existente em relação ao fluxo futuro**, e não falhas observadas em uma UI de remissões já publicada (ela não existe). Os roteiros abaixo são instruções de reprodução **a executar**, não resultados de teste manual realizado.

| ID | Gravidade | Constatação | Reprodução / verificação dirigida | Impacto |
| --- | --- | --- | --- | --- |
| **UXP-01** | **Alta** para liberar remissões | O roteador/leitor não possui contrato de retorno contextual de uma remissão: o estado local de paginação/divisão é recriado e a rota do artigo apenas desloca a página até ele. | Inspecionar **route()** em app.js e **reader()** em reader.js. Em futura prévia, abrir origem em página avançada ou com filtro, seguir remissão e usar Voltar; confrontar URL, painel, filtro, posição e foco anteriores. | Perda do contexto de estudo e do ponto exato da leitura, sobretudo após percursos longos. |
| **UXP-02** | **Alta** para acessibilidade da nova navegação | A rota para artigo executa deslocamento visual, sem transferência programática de foco para o título/conteúdo de destino. | Inspecionar final de **reader()**, que usa **scrollIntoView**. Na prévia, navegar exclusivamente com teclado e verificar **document.activeElement** e anúncio do leitor de tela após seguir vínculo. | Risco de desorientação de usuários de teclado/leitor de tela. O grau de falha em navegadores específicos requer teste real. |

**Não classificado como defeito atual:** inexistência de componente visual de remissões, ausência de estado específico de erro/offline para esse recurso e falta de navegação inversa são limites deliberados do estágio experimental, e não regressões da **main**.

## 5. Hipóteses, riscos e verificações pendentes

- **R-01 — Descoberta sob demanda:** como o índice não é carregado na entrada do leitor, a interface precisa saber onde mostrar um controle recolhido **sem download automático global**. Hipótese: metadado mínimo de existência de vínculos, derivado da mesma edição aprovada; exige estudo de contrato, tamanho e invalidação, não está implementado.
- **R-02 — Retorno e rolagem:** renderização assíncrona, altura variável dos controles fixos, alterações de fonte, paginação e histórico do navegador podem comprometer a restauração pixel a pixel. Não foi comprovado por teste interativo.
- **R-03 — Offline parcial:** o índice pode estar no cache e o texto do destino, não. Requer mensagem adequada e retorno sem bloquear a origem; testar também integridade inválida e transição entre edições.
- **R-04 — Mobile e tecnologias assistivas:** alvos de toque, altura da barra fixa, anúncio de expansão, ordenação de foco e leitores de tela em Android/iOS ainda não foram avaliados em dispositivo físico.
- **R-05 — Risco semântico:** títulos como “Artigos relacionados” ou explicações de “relevância” sugeririam associação jurídica não autorizada. A interface deve representar apenas texto expressamente remetido, não vigência, conteúdo semelhante ou interpretação.
- **R-06 — Qualidade jurídica:** a avaliação experimental não teve revisão humana independente e não autoriza generalizar a precisão do acervo, apesar de testes técnicos verdes.

## 6. Recomendações priorizadas

### Obrigatórias antes de disponibilizar a UI em produção

**P0 — Contrato jurídico de exibição.** Mostrar somente arestas aprovadas por revisão e política central, vinculadas à edição íntegra. Nunca completar referências com semelhança temática ou inferência; CF e ADCT permanecem distintos. O leitor não edita, não destaca por mutação e não reescreve a redação legal. Quando houver incerteza, omitir o vínculo.

**P0 — Navegação direta e reversível.** Utilizar a URL canônica do artigo e o leitor já existente, não modal ou painel de texto duplicado. Capturar no histórico da sessão a rota completa e o contexto transitório de origem; no retorno, restaurar divisão, filtros, paginação, artigo, expansão e rolagem após renderizar. Preservar também o botão nativo Voltar e encadeamentos A → B → C. Não persistir esse histórico contextual como histórico permanente de consultas.

**P0 — Acessibilidade de foco.** Depois da navegação, focar o cabeçalho/conteúdo do artigo de destino com rolagem compensada; na volta, devolver foco ao vínculo de origem se ainda existir, ou a alvo substituto lógico. Teclado integral, foco visível, sem armadilhas e com texto acessível para estado expandido/recolhido.

**P0 — Falha segura.** Distinguir “nenhuma remissão aprovada” (nenhum controle) de falha de carga/índice inválido (mensagem e ação de tentar novamente). Não mostrar arestas de edições misturadas. Falha ao abrir destino offline não deve apagar ou tornar inacessível a origem.

**P1 — Apresentação mínima.** Ao final do artigo, controle **Remissões expressas (N)** fechado por padrão e lista de destinos identificados por artigo, norma e, quando necessário, escopo. Sem alteração da redação, inserção automática de links no corpo ou resumo jurídico gerado. Usar padrões nativos de expansão e ações com área acionável confortável no mobile.

### Opcionais ou posteriores

- **P2 — Relações inversas:** seção separada **Citado expressamente por (N)**, também recolhida, derivada das mesmas arestas, nunca grafos inferidos; liberar após validar o fluxo direto.
- **P2 — Ajustes visuais:** refinamento de espaçamento/indicadores sem cartões grandes, painel lateral, modal ou prévias jurídicas.
- **P2 — Descoberta de seções:** escolher com Engenharia o menor metadado possível para existência de vínculos, se necessário, sem violar o orçamento de carga inicial.

## 7. Critérios de aceite objetivos

| ID | Cenário de teste | Resultado obrigatório |
| --- | --- | --- |
| **AC-01** | Artigo sem arestas autorizadas | Nenhum cabeçalho/seção vazia; nenhuma conexão sugerida por tema. |
| **AC-02** | Artigo com remissões autorizadas | Seção ao final e recolhida por padrão; somente arestas aprovadas, títulos inequívocos; texto legislativo e cópia permanecem inalterados. |
| **AC-03** | Expansão com teclado | Tab/Shift+Tab e Enter/Espaço funcionam; estado anunciado de forma acessível; foco nunca oculto. |
| **AC-04** | Ida ao destino | Abre artigo correto, norma, CF/ADCT e edição corretos; posiciona visualmente e programaticamente o foco no conteúdo. |
| **AC-05** | Voltar por ação contextual e pelo navegador | Retorna à mesma rota, página, filtro, painel, posição e, quando aplicável, link focado; não aparece ação de retorno sem origem válida. |
| **AC-06** | Percurso A → B → C | Voltar percorre C → B → A sem trocar origem nem criar ciclo indevido de histórico. |
| **AC-07** | Origem na página 2+, divisão filtrada e modo de foco | Todos os estados recuperados; fonte e espaçamento alterados não impedem encontrar o ponto anterior. |
| **AC-08** | Mobile 320/360/390 px e zoom 200% | Sem rolagem horizontal, corte de controles, obstrução pela barra fixa ou perda de foco visível. |
| **AC-09** | Navegação por leitor de tela | Nome, quantidade, estado da seção, destino e retorno compreensíveis sem narrar vínculos como interpretação jurídica. |
| **AC-10** | Offline com destino não guardado | Explicação específica de indisponibilidade e caminho inequívoco de retorno, sem impedir leitura da origem. |
| **AC-11** | Offline completo previamente confirmado | Índice e artigos de destino preparados abrem sem rede na mesma edição. |
| **AC-12** | Rede/SHA/contrato/edição incompatível | Nenhuma aresta parcial ou obsoleta; estado de falha recuperável; não combinar índices e textos de edições distintas. |
| **AC-13** | Entrada direta por URL | Artigo funciona sem estado de remissão anterior e sem botão de “voltar à leitura” fictício. |
| **AC-14** | Home, busca, favoritos, cópia e PWA com recurso desabilitado | Comportamento existente preservado; zero solicitação inicial do índice de remissões. |
| **AC-15** | Comparar resultado com lista de arestas aprovada | Equivalência exata dos destinos mostrados; links desconhecidos/ambíguos omitidos. |

**Procedimento:** automatizar regressões de rotas, eventos de foco e integridade; executar testes manuais com teclado e leitores de tela (desktop e celular), rede desligada e cache parcial; usar fixtures de origem/destino confirmados. Testes verdes técnicos, isoladamente, não certificam integridade jurídica global. Não há testes novos executados neste parecer.

## 8. Pendências para a Coordenação Central

1. **Autorização jurídica prévia:** definir quem revisa independentemente as classes e vínculos da Fase 1A, quais casos são elegíveis e a política de abstenção; confirmar que a Fase 1A experimental **não** é base autorizada para publicação automática.
2. **Recorte da primeira UI:** aprovar saída apenas, recolhida por padrão, e diferir ou incluir as inversas em bloco claramente distinto.
3. **Retorno contextual:** decidir o contrato compartilhado com Engenharia para guardar estado transiente, com suporte a histórico normal, filtros e foco.
4. **Descoberta sem custo inicial:** decidir se será gerado metadado leve por artigo ou outra solução que preserve carregamento sob demanda e integridade da edição.
5. **Portão de liberação:** aprovar orçamento de desempenho/mobile, amostragem acessível e plano de testes offline; exigir regressão e revisão antes de qualquer integração, merge ou deploy.

## 9. Parecer final

**Favorável à direção de UX proposta, com condicionantes; não favorável à ativação imediata.**

A experiência recomendada é uma extensão discreta da leitura: **remissões expressas verificadas, no final do artigo, recolhidas, com navegação canônica e retorno exato ao contexto anterior**. Relações inversas, se aprovadas, devem aparecer separadamente. A simplicidade não pode ocultar erro de edição, ambiguidade ou ausência de destino offline.

Para avançar à implementação, são indispensáveis: (i) aprovação central e revisão jurídica independente da política/arestas; (ii) contrato técnico para restauração de contexto e foco; (iii) tratamento seguro de ausência, falha e offline; e (iv) comprovação dos critérios de aceite em dispositivos e cenários reais.

**Limite de autorização deste registro:** somente documentação em branch própria. Nenhum código, base legislativa, política de elegibilidade, merge ou deploy está autorizado por este parecer.
