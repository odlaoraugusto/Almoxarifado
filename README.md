# Almoxarifado — Sistema de Solicitação e Controle de Estoque

SaaS para controle de almoxarifado hospitalar: qualquer pessoa da organização abre um
pedido de material pelo formulário público (sem login); a equipe do almoxarifado
(1 coordenador + 4 atendentes, únicos com login) vê a fila no painel, confere item a
item (com controle de estoque por lote/validade, FEFO), registra entradas (compra ou
empréstimo/permuta com unidade externa), ajusta saldo por contagem física, e exporta
relatórios em PDF/Excel — com prévia em tela antes de baixar.

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
- **Ajuste de estoque**: correção de saldo por contagem física (exclusivo Coordenador).
- **Relatórios** (`/relatorios`): pedidos, estoque, vencimentos, movimentações — prévia em
  tela + exportação PDF/Excel.

## Perfis de acesso

| Perfil | Login? | Pode |
|---|---|---|
| Solicitante (qualquer pessoa) | Não | Abrir pedido pelo formulário público |
| Atendente (4) | Sim | Ver fila, conferir pedidos, registrar entrada/empréstimo, ver relatórios |
| Coordenador (1) | Sim | Tudo do Atendente + cadastrar itens/setores, ajustar estoque, gerenciar usuários |

## Ambiente de teste online

- **Frontend**: https://almoxarifado.169-58-217-209.sslip.io
- **Backend**: https://almoxarifado-api.169-58-217-209.sslip.io
- Ambos rodando em Docker na mesma VPS, atrás de Traefik/HTTPS (Let's Encrypt) — ver `docker-compose.vps.yml`.
- **Banco**: Postgres na mesma VPS (container compartilhado com outros serviços) — o almoxarifado tem **banco e usuário próprios**, isolados, nunca exposto à internet (só acessível pela rede Docker interna).
- **Código**: https://github.com/odlaoraugusto/Almoxarifado (público — nome real da instituição só em `.env`, nunca commitado)

`render.yaml` continua no repo como caminho alternativo de deploy (Render + Neon), não usado atualmente.

Credenciais iniciais (seed): login `coordenador` / `atendente1`..`atendente4`, senha temporária `Almox@2026` — troca obrigatória no primeiro acesso.

## Instalação em servidor local (produção)

Ver **[`docs/05_INSTALACAO_SERVIDOR_LOCAL.md`](docs/05_INSTALACAO_SERVIDOR_LOCAL.md)** — guia completo do zero num computador novo, cobrindo Docker e instalação nativa (sem Docker).

## Status

Em uso no ambiente de teste, com dados fictícios para validação (a zerar antes do uso real).
