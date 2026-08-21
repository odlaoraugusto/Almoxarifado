# Planejamento Técnico — Sistema de Gerenciamento de Almoxarifado Hospitalar

Documento no mesmo formato de `docs/00_PROJETO.md` do projeto de referência (`estoque-farmacia`), adaptado ao domínio do Almoxarifado. Objetivo: fechar premissas e modelagem antes de escrever qualquer código, do mesmo jeito que foi feito lá.

## 1. Premissas já confirmadas (nesta conversa)

| Item | Decisão |
|---|---|
| Ambiente | Servidor local do hospital, rede interna (mesmo princípio da farmácia) |
| Stack | Python (FastAPI) + PostgreSQL + React, sem Docker — mesma stack da farmácia |
| Banco de dados | Local, separado do banco da farmácia (dois sistemas distintos) |
| Relação com a farmácia | Projetos irmãos — reaproveitam padrão técnico e visual, mas não compartilham login nem banco |
| Quem pede material | Qualquer setor do hospital, **sem login** — formulário público, como é hoje no Google Sheets |
| Quem executa/confere | Só a equipe do almoxarifado — hoje 5 pessoas, autenticadas por PIN de 4 dígitos |
| Conferência de entrega | Item a item: quantidade solicitada vs. entregue, com registro de substituição (item liberado ≠ item pedido) e motivo obrigatório nesse caso |
| Relatório gerencial | Saídas registradas, filtrável por data, exportável em Excel **e** PDF |
| Identidade visual | Paleta oficial FESFSUS (`#61358c` `#7572a7` `#79bfb4` `#73d9a8` `#575756`), mesmo princípio já aplicado na farmácia (barra institucional com as cores cheias, resto do sistema com paleta suavizada) |

## 2. Diferença estrutural importante em relação à farmácia

Na farmácia, **todo mundo loga** (Coordenador/Farmacêutico/Atendente) e o sistema controla lote físico com entrada/saída/transferência entre unidades reais.

No almoxarifado, o desenho é mais parecido com um **balcão de pedidos**: setor pede (sem login, como um formulário público) → almoxarifado confere e libera (com login). Não existe hoje a necessidade de "Entrada" nem "Transferência entre unidades" — só existe **Solicitação → Conferência/Liberação**. Isso simplifica bastante o modelo de dados em relação à farmácia (não precisa de `lotes` com `status_transferencia`, por exemplo), *a menos que* a decisão da seção 3 abaixo mude isso.

## 3. Decisões desta rodada

**3.1 — Controle de estoque físico: RESOLVIDO.** O sistema vai controlar `lotes` (quantidade, validade, valor) de verdade, com baixa automática na Conferência — igual ao modelo da farmácia. Estoque crítico e vencimento passam a ser nativos do sistema (não dependem mais da planilha externa).

**3.2 — Autenticação: RESOLVIDO.** Login/senha (não mais PIN), mesmo padrão da farmácia (bcrypt + JWT).

**3.3 — Perfis: RESOLVIDO.** Dois perfis, não três como na farmácia:
- **Coordenador** — 1 pessoa
- **Atendente** — 4 pessoas

**Proposta de matriz de permissões** (defaults abaixo, mesma lógica da farmácia — revisável a qualquer momento):

| Ação | Atendente | Coordenador |
|---|---|---|
| Conferir/liberar pedido (com substituição) | ✅ | ✅ |
| Registrar Entrada de estoque (recebimento de compra) | ✅ | ✅ |
| Ver estoque atual, itens críticos, vencimentos | ✅ | ✅ |
| Relatório de saídas (Excel/PDF) | ✅ | ✅ |
| **Ajuste de estoque** (corrigir saldo fora do fluxo normal, ex. divergência de contagem) | ❌ | ✅ |
| **Cadastro/edição de itens** (nome, apresentação, categoria, estoque mínimo) | ❌ | ✅ |
| **Gestão de usuários** (criar/editar/desativar atendente) | ❌ | ✅ |
| **Trilha de auditoria completa** | ❌ | ✅ |
| **Cadastro de setores** | ❌ | ✅ |

Motivo do corte: são as mesmas 4 ações que a farmácia mantém exclusivas do Coordenador mesmo depois de equalizar Farmacêutico=Coordenador (seção 27 do doc de referência) — são as ações "administrativas" que alteram saldo fora do fluxo normal ou controlam quem tem acesso ao sistema, não o trabalho operacional do dia a dia.

