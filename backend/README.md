# Almoxarifado — Backend

API REST (FastAPI + PostgreSQL + SQLAlchemy/Alembic) do sistema de controle de
almoxarifado hospitalar (nome real da instituição fica só em `HOSPITAL_NOME`,
variável de ambiente não commitada — repositório público). Ver
`../docs/00_PROJETO_ALMOXARIFADO.md` (raiz do repositório `almoxarifado/`) para
o planejamento completo — este README cobre só o "como rodar".

Convenções de código, estrutura de pastas e stack espelham o projeto irmão
`../../estoque-farmacia-ref/backend` (farmácia hospitalar), adaptadas ao
domínio mais simples do almoxarifado: um único estoque central (sem unidades
múltiplas nem transferência entre elas), com formulário de pedido **público**
(sem login) e conferência item a item pela equipe do almoxarifado.

Sem Docker: instalação direta no servidor (Windows/Linux), PostgreSQL local.

## Requisitos

- Python 3.12+
- PostgreSQL 14+ local (instância própria, separada do banco da farmácia)

## Rodando localmente

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate

pip install -r requirements.txt

copy .env.example .env      # Windows
# cp .env.example .env      # Linux/Mac
# edite o .env com a URL real do banco e um JWT_SECRET_KEY novo
```

### Variáveis de ambiente (`.env`)

| Variável | Obrigatória | Descrição |
|---|---|---|
| `DATABASE_URL` | sim | ex.: `postgresql+psycopg2://almoxarifado:senha@localhost:5432/almoxarifado` |
| `JWT_SECRET_KEY` | sim | segredo de assinatura da sessão — gere com `python -c "import secrets; print(secrets.token_hex(32))"` |
| `JWT_ALGORITHM` | não (default `HS256`) | |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | não (default `480`, 8h) | duração do token/sessão |
| `HOSPITAL_NOME` | não (tem default genérico) | nome exibido no cabeçalho dos relatórios |
| `HOSPITAL_ORGANIZACAO` | não (tem default genérico) | idem, para a organização/rede |
| `CORS_ORIGINS` | não (default `http://localhost:5173`) | lista separada por vírgula das origens do frontend, ou `*` |

### Banco de dados — migrações

```bash
alembic upgrade head
```

Cria o schema completo: `usuarios`, `setores`, `itens`, `lotes`, `pedidos`,
`pedido_itens`, `movimentacoes`.

### Usuários iniciais

```bash
python scripts/seed_usuarios.py
```

Cria 5 usuários (idempotente — pula quem já existe): 1 coordenador
(`coordenador`) + 4 atendentes (`atendente1`..`atendente4`), todos com senha
temporária **`Almox@2026`** e `deve_trocar_senha=true` — o frontend deve
forçar a troca (`POST /auth/trocar-senha`) antes de liberar o resto do
painel. Nomes de exemplo genéricos ("Nome do Coordenador" etc.) — troque
depois via `PUT /usuarios/{id}`.

### Setores iniciais (opcional, mas recomendado)

```bash
python scripts/seed_setores.py
```

Sem isso, o `<select>` de setor do formulário público nasce vazio até o
Coordenador cadastrar algum pela tela `/setores`. O script cria os
setores que já pediam material pelo formulário antigo em planilha (UTI
Neonatal, Maternidade, Centro Cirúrgico, Emergência Obstétrica, Farmácia
Satélite, Enfermaria Pediátrica) — idempotente, mais podem ser
adicionados/editados depois pelo Coordenador.

### Subindo a API

```bash
uvicorn app.main:app --reload
```

Docs interativos (Swagger) em `http://localhost:8000/docs`.

## Status da validação nesta rodada

Havia uma instância PostgreSQL escutando em `localhost:5432` neste ambiente,
mas sem credenciais conhecidas disponíveis para esta sessão — não tentei
adivinhar usuário/senha (evitar isso é básico de segurança). Por isso, a
validação foi feita sem um `alembic upgrade head` real contra o banco:

- **Migration**: validada com `alembic upgrade head --sql` (modo offline, gera
  o SQL sem se conectar a um banco) — passou sem erro de sintaxe, FKs na
  ordem certa (`usuarios`/`setores`/`itens` → `lotes` → `pedidos` →
  `pedido_itens` → `movimentacoes`).
- **App**: `from app.main import app` importa sem erro; todas as rotas
  aparecem corretas no `openapi.json` (confirma que todo o grafo de
  models/schemas/services/routers está bem ligado).
- **Exportação de relatórios**: testado gerando PDF e Excel de uma tabela
  fake, incluindo texto contendo `<b>` (tentativa de injeção no PDF) e
  `=CMD(1)`/`+1+1` (tentativa de formula injection no Excel) — PDF veio com
  assinatura válida, e o `.xlsx` gerado foi reaberto com `openpyxl` para
  confirmar que as células perigosas viraram texto literal (`'=CMD(1)`),
  não fórmula.
- **Não validado de ponta a ponta**: fluxo real de conferência de pedido
  (FEFO, lock de linha, finalização de pedido) só roda contra um Postgres de
  verdade — peça pra alguém com acesso ao Postgres local rodar
  `alembic upgrade head && python scripts/seed_usuarios.py` e testar os
  endpoints antes de considerar isso "pronto pra produção".

