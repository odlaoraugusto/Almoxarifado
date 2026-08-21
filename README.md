# Almoxarifado — Sistema de Solicitação e Controle de Estoque

SaaS simples para controle de almoxarifado: qualquer pessoa da organização abre uma
solicitação de material pelo formulário público (sem login); a equipe do almoxarifado
(1 coordenador + 4 atendentes, únicos com login) vê a fila no painel, assume, atende
(dando baixa no estoque) ou recusa cada solicitação, e exporta relatórios em PDF/Excel.

Stack e convenções de pasta inspiradas no projeto irmão `estoque-farmacia-ref/`
(clonado localmente ao lado desta pasta a partir de `odlaoraugusto/estoque-farmacia`),
adaptando o domínio: aqui não há lotes/validade/múltiplas unidades — é um controle de
estoque único, mais simples, com formulário de entrada público.

## Stack

- **Backend**: Python + FastAPI + SQLAlchemy + Alembic
- **Banco de dados**: PostgreSQL, local (sem Docker — instalação direta na máquina/servidor)
- **Frontend**: React + TypeScript + Vite
- **Relatórios**: gerados em Python (reportlab para PDF, openpyxl para Excel), sem serviço separado

## Estrutura

```
almoxarifado/
├── backend/        API FastAPI (auth, itens, solicitações, relatórios)
└── frontend/        React + TS (formulário público + painel autenticado)
```

Ver `backend/README.md` e `frontend/README.md` para como rodar cada parte localmente.

## Perfis de acesso

| Perfil | Login? | Pode |
|---|---|---|
| Solicitante (qualquer pessoa) | Não | Abrir solicitação pelo formulário público |
| Atendente (4) | Sim | Ver fila, assumir/atender/recusar solicitações, dar entrada de estoque, ver relatórios |
| Coordenador (1) | Sim | Tudo do Atendente + cadastrar/editar itens do catálogo, gerenciar usuários (os 5 logins) |

## Status

Em construção — v1 inicial.
