# Almoxarifado — Frontend

React + TypeScript + Vite. Consome a API real do backend (`../backend`) —
sem dados mockados. Estrutura e convenções de código inspiradas no
projeto irmão (`estoque-farmacia-ref/frontend`), paleta visual oficial
FESFSUS idêntica à do sistema irmão e ao protótipo aprovado do formulário
público (`../docs/prototipo_formulario_publico.html`).

## Rodando localmente

```bash
npm install
cp .env.example .env   # ajuste VITE_API_URL se o backend não estiver em localhost:8000
npm run dev
```

O backend precisa estar rodando (ver `../backend/README.md`) com pelo
menos um usuário coordenador semeado.

## Scripts

- `npm run dev` — servidor de desenvolvimento
- `npm run build` — `tsc -b` + build de produção
- `npm run lint` — oxlint
- `npm run preview` — serve o build de produção localmente

## Estrutura

```
src/
  types.ts              tipos espelhando os schemas do backend
  lib/
    api.ts               cliente HTTP fino (fetch) + ApiError + mensagens amigáveis
    permissoes.ts         regras de visibilidade por perfil (coordenador/atendente)
    formato.ts            formatação de data/moeda/labels/régua de vencimento
    instituicao.ts        nome fixo do hospital/organização (não há endpoint /config)
  context/
    AuthContext.tsx        sessão (token, usuário)
  components/
    Layout.tsx              topbar institucional + sidebar + outlet
    RotaProtegida.tsx        guarda de rota (token) + ExigeSenhaAtualizada (força /trocar-senha)
    Alerta.tsx               banner de erro/sucesso/info
    BuscaAutocomplete.tsx    busca genérica com sugestões (reaproveitável; a busca do
                             formulário público tem UX própria portada do protótipo,
                             não usa este componente)
  pages/
    PedidoPublicoPage.tsx   "/" — formulário público de pedido de material (sem login)
    LoginPage.tsx           login da equipe (1 coordenador + 4 atendentes)
    TrocarSenhaPage.tsx     troca de senha (obrigatória no 1º login)
    PainelPage.tsx          fila de pedidos + conferência item a item
    EstoquePage.tsx         catálogo de itens (saldo agregado por lotes) + lotes + entrada/ajuste
    SetoresPage.tsx         CRUD de setores (exclusivo Coordenador)
    RelatoriosPage.tsx      exportação de relatórios em PDF/Excel
    UsuariosPage.tsx        gestão dos 5 logins (exclusivo Coordenador)
```

## Permissões

Toda visibilidade de tela/ação é derivada de `usuario.perfil` (vindo de
`/auth/me`) — ver `src/lib/permissoes.ts`, que espelha a matriz da seção
3.3 de `../docs/00_PROJETO_ALMOXARIFADO.md`. Itens sem acesso somem do
menu, não aparecem desabilitados.

## Sobre o contrato de API

Este frontend foi construído em paralelo ao backend (agente
`almox-backend`) a partir de `../docs/00_PROJETO_ALMOXARIFADO.md`
(modelagem definitiva: `pedidos` com N `pedido_itens`, `lotes` por item,
`setores`). Como o schema exato dos endpoints novos não estava fixado
literalmente no doc, o frontend chegou a assumir alguns nomes de rota
que não batiam com o que o backend implementou de fato — **essas
divergências já foram conferidas contra o código real do backend e
corrigidas** (ver histórico da sessão). Contrato final, conferido rota a
rota:

- `GET /setores/publico`, `GET /itens/publico` — públicos, sem auth,
  usados pelo formulário em `/`.
- `POST /pedidos` (sem auth) — cria o pedido; a resposta traz `id` (vira
  o "protocolo" mostrado no modal de sucesso) e os itens, usados no
  comprovante em PDF gerado no cliente via `jsPDF`.
- `GET /pedidos?status=&setor_id=`, `GET /pedidos/{id}` (Bearer) — fila e
  detalhe (com `itens[]` aninhados).
- `PATCH /pedidos/{id}/itens/{itemId}/conferir` (Bearer) `{
  item_id_entregue?, quantidade_entregue, motivo_substituicao? }` —
  conferido contra `app/schemas/pedido.py::PedidoItemConferirCreate` no
  backend, bate exatamente. `item_id_entregue`/`motivo_substituicao` só
  são enviados quando o atendente troca o item entregue pelo solicitado.
- `GET /itens?incluir_inativos=` (Bearer, saldo agregado — `Σ lotes`,
  nunca escrito diretamente pelo front), `POST /itens`, `PUT /itens/{id}`
  (coordenador).
- `GET /lotes` (Bearer, todos os lotes) e `POST /itens/{id}/entrada`
  (Bearer, qualquer perfil — registra uma entrada/novo lote; `item_id`
  vai na URL, não no payload) — **corrigido**: a suposição original era
  `POST /lotes`, mas o backend implementou a entrada como sub-rota de
  item (`app/api/routes/itens.py`). O `GET /lotes` não existia no
  backend original — foi adicionado durante a verificação de integração.
- `POST /ajustes` (Bearer, só coordenador) `{ lote_id, quantidade_nova,
  motivo_ajuste }` — **corrigido**: a suposição original enviava um
  `delta` pronto; o backend (mesmo padrão da farmácia) exige o **novo
  saldo** e calcula o delta ele mesmo. O formulário em `EstoquePage`
  agora pede "novo saldo (contagem física)" em vez de uma diferença.
- `GET /usuarios?incluir_inativos=`, `GET /setores?incluir_inativos=`,
  `GET /itens?incluir_inativos=` — parâmetro confirmado idêntico nos
  três endpoints.
- Relatórios: `/relatorios/pedidos`, `/relatorios/estoque`,
  `/relatorios/vencimentos`, `/relatorios/movimentacoes` — **corrigido**:
  a rota de pedidos estava apontando para `/relatorios/solicitacoes`
  (nome do contrato inicial, já abandonado), o que dava 404. A aba
  "Vencimentos próximos" (`dias` como filtro) também foi adicionada — o
  backend já a expunha, só não estava coberta no frontend.

## Formulário público (`/`)

Adaptado quase literalmente do protótipo aprovado
(`../docs/prototipo_formulario_publico.html`): mesma UX de busca/adição
de item com sugestões (código, nome, badge de categoria, navegação por
teclado), tabela de itens do pedido com quantidade editável, modal de
sucesso com protocolo e botão "Baixar Comprovante em PDF" (gerado no
cliente com `jsPDF` — é só um recibo rápido pro solicitante; os
relatórios de verdade continuam sendo gerados no backend). Só a fonte de
dados mudou: Google Apps Script/Sheets → nossa API. As classes CSS do
protótipo foram portadas com os mesmos nomes, escopadas sob
`.pedido-publico` em `src/index.css` para não vazar pros seletores
genéricos (`table`, `section`, `input`) usados no resto do sistema
autenticado, que compartilha o mesmo bundle de CSS.