## Decisões técnicas que desviam ou complementam o doc de planejamento

- **`ativo` em `itens`**: não está na lista literal da seção 4 do
  `00_PROJETO_ALMOXARIFADO.md`, mas foi adicionado (mesmo precedente da
  farmácia) para permitir descontinuar um item do catálogo sem `DELETE`
  físico, que quebraria a FK de `lotes`/`pedido_itens` históricos.
- **`apresentacao`/`categoria` como texto livre (não enum)**: a lista de
  categorias é definida na prática pelo Coordenador (ver
  `docs/prototipo_formulario_publico.html`: "Mat. Med.", "EPI/SIAST",
  "Higienização" etc.) e pode crescer sem exigir migração — mesmo raciocínio
  já documentado na farmácia para evitar `ALTER TYPE`.
- **Conferência de pedido sem `lote_id` explícito**: o contrato de
  `PATCH /pedidos/{id}/itens/{pedido_item_id}/conferir` não pede o lote —
  o backend escolhe automaticamente pelo FEFO (primeiro o lote que vence
  antes), podendo consumir de mais de um lote se um só não cobrir a
  quantidade. Cada lote tocado é travado com `SELECT ... FOR UPDATE` antes
  de decrementar, e cada consumo gera sua própria linha em `movimentacoes`.
- **`quantidade_entregue=0`**: registra "item não atendido" sem tocar em
  estoque nem exigir `motivo_substituicao` (só é obrigatório quando o item
  entregue difere do solicitado) — o doc de planejamento não cobria
  explicitamente rejeição de pedido/item, essa foi a interpretação adotada
  na ausência de um fluxo de "recusa" no novo modelo.
- **Sem endpoint de "assumir" nem "recusar" pedido inteiro**: o modelo novo
  (seção 4 do doc) só tem `pedidos.status = pendente | executado` — mais
  simples que a primeira versão deste plano (que tinha `em_andamento`/
  `recusada`). Ficou assim para seguir literalmente o schema aprovado.
- **`numero_nota_fiscal` sempre opcional em `lotes`**: a farmácia tem uma
  regra de "nota fiscal obrigatória quando origem=compra"; o doc do
  almoxarifado não pede isso explicitamente, então não foi replicada — pode
  ser adicionada depois se o Coordenador confirmar que quer a mesma trava.
- **`HOSPITAL_NOME`/`HOSPITAL_ORGANIZACAO`** (em vez de um único
  `ORGANIZACAO_NOME`): alinhado ao padrão já usado no `.env` da farmácia,
  a pedido da mensagem de correção desta rodada.
- **IDs**: inteiros autoincremento (`SERIAL`), não UUID — mesma decisão já
  tomada na farmácia, adequada a esta escala.
- **Enums**: `VARCHAR + CHECK CONSTRAINT` (`sa.Enum(..., native_enum=False)`),
  não `ENUM` nativo do Postgres — evita `ALTER TYPE ... ADD VALUE` (que não
  roda dentro de transação) se for preciso adicionar um valor novo no futuro.
- **Concorrência**: `SELECT ... FOR UPDATE` ao buscar lote/pedido/pedido_item
  antes de decrementar saldo, dar baixa ou finalizar um pedido — evita duas
  pessoas da equipe conferindo o mesmo item/pedido ao mesmo tempo. Os models
  `Item`/`Solicitação`-equivalentes (`Lote`, `Pedido`, `PedidoItem`) usam
  `lazy="selectin"` nos relacionamentos, não o padrão implícito, porque o
  Postgres recusa `FOR UPDATE` numa query com `LEFT OUTER JOIN` em FK
  opcional (bug real já visto no projeto irmão).
- **Hash de senha**: `bcrypt` direto (sem `passlib`), mesmo motivo já
  documentado na farmácia (incompatibilidade `passlib` 1.7.x × `bcrypt` >= 4.1).
- **Limite conhecido do `FOR UPDATE` em operação de múltiplos passos**: cada
  chamada de repositório (`salvar`/`create`) dá commit imediatamente (mesmo
  padrão "um commit por operação" já usado na farmácia, sem transação manual
  around múltiplos passos). Isso significa que o lock de
  `PedidoItem.get_by_id_for_update()` em `conferir_item` é liberado assim que
  o primeiro commit interno da baixa de lote acontece, antes do
  `pedido_item` em si ser salvo — mesma característica já presente em
  `SolicitacaoService.aceitar` da farmácia (o lock da solicitação é
  liberado pelos commits internos de `TransferenciaService.enviar` antes do
  save final). Na prática, dois atendentes clicando "conferir" no mesmíssimo
  item em uma janela de milissegundos podem, em tese, conferir o mesmo item
  duas vezes. Não introduzi transação manual (`db.begin()`/`rollback`) para
  fechar essa janela por não ser o padrão já estabelecido no projeto irmão —
  mas é um ponto real a revisar com o time se isso disparar em produção.

