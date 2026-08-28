# Manual do Sistema — Almoxarifado

Manual de uso completo do sistema de solicitação e controle de estoque do
almoxarifado. Cobre as duas portas de entrada do sistema — o formulário
público (sem login) e o painel da equipe (com login) — tela por tela,
incluindo o que cada perfil pode e não pode fazer.

## Sumário

1. [Visão geral](#1-visão-geral)
2. [Perfis de acesso](#2-perfis-de-acesso)
3. [Formulário público — fazer um pedido](#3-formulário-público--fazer-um-pedido)
4. [Login e primeiro acesso](#4-login-e-primeiro-acesso)
5. [Painel de pedidos](#5-painel-de-pedidos)
6. [Estoque — catálogo e lotes](#6-estoque--catálogo-e-lotes)
7. [Entrada por Compra](#7-entrada-por-compra)
8. [Empréstimos e Permutas](#8-empréstimos-e-permutas)
9. [Setores](#9-setores)
10. [Usuários](#10-usuários)
11. [Permissões (Admin)](#11-permissões-admin)
12. [Relatórios](#12-relatórios)
13. [Importação de itens e setores por planilha](#13-importação-de-itens-e-setores-por-planilha)
14. [Perguntas frequentes / mensagens de erro](#14-perguntas-frequentes--mensagens-de-erro)

---

## 1. Visão geral

O sistema tem duas portas de entrada completamente separadas:

- **Formulário público** (`/`) — qualquer pessoa da organização pede
  material, sem login. É a única forma de abrir um pedido.
- **Painel** (`/login` → telas internas) — só a equipe do almoxarifado
  (Coordenador, Atendentes, Admin) entra aqui. É onde o pedido é
  conferido e liberado, o estoque é controlado, e os relatórios saem.

Cada pedido feito no formulário público entra numa fila. A equipe
confere item a item, dando baixa real no estoque pelo método **FEFO**
(*First Expire, First Out* — sempre consome primeiro o lote que vence
mais cedo). Todo o histórico — quem pediu, quem conferiu, de qual lote
saiu — fica registrado e pode ser consultado depois nos relatórios.

## 2. Perfis de acesso

| Perfil | Login? | O que pode fazer |
|---|---|---|
| **Solicitante** (qualquer pessoa da organização) | Não | Abrir pedido pelo formulário público. Não acessa nada mais. |
| **Atendente** | Sim | Ver a fila de pedidos, conferir/liberar pedidos, registrar Entrada por Compra e Empréstimo/Permuta, ver Estoque e Relatórios de pedidos. Ações extras dependem da matriz de permissões (ver abaixo). |
| **Coordenador** | Sim | Tudo do Atendente, mais as ações "extras" — **liberadas por padrão**, mas o Admin pode restringir depois. |
| **Admin** (global) | Sim | Superusuário — sempre tem tudo liberado. É o único que acessa a tela **Permissões**, onde decide o que Coordenador e Atendente podem fazer. Também é o único que pode promover alguém a Admin. |

### As 5 ações "extras" (configuráveis pelo Admin)

Estas 5 ações **não** são fixas por perfil — o Admin decide, na tela
**Permissões**, se Coordenador e/ou Atendente têm acesso a cada uma.
Por padrão (recém-instalado, ou logo após a migração que introduziu
esse sistema), o Coordenador nasce com as 5 liberadas e o Atendente
nasce sem nenhuma — mas isso é só o ponto de partida, editável a
qualquer momento.

| Ação | O que libera |
|---|---|
| **Ajustar estoque** | Corrigir o saldo de um lote por contagem física (tela Estoque → Ajustar). |
| **Gerenciar itens** | Cadastrar/editar itens do catálogo e editar o valor unitário de um lote já lançado. |
| **Gerenciar setores** | Cadastrar/editar os setores que aparecem no formulário público. |
| **Gestão de usuários** | Cadastrar/editar/desativar os logins do almoxarifado (Coordenador e Atendente — promover alguém a **Admin** continua exclusivo do Admin, mesmo com essa permissão liberada). |
| **Relatório de movimentações** | Ver a trilha de auditoria completa (todas as entradas/saídas/ajustes de todos os lotes). |

Ações que **não** entram nessa matriz — sempre liberadas a qualquer
login autenticado (Atendente, Coordenador ou Admin), porque são o
trabalho do dia a dia:

- Ver a fila de pedidos e conferir/liberar itens.
- Registrar Entrada por Compra.
- Registrar Empréstimo/Permuta.
- Ver o catálogo/lotes de Estoque (só não pode *editar* sem a permissão acima).
- Ver e exportar o Relatório de Pedidos, Estoque e Vencimentos (só o de
  Movimentações é restrito).

## 3. Formulário público — fazer um pedido

Endereço: a raiz do site (`/`). Não pede login.

1. **Setor Solicitante** — escolha na lista (cadastrada previamente pelo
   Coordenador/Admin, tela Setores).
2. **Responsável pelo Pedido** — nome de quem está solicitando.
3. **Buscar Material no Estoque** — digite código ou nome do item;
   escolha na lista de sugestões e clique **+ Adicionar**. Repita para
   cada item do pedido. Cada linha adicionada tem uma **Quantidade**
   editável (mínimo 1).
4. **Observação** (opcional) — texto livre, ex. "uso emergencial".
5. **Confirmar Pedido de Material** — envia o pedido. Aparece um número
   de protocolo (`#1234`) e a opção de baixar um **comprovante em PDF**.

Guarde o número de protocolo — é a referência pra acompanhar o pedido
depois com a equipe do almoxarifado (o solicitante não tem uma tela de
consulta própria; quem confirma o andamento é a equipe, pelo Painel).

## 4. Login e primeiro acesso

Endereço: `/login`. Pede **login** e **senha**.

- Todo usuário novo (criado pela tela Usuários, ou pelos scripts de
  seed na implantação) nasce com uma **senha temporária** e é obrigado
  a trocá-la no primeiro acesso — o sistema redireciona sozinho pra
  tela de troca de senha antes de liberar qualquer outra tela.
- **Trocar senha** também fica disponível a qualquer momento pelo canto
  superior do painel (**Trocar senha**, ao lado de **Sair**).
- Uma senha resetada pelo Coordenador/Admin (tela Usuários) volta a
  exigir troca no próximo login da pessoa.

## 5. Painel de pedidos

Endereço: `/painel` — tela inicial depois do login.

### Visão geral

- **Tiles de resumo**: Total, Pendentes, Parciais, Executados, Recebidos
  hoje.
- **Abas de status**: Pendente / Parcial / Executado / Todos.
- Cada linha da fila mostra setor, responsável, data/hora e status.

### Status do pedido

| Status | Significado |
|---|---|
| `Pendente` | Nenhum item foi conferido ainda. |
| `Parcial` | Pelo menos um item foi conferido, mas o pedido não está 100% atendido — seja porque ainda falta conferir algum item, seja porque algum item foi liberado em quantidade **menor** que a pedida. |
| `Executado` | Todos os itens conferidos, todos entregues na quantidade exatamente igual à solicitada. |

### Conferir um pedido (item a item)

1. Clique no pedido pra abrir o modal de conferência.
2. Cada item mostra **duas colunas**: "Qtd. solicitada" (fixa, não dá
   pra editar) e **"Qtd. dispensada"** (editável).
3. Um **checkbox "liberar"** por item decide o que está sendo confirmado
   agora — dá pra liberar só parte dos itens de um pedido e voltar
   depois pro resto (o pedido fica `Parcial` enquanto isso).
4. Se um item não tem estoque suficiente pra cobrir a quantidade
   dispensada informada, o sistema **recusa** com a mensagem "Estoque
   insuficiente" — ver seção 14 para como resolver.
5. **Confirmar** — cada item marcado gera uma baixa real de estoque
   (método FEFO, pode consumir de mais de um lote se precisar) e fica
   registrado.

**Substituir item** — quando o almoxarifado não tem exatamente o que foi
pedido mas tem um equivalente (ex.: pediram seringa com rosca, só tem
com bico), clique em **"⇄ Entregar outro item (substituição)"** dentro
do item, na conferência. Aparece uma busca pra escolher o item do
catálogo que está sendo entregue de verdade, e um campo de **motivo**
(obrigatório). A baixa de estoque sai do item **entregue**, não do
solicitado. Qualquer perfil autenticado (Atendente, Coordenador ou
Admin) pode fazer isso — não é uma permissão restrita. Depois de
confirmado, a tela mostra "Substituído por [item] — motivo: [...]" no
lugar do item original.

### "Marcar executado sem conferência" (atalho)

Na lista, selecionando um ou mais pedidos em lote, existe o atalho
**"Marcar executado sem conferência"** — confirma todos os itens ainda
pendentes desses pedidos na quantidade cheia (igual à solicitada), sem
abrir a tela item a item. Ainda dá baixa real de estoque via FEFO (não
é um atalho que finge a movimentação) — só pula a etapa manual. Se
algum item não tiver estoque suficiente, aquele pedido específico falha
e fica sinalizado pra conferência manual.

### Relatório rápido

No próprio Painel existe uma caixa de exportação rápida (saídas
executadas por período) — atalho pro Relatório de Pedidos já filtrado.

## 6. Estoque — catálogo e lotes

Endereço: `/estoque`.

### Dashboard

- **Itens em estoque crítico** — itens com saldo abaixo do mínimo
  cadastrado.
- **Lotes vencidos ou vencendo (60d)**.
- **Itens ativos no catálogo**.
- **4 grupos de vencimento**, cada um com cor própria:

| Grupo | Cor | Sinalizado no painel? |
|---|---|---|
| Vencidos | vermelho | Sim |
| Vence em até 30 dias | amarelo | Sim |
| Vence em 30–60 dias | lilás | Sim |
| Vence em 60+ dias (sem urgência) | verde | Não (informativo) |

Logo abaixo dos tiles, dois blocos listam item a item (não só o total):
**Estoque crítico** (item, saldo atual e mínimo) e **Lotes vencidos ou
vencendo** — cada linha com a mesma cor do nível (vermelho/amarelo/
lilás), nome do item, número do lote e quantidade, ordenado do mais
urgente pro menos urgente.

### Catálogo — cadastro/edição de item

Visível a qualquer login; o formulário de **Novo item**/**Editar** só
aparece pra quem tem a permissão "Gerenciar itens" (Coordenador por
padrão, configurável pelo Admin).

Campos do cadastro:

| Campo | Obrigatório? |
|---|---|
| Código | Sim — único no catálogo |
| Nome | Sim |
| Apresentação | Não (ex.: "Caixa c/ 100") |
| **Fabricante** | Não — dado de identificação do item, não do lote |
| Categoria | Sim — uma das 5 fixas: Material Médico, EPI, Higienização, Material de Expediente, Enxoval |
| Estoque mínimo | Não (0 se não preenchido) — usado pro alerta de "crítico" |
| **Valor unitário** | Não — preço de referência do item, independente do valor de cada lote (esse outro é editável na tela de Lotes, seção "Lotes" abaixo) |

Um item nunca é apagado de verdade (preserva o histórico de pedidos e
movimentações que o referenciam) — "excluir" é **Desativar**, que some
das buscas normais mas continua consultável marcando "Mostrar
inativos".

**Não existe mais** um botão de "Entrada" avulso dentro do cadastro do
item — toda entrada de estoque passa pelas telas dedicadas: **Entrada
por Compra** ou **Empréstimos e Permutas** (seções 7 e 8).

### Lotes

Cada item pode ter vários lotes (um por recebimento — nunca incrementa
um lote existente, cada entrada é um evento rastreável por si só).
Tabela "Lotes" mostra: item, número do lote, validade, quantidade
atual, **valor unitário**, origem (Compra/Doação/Empréstimo) e
sinalização de vencimento.

- **Editar valor unitário** — quem tem "Gerenciar itens" vê um botão
  **Editar** ao lado do valor unitário de cada lote; corrige só esse
  campo (nunca mexe em quantidade — isso preserva a trilha de
  auditoria).
- **Ajustar saldo** — quem tem "Ajustar estoque" vê um botão
  **Ajustar** por lote; pede o **novo saldo** (contagem física) e um
  **motivo obrigatório**; o sistema calcula a diferença sozinho e
  registra a movimentação do tipo "ajuste".

## 7. Entrada por Compra

Endereço: `/entrada-compra`. Liberado a qualquer login autenticado.

Fluxo: preencher o cabeçalho (**número da nota fiscal** + **AFM**
opcional), depois buscar e adicionar quantos itens forem necessários
numa mesma tela — cada linha vira uma entrada própria (um lote novo por
item), repetindo o mesmo cabeçalho de NF/AFM. Campos por item: lote
(opcional), validade (opcional), quantidade, valor unitário (opcional).

## 8. Empréstimos e Permutas

Endereço: `/emprestimos`. Liberado a qualquer login autenticado.

Para operações com uma **unidade externa** (fora do catálogo de
setores do sistema):

- **Direção**: "Saída" (a gente empresta material pra fora — dá baixa
  real de estoque via FEFO) ou "Entrada" (devolução ou permuta
  recebida — cria lote(s) novo(s), igual a uma Entrada por Compra).
- **Unidade de origem/destino** e **ofício** (opcional).
- Lista de itens, igual à Entrada por Compra.

Toda operação fica registrada com um histórico consultável na mesma
tela (tabela de empréstimos já feitos).

## 9. Setores

Endereço: `/setores`. Só aparece no menu pra quem tem "Gerenciar
setores" (Coordenador por padrão).

Cadastro simples: nome do setor + ativo/inativo. É a lista que alimenta
o `<select>` "Setor Solicitante" do formulário público — sem nenhum
setor cadastrado, essa lista nasce vazia.

Lista grande de setores já pronta numa planilha? O mesmo script de
importação da seção 13 também importa setores (`--setores`), separado
da planilha de itens.

## 10. Usuários

Endereço: `/usuarios`. Só aparece no menu pra quem tem "Gestão de
usuários" (Coordenador por padrão, configurável pelo Admin).

- Cadastra/edita nome, login (fixo depois de criado), senha (opcional
  no reset — deixando em branco mantém a senha atual) e perfil
  (Atendente/Coordenador; **Admin só aparece na lista de opções pra
  quem já está logado como Admin** — mesmo alguém com a permissão
  "Gestão de usuários" liberada não consegue promover ninguém a Admin,
  o backend recusa).
- Não existe DELETE — "excluir" é **Desativar** (preserva a autoria de
  pedidos já conferidos por aquela pessoa).
- Ninguém edita a própria conta por essa tela pra se desativar ou trocar
  o próprio perfil (trava contra ficar trancado pra fora sem querer,
  numa equipe pequena) — o nome próprio continua editável.

## 11. Permissões (Admin)

Endereço: `/permissoes` — **só aparece pra quem está logado como
Admin**.

Tabela com 2 linhas (Coordenador, Atendente) × 5 colunas (as ações
"extras" da seção 2) — cada célula é um checkbox. **Salvar
permissões** grava a matriz inteira de uma vez. A mudança já vale no
próximo carregamento de página de quem estiver logado com aquele
perfil (não precisa reiniciar nada).

O Admin não aparece nessa matriz — ele é superusuário implícito, sempre
com tudo liberado, em qualquer versão da matriz.

## 12. Relatórios

Endereço: `/relatorios`. Liberado a qualquer login autenticado, exceto
o de Movimentações (permissão "Relatório de movimentações").

Quatro relatórios, cada um com **prévia em tela** (botão "Ver
prévia"/"Atualizar prévia", mostra os dados numa tabela HTML antes de
baixar) e exportação em **PDF** ou **Excel**:

| Relatório | Filtros disponíveis | O que mostra |
|---|---|---|
| **Pedidos** | status, setor, período | Um pedido por linha, com **Item / Qtd. Solicitada / Qtd. Dispensada** em colunas separadas (uma linha por item do pedido, não um resumo em texto). |
| **Estoque** | — | Posição atual por item (soma dos lotes), com sinalização de item crítico. |
| **Vencimentos** | dias considerados (padrão 60) | Lotes vencendo dentro do prazo, agrupados por nível de urgência. |
| **Movimentações** | tipo (entrada/saída/ajuste), período | Trilha de auditoria completa — toda entrada/saída/ajuste de todo lote, com quem executou. |

## 13. Importação de itens e setores por planilha

Alternativa a cadastrar item por item (tela Estoque) ou setor por setor
(tela Setores) — útil pra carregar uma lista grande de uma vez (migração
de uma planilha antiga, por exemplo). Itens e setores vêm de planilhas
**separadas**, cada uma no seu próprio formato, mas o mesmo comando
importa as duas juntas.

- Script: `backend/scripts/importar_itens_planilha.py`.
- Modelo pronto (itens), já formatado: `docs/modelo_importacao_itens.xlsx`
  (cabeçalho azul = coluna obrigatória, verde = opcional; comentários
  na célula do cabeçalho explicam cada uma; 4 linhas de exemplo).
- Roda **sempre via API** (nunca acesso direto ao banco) — respeita as
  mesmas validações do cadastro manual pela tela.
- **Idempotente nos dois casos** — item cujo código já existir, ou
  setor cujo nome já existir, é pulado (seguro rodar de novo se a
  importação parar no meio).

**Planilha de itens — colunas obrigatórias**: `codigo`, `nome`,
`apresentacao`, `categoria` (uma das 5 fixas — aceita a chave ou o
rótulo).

**Planilha de itens — colunas opcionais**: `estoque_minimo` (0 se vazio
ou não numérico) e `fabricante` — as duas sem nenhuma relação com
estoque, viram direto o cadastro do item; `quantidade` (se preenchida,
já registra uma entrada — nesse caso `numero_lote`, `data_validade`,
`valor_unitario` e `numero_nota_fiscal` também podem ser preenchidos,
viram atributos desse lote).

**Planilha de setores** — uma coluna só, obrigatória: `nome`.

Uso:

```bash
# itens
python scripts/importar_itens_planilha.py caminho/itens.xlsx \
    --api-url http://localhost:8000 --login coordenador --senha "..."

# itens + setores juntos
python scripts/importar_itens_planilha.py caminho/itens.xlsx --setores caminho/setores.xlsx \
    --api-url http://localhost:8000 --login coordenador --senha "..."

# só setores
python scripts/importar_itens_planilha.py --setores caminho/setores.xlsx \
    --api-url http://localhost:8000 --login coordenador --senha "..."
```

## 14. Perguntas frequentes / mensagens de erro

**"Estoque insuficiente para o item id=X: disponível Y, necessário Z"**
— apareceu ao tentar conferir um pedido ou registrar uma saída de
empréstimo. Significa exatamente o que diz: não existe saldo suficiente
naquele item pra liberar a quantidade pedida. Duas saídas:
1. Registrar uma **Entrada por Compra** daquele item primeiro, depois
   conferir normalmente; ou
2. Na conferência, colocar a **"Qtd. dispensada" = 0** pra esse item —
   marca como "não atendido" sem mexer em estoque, e o pedido segue
   `Parcial` (ou você conclui o restante dos itens do pedido).

**"Perfil sem permissão para esta operação" (403)** — a ação clicada
depende de uma das 5 permissões configuráveis (seção 2) e o seu perfil
não tem ela liberada no momento. Só o Admin pode mudar isso, na tela
Permissões.

**"Você não pode desativar a própria conta" / "Você não pode alterar o
próprio perfil de acesso"** — trava de segurança da tela Usuários:
ninguém se autodesativa ou se autopromove/rebaixa por lá. Peça pra
outra pessoa com a permissão de Gestão de usuários fazer a mudança, ou,
no caso de virar Admin, só o Admin já logado consegue.

**Pedido não aparece na fila do Painel** — confira se o filtro de aba
não está escondendo (ex. pedido já `Executado` não aparece na aba
"Pendente").

**Formulário público mostra "Carregando setores..." sem nunca
carregar** — normalmente é o backend fora do ar ou bloqueado por
CORS/firewall; confira com quem administra o servidor.