**3.4 — Setor solicitante: proposta de default.** Vira uma tabela simples `setores` (id, nome, ativo) — sem responsável fixo nem centro de custo associado, mantendo o mesmo nível de simplicidade que a aba Setores tem hoje. Cadastro exclusivo do Coordenador (linha da tabela acima). Avisa se precisar de mais campos.

## 4. Modelagem de Banco de Dados (proposta)

Adaptando a estrutura da farmácia (`docs/00_PROJETO.md` seção 6) ao almoxarifado. Diferença estrutural principal: não existem múltiplas unidades físicas de estoque nem transferência entre elas — só **um** estoque central (o almoxarifado), que atende os setores. Por isso não há tabela `unidades` nem `lotes.status_transferencia`.

### `usuarios`
`id, nome, login, senha_hash, perfil (coordenador | atendente), ativo`

### `setores`
`id, nome, ativo`

### `itens` (cadastro geral — catálogo, não é o saldo em si)
`id, codigo, nome, apresentacao, categoria, estoque_minimo`

### `lotes` (estoque físico — cada lote ligado a UM item)
`id, item_id, numero_lote (opcional — nem todo material de almoxarifado tem lote formal), data_validade (opcional — nem todo item vence, ex. material de expediente), quantidade_atual, valor_unitario (opcional), origem (compra | doacao), numero_nota_fiscal, data_entrada, usuario_entrada_id`

### `pedidos` (a solicitação do setor — sem login, formulário público)
`id, setor_id, responsavel_solicitante, observacao, data_hora, status (pendente | executado), data_execucao, usuario_execucao_id`

### `pedido_itens` (um pedido tem vários itens; cada um é conferido individualmente)
`id, pedido_id, item_id_solicitado, quantidade_solicitada, item_id_entregue (nulo até conferir), quantidade_entregue (nulo até conferir), motivo_substituicao (obrigatório quando item_id_entregue ≠ item_id_solicitado)`

### `movimentacoes` (trilha de auditoria — nunca se apaga, igual à farmácia)
`id, tipo (entrada | saida | ajuste), lote_id, quantidade, pedido_item_id (preenchido só quando tipo=saida, liga à liberação de um item de pedido específico), motivo_ajuste (obrigatório quando tipo=ajuste, delta com sinal como na farmácia), usuario_id, data_hora`

### Fluxos

- **Entrada** → cria/incrementa linha em `lotes` + linha em `movimentacoes` (tipo=entrada).
- **Pedido criado** (formulário público, sem login) → cria `pedidos` + `pedido_itens` com status Pendente, sem tocar em `lotes`.
- **Conferência/liberação** → para cada `pedido_item`: preenche `item_id_entregue`/`quantidade_entregue` (e `motivo_substituicao` se for diferente do solicitado), decrementa `lotes.quantidade_atual` do item efetivamente entregue (FEFO — primeiro o lote que vence antes, igual à farmácia) + linha em `movimentacoes` (tipo=saida). `pedidos.status` vira Executado só quando todos os itens do pedido foram conferidos.
- **Ajuste** → Coordenador corrige `lotes.quantidade_atual` fora do fluxo normal + linha em `movimentacoes` (tipo=ajuste, delta com sinal, motivo obrigatório) — mesmo padrão da farmácia.

Isso resolve nativamente: estoque crítico (Σ `quantidade_atual` por item < `estoque_minimo`), vencimento (`lotes.data_validade`, 3 níveis como a farmácia: vencido / <30 dias / 30–60 dias), e trilha de auditoria completa.

## 5. Squad — mesmos papéis do projeto de referência

| Papel | Responsabilidade nesta fase |
|---|---|
| Arquiteto(a) de Software | Fechar a decisão da seção 3.1 e modelar o banco a partir dela |
| Dev Backend | API, regras de negócio (validação de conferência, substituição, PIN/login) |
| Dev Frontend | Formulário público (setor) + painel autenticado (almoxarifado) |
| QA | Casos de teste: concorrência (dois PINs conferindo o mesmo pedido ao mesmo tempo), validação de substituição sem motivo, relatório com filtro de data |
| DevOps | Servidor local, backup (`pg_dump` agendado), rotina de deploy |

## 6. Próximo passo

Confirma a matriz de permissões da seção 3.3 e o default da 3.4 (ou ajusta o que não bater), que eu já parto pra estrutura do projeto (backend FastAPI + Alembic migration inicial + frontend React), do mesmo jeito que foi feito na farmácia depois da aprovação do protótipo.