## Rodada — `numero_afm` em Lote + módulo de Empréstimos e Permutas

- **`lotes.numero_afm`**: campo opcional novo, ao lado de
  `numero_nota_fiscal` — número de autorização usado em compras (mesmo
  conceito do projeto irmão da farmácia). Passa por `EntradaCreate` e
  aparece em `LoteOut`; não muda em nada o fluxo de
  `POST /itens/{item_id}/entrada`, que continua existindo exatamente
  como antes (a tela "Entrada por Compra" do frontend chama esse mesmo
  endpoint uma vez por item, não um endpoint de lote em lote).
- **Empréstimo/permuta com unidade EXTERNA** (`RegistroEmprestimo`,
  tabela `emprestimos`) — não é o mesmo conceito de `Pedido`/`Setor`
  (que são sempre departamentos internos pedindo material pelo
  formulário público). `unidade_origem` é texto livre (nome da
  instituição/unidade de fora), não FK.
  - `direcao=saida`: dá baixa real de estoque via FEFO — reaproveita a
    MESMA lógica de lock+decremento que `PedidoService` usava
    internamente, agora extraída para `app/services/consumo_fefo.py`
    (função `consumir_fefo(db, lote_repository, movimentacao_repository,
    usuario_id, item_id, quantidade_necessaria, *, pedido_item_id=None,
    emprestimo_id=None)`). `PedidoService.conferir_item` foi refatorado
    para chamar essa função compartilhada — comportamento e mensagens de
    erro idênticos aos de antes da refatoração.
  - `direcao=entrada`: cria lote(s) novo(s) por item
    (`Lote.origem='emprestimo'`, `Lote.emprestimo_id` preenchido), igual
    à Entrada por compra/doação.
  - `Movimentacao.emprestimo_id` (FK opcional) só é preenchido nas
    SAÍDAS geradas por um empréstimo enviado — paralelo a
    `pedido_item_id`, mutuamente exclusivos na prática, sem constraint
    de banco pra isso (mesmo padrão do par `pedido_item_id`).
- **Rotas**: `POST /emprestimos` e `GET /emprestimos`, Bearer, qualquer
  perfil autenticado (mesmo nível de permissão de quem já registra
  Entrada de estoque).
- **Formato do "detalhe" em `EmprestimoOut.itens`** (decisão de
  formato, não estava 100% especificada): uma lista de
  `{item, quantidade, lote_id | movimentacao_id}` — um item por LOTE
  criado (direção entrada) ou por linha de `Movimentacao` de saída
  gerada (direção saída). Importante: numa saída, um único item pedido
  em `EmprestimoCreate.itens` pode gerar MAIS DE UMA linha no detalhe se
  o FEFO precisar atravessar mais de um lote para cobrir a quantidade —
  o array de resposta não tem correspondência 1:1 com o array de
  entrada nesse caso.
- **`quantidade` do detalhe de entrada em `GET /emprestimos` (listagem
  histórica)**: usa `Lote.quantidade_atual` no momento da consulta, não
  um valor congelado de "quantidade originalmente recebida" — mesma
  convenção que o resto da API já usa (`LoteOut` também só expõe o
  saldo atual, sem guardar a quantidade de entrada original em nenhum
  lugar). Ou seja, se aquele lote específico já foi parcialmente
  consumido depois (por uma conferência de pedido ou por outro
  empréstimo de saída), o número mostrado no histórico reflete o saldo
  atual do lote, não o que entrou naquele dia. Na resposta de
  `POST /emprestimos` (`criar`) o valor é sempre exato, por ser lido
  logo após a criação do lote.
- **CHECK CONSTRAINT de `lotes.origem`**: a coluna usa
  `sa.Enum(..., native_enum=False)` desde `0001_schema_inicial`, mas —
  mesma limitação real do Alembic já documentada em
  `0002_status_pedido_parcial` (Enum inline dentro de
  `op.create_table` não gera a CHECK de verdade contra um Postgres
  real, só no `--sql` offline) — muito provavelmente nunca teve uma
  CHECK CONSTRAINT de fato em produção. Não deu pra confirmar com `\d
  lotes` nesta rodada (sem acesso à VPS); a migration `0003` documenta
  essa suposição e cria a constraint (não substitui uma que não se sabe
  se existe), já com os 3 valores (`compra`, `doacao`, `emprestimo`).
  Se a mesma limitação também afeta `usuarios.perfil` e
  `movimentacoes.tipo` (colunas com Enum inline em `create_table` na
  mesma migration 0001), não foi investigado nem corrigido nesta rodada
  — fora do escopo pedido; vale uma checagem futura com `\d usuarios`/
  `\d movimentacoes` direto no Postgres da VPS.

## O que ficou fora desta rodada

- **Frontend** — não faz parte deste pacote (`../frontend`, em construção
  em paralelo contra este mesmo contrato de API).
- **Seed de setores** — não foi criado nenhum setor padrão; é cadastro
  exclusivo do Coordenador (`POST /setores`), a fazer no primeiro acesso.
- **Rotina de backup em código** — é configuração de infraestrutura
  (`pg_dump` agendado), não código Python.
