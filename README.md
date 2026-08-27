# Almoxarifado — Sistema de Solicitação e Controle de Estoque

SaaS para controle de almoxarifado hospitalar: qualquer pessoa da organização abre um
pedido de material pelo formulário público (sem login); a equipe do almoxarifado
(1 coordenador + 4 atendentes) vê a fila no painel, confere item a item (com controle de
estoque por lote/validade, FEFO), registra entradas (compra ou empréstimo/permuta com
unidade externa), ajusta saldo por contagem física, e exporta relatórios em PDF/Excel —
com prévia em tela antes de baixar. Um Admin global, separado da equipe operacional,
configura o que Coordenador e Atendente podem fazer (tela Permissões).

Stack e convenções de pasta inspiradas no projeto irmão `estoque-farmacia-ref/`
(clonado localmente ao lado desta pasta a partir de `odlaoraugusto/estoque-farmacia`).

## Stack

- **Backend**: Python + FastAPI + SQLAlchemy + Alembic
- **Banco de dados**: PostgreSQL
- **Frontend**: React + TypeScript + Vite
- **Relatórios**: gerados em Python (reportlab para PDF, openpyxl para Excel), sem serviço separado
- **Deploy**: Docker (recomendado) ou instalação nativa — ver `docs/05_INSTALACAO_SERVIDOR_LOCAL.md`

## Estrutura

```
almoxarifado/
├── backend/        API FastAPI (auth, itens, lotes, pedidos, empréstimos, ajustes, relatórios)
├── frontend/        React + TS (formulário público + painel autenticado)
└── docs/            Planejamento e guia de instalação
```

Ver `backend/README.md` e `frontend/README.md` para detalhes de cada parte, e
`docs/05_INSTALACAO_SERVIDOR_LOCAL.md` para o passo a passo completo de instalação
num servidor novo (Docker ou nativo).

## Funcionalidades

- **Formulário público** (`/`, sem login): qualquer pessoa da organização pede material.
- **Painel** (`/painel`): fila de pedidos com filtros, seleção em lote, conferência item
  a item (quantidade solicitada fixa × quantidade dispensada editável, com checkbox por
  item — dá pra conferir só parte do pedido agora). Status `pendente` → `parcial` →
  `executado`, calculado automaticamente.
- **Estoque** (`/estoque`): catálogo de itens (categoria fixa: Material Médico / EPI /
  Higienização / Material de Expediente), saldo por lote, alerta de estoque crítico e
  vencimento em 4 grupos (vencidos / ≤30d / 30-60d / 60d+).
- **Entrada por Compra** (`/entrada-compra`): uma nota fiscal (+ AFM opcional), vários itens.
- **Empréstimos e Permutas** (`/emprestimos`): registro com unidade externa, nas duas
  direções (emprestar = saída via FEFO, receber/permuta = entrada).
- **Ajuste de estoque**: correção de saldo por contagem física (liberado por padrão ao
  Coordenador — configurável pelo Admin).
- **Relatórios** (`/relatorios`): pedidos, estoque, vencimentos, movimentações — prévia em
  tela + exportação PDF/Excel.
- **Permissões** (`/permissoes`, exclusivo Admin): define o que Coordenador e Atendente
  podem fazer além do básico.

## Perfis de acesso

| Perfil | Login? | Pode |
|---|---|---|
| Solicitante (qualquer pessoa) | Não | Abrir pedido pelo formulário público |
| Atendente (4) | Sim | Ver fila, conferir pedidos, registrar entrada/empréstimo, ver relatórios. Ações extras (ajustar estoque, gerenciar itens/setores, gestão de usuários, relatório de movimentações) dependem do que o Admin liberou na tela Permissões |
| Coordenador (1) | Sim | Igual ao Atendente + as ações extras liberadas por padrão (configurável, tela Permissões) |
| Admin (global) | Sim | Superusuário implícito — sempre com tudo liberado. Único que acessa a tela **Permissões**, onde define o que Coordenador e Atendente podem fazer, e o único que pode promover outro login a Admin |

A matriz de permissões (`PUT /permissoes`) nasce com o comportamento histórico do sistema (Coordenador com tudo liberado, Atendente só com o básico) — o Admin ajusta a partir daí, sem precisar mexer em código.

## Deploy

- **[`docs/05_INSTALACAO_SERVIDOR_LOCAL.md`](docs/05_INSTALACAO_SERVIDOR_LOCAL.md)** — guia completo do zero num computador novo, cobrindo Docker e instalação nativa, incluindo como importar o catálogo de itens de uma planilha Excel/CSV existente (`backend/scripts/importar_itens_planilha.py` + modelo em `docs/modelo_importacao_itens.xlsx`) em vez de cadastrar item por item.
- **[`docs/GUIA_IMPLANTACAO_SERVIDOR.md`](docs/GUIA_IMPLANTACAO_SERVIDOR.md)** — instalação nativa/NSSM num servidor Windows que já roda outros apps (portas configuráveis, convivendo com os demais serviços).
- `render.yaml` continua no repo como caminho alternativo de deploy (Render + Neon), não usado atualmente.

Credenciais iniciais (seed): login `coordenador` / `atendente1`..`atendente4`, senha temporária `Almox@2026`; login `admin` (seed separado, `scripts/seed_admin.py`), senha temporária `Admin@2026` — troca obrigatória no primeiro acesso de todos.

## Status

Em uso no ambiente de teste, com dados fictícios para validação (a zerar antes do uso real).
