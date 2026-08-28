# Guia Prático — Como Usar o Almoxarifado

Passo a passo das tarefas do dia a dia. Se você quer entender o
sistema por trás de cada tela (permissões, o que cada campo significa),
veja o [`MANUAL_DO_SISTEMA.md`](MANUAL_DO_SISTEMA.md) — este guia aqui
é só "como eu faço X".

## Sumário

1. [Antes de começar](#1-antes-de-começar)
2. [Como fazer um pedido](#2-como-fazer-um-pedido)
3. [Como conferir e liberar um pedido (saída)](#3-como-conferir-e-liberar-um-pedido-saída)
4. [Como registrar uma entrada de estoque (compra)](#4-como-registrar-uma-entrada-de-estoque-compra)
5. [Como registrar um empréstimo ou permuta](#5-como-registrar-um-empréstimo-ou-permuta)
6. [Como fazer um ajuste de estoque](#6-como-fazer-um-ajuste-de-estoque)
7. [Como gerar um relatório](#7-como-gerar-um-relatório)
8. [Outras tarefas](#8-outras-tarefas)

---

## 1. Antes de começar

**Se você só vai pedir material** (não faz parte da equipe do
almoxarifado): não precisa de login nenhum. Vá direto pra seção 2.

**Se você é da equipe do almoxarifado** (Atendente, Coordenador ou
Admin):

1. Acesse `/login`.
2. Digite seu **login** e **senha**.
3. No primeiro acesso (ou depois de um reset), o sistema pede pra você
   trocar a senha antes de liberar qualquer tela — é obrigatório,
   digite a senha atual + a nova duas vezes.
4. Depois de logado, o menu do lado mostra só as telas que você tem
   permissão de usar — se alguma tela deste guia não aparecer pra você,
   é porque seu perfil não tem essa permissão liberada (fale com o
   Coordenador ou o Admin).

---

## 2. Como fazer um pedido

Abra a página inicial do sistema (endereço raiz, sem `/login`).

1. Em **Setor Solicitante**, escolha seu setor na lista.
2. Em **Responsável pelo Pedido**, digite seu nome.
3. Em **Buscar Material no Estoque**, digite o código ou o nome do
   item — conforme você digita, aparecem sugestões. Clique na sugestão
   certa.
4. Clique em **+ Adicionar**. O item entra na tabela de baixo, com
   quantidade **1** por padrão — clique no campo de quantidade e ajuste
   se precisar.
5. Repita os passos 3 e 4 pra cada item que você precisa.
6. Se quiser, escreva algo em **Observação** (ex.: "uso emergencial").
7. Clique em **Confirmar Pedido de Material**.

Pronto — aparece uma tela de confirmação com um **número de
protocolo** (ex.: `#1234`). Anote esse número: é como você vai
acompanhar o pedido depois com a equipe do almoxarifado. Você também
pode clicar em **Baixar Comprovante em PDF** pra guardar um
comprovante.

> Esse formulário não pede login — qualquer pessoa da organização pode
> usar. Só a equipe do almoxarifado consegue ver a fila de pedidos e
> liberar o material.

---

## 3. Como conferir e liberar um pedido (saída)

Isso é o que dá baixa de verdade no estoque. Só quem tem login acessa.

1. Entre em **Painel de pedidos**.
2. Encontre o pedido — use as abas (Pendente / Parcial / Executado /
   Todos), a busca, ou os filtros de setor/data se precisar.
3. Clique no pedido pra abrir a tela de conferência.
4. Para cada item da lista:
   - **Qtd. solicitada** é fixa (o que a pessoa pediu, não dá pra
     mudar).
   - **Qtd. dispensada** é o que você está de fato entregando agora —
     edite se for entregar menos do que foi pedido (ex.: só tem 3 das
     5 pedidas).
   - O **checkbox** ao lado do nome do item decide se aquele item está
     sendo confirmado agora. Desmarque um item se ainda não vai
     entregá-lo — você confirma o resto do pedido depois, numa
     conferência seguinte.
5. Clique em **Confirmar itens marcados**.

O sistema dá baixa real no estoque (sempre do lote que vence primeiro
— você não escolhe o lote manualmente). O pedido muda de status
sozinho:

- **Parcial** — ainda falta conferir algo, ou algum item saiu em
  quantidade menor que a pedida.
- **Executado** — tudo conferido, tudo na quantidade certa.

### Quando não tem exatamente o item pedido — substituir

Às vezes o pedido pede um material específico (ex.: "seringa com
rosca") mas só tem um equivalente em estoque (ex.: "seringa com bico").
Nesse caso:

1. Na tela de conferência, dentro do item, clique em
   **"⇄ Entregar outro item (substituição)"**.
2. Busque e selecione o item que você está entregando de verdade.
3. Escreva o **motivo** da substituição (obrigatório) — ex.: "só tinha
   com bico, sem rosca no estoque".
4. Preencha a quantidade normalmente e confirme como de costume.

O estoque é descontado do item que você **realmente entregou**, não do
que foi pedido originalmente. Depois de confirmado, a tela mostra
"Substituído por [item] — motivo: [...]" pra deixar registrado.

### Liberar vários pedidos de uma vez, sem conferir item a item

Se você confia que vai entregar exatamente o que foi pedido em vários
pedidos, sem precisar abrir um por um:

1. Na lista do Painel, marque o checkbox dos pedidos que quer liberar
   (só aparece pra pedidos ainda não totalmente executados).
2. Clique em **Marcar executado (sem conferência)**.

Isso ainda dá baixa real de estoque em cada item — só pula a etapa
manual. Se algum item de algum pedido não tiver estoque suficiente,
**aquele pedido específico** falha e continua na fila pra você conferir
manualmente (os outros pedidos selecionados são processados
normalmente).

### "Estoque insuficiente" — o que fazer

Se aparecer essa mensagem ao tentar liberar um item, é porque não tem
saldo suficiente daquele item pra entregar a quantidade pedida. Duas
saídas:

- Registre uma **entrada** desse item primeiro (seção 4), depois volte
  e confira o pedido; ou
- Na conferência, coloque a quantidade dispensada como **0** — marca
  como "não atendido" sem mexer em estoque, e você resolve depois.

---

## 4. Como registrar uma entrada de estoque (compra)

Use isso quando chega material novo de uma compra.

1. Entre em **Entrada por Compra**.
2. Preencha o **Nº nota fiscal** (obrigatório) e o **Nº AFM**, se
   tiver (opcional).
3. Em **Buscar item do catálogo**, digite o código ou nome, escolha o
   item na sugestão, clique em **+ Adicionar**. Repita pra cada item
   da nota fiscal.
4. Pra cada item adicionado na tabela, preencha:
   - **Quantidade** (obrigatório).
   - **Nº do lote** (opcional).
   - **Validade** (opcional — deixe em branco se o item não vence).
   - **Valor unit.** (opcional).
5. Clique em **Registrar entrada**.

Cada item vira um **lote novo** no estoque (mesmo que já exista lote
do mesmo item — cada recebimento é registrado separado, nunca soma em
cima de um lote existente).

---

## 5. Como registrar um empréstimo ou permuta

Use isso só para operações com uma **unidade de fora** do hospital
(outra instituição) — não confundir com pedido interno de um setor.

1. Entre em **Empréstimos e Permutas**.
2. Escolha a **Direção**:
   - **Saída (emprestar pra fora)** — o hospital está emprestando
     material; dá baixa real no nosso estoque.
   - **Entrada (devolução / permuta recebida)** — estamos recebendo de
     volta ou em troca; cria lote(s) novo(s), igual a uma entrada de
     compra.
3. Preencha a **Unidade de origem** (obrigatório — nome da instituição)
   e o **Nº do ofício**, se tiver.
4. Adicione os itens (mesma busca das outras telas). Se a direção for
   "Entrada", também dá pra preencher lote/validade/valor por item.
5. Clique em **Confirmar registro**.

O histórico completo de empréstimos/permutas já feitos fica logo
abaixo do formulário, na mesma tela.

---

## 6. Como fazer um ajuste de estoque

Use isso só pra corrigir uma divergência encontrada numa **contagem
física** — nunca pra registrar uma saída ou entrada normal (isso é
sempre pelas telas 3/4/5).

> Precisa da permissão "Ajustar estoque" (Coordenador por padrão,
> configurável pelo Admin). Se você não vir o botão **Ajustar**
> descrito abaixo, é porque seu perfil não tem essa permissão liberada
> — fale com o Coordenador ou o Admin.

1. Entre em **Estoque**.
2. Role até a tabela **Lotes**, encontre o lote que precisa corrigir.
3. Clique em **Ajustar**.
4. Em **Novo saldo (contagem física)**, digite o saldo que você contou
   de verdade (não a diferença — o saldo final).
5. Escreva o **Motivo** (obrigatório).
6. Clique em **Confirmar ajuste**.

O sistema calcula a diferença sozinho e registra o ajuste na trilha de
auditoria (visível no Relatório de Movimentações).

### Corrigir só o valor unitário de um lote (sem mexer em quantidade)

Isso é diferente do ajuste acima — é só pra corrigir um preço lançado
errado ou esquecido, sem tocar no saldo:

1. Na mesma tabela **Lotes**, clique em **Editar** ao lado do "Valor
   unit." do lote.
2. Digite o valor certo.
3. Clique em **Salvar**.

---

## 7. Como gerar um relatório

1. Entre em **Relatórios**.
2. Escolha a aba: **Pedidos**, **Estoque atual**, **Vencimentos
   próximos** ou **Movimentações (auditoria)** — essa última só
   aparece pra quem tem a permissão correspondente.
3. Ajuste os filtros disponíveis pra aquele relatório (status, período,
   dias de vencimento).
4. Clique em **Ver prévia** pra conferir os dados na tela antes de
   baixar (o botão vira **Atualizar prévia** se você mudar os filtros
   depois).
5. Clique em **Exportar Excel** ou **Exportar PDF** pra baixar o
   arquivo.

O Painel também tem um atalho de relatório rápido (saídas executadas
por período), já filtrado — útil pro fechamento do dia sem precisar
entrar na tela de Relatórios.

---

## 8. Outras tarefas

Tarefas menos frequentes, mas que você vai precisar em algum momento:

| Tarefa | Onde | Quem pode |
|---|---|---|
| Cadastrar/editar um item do catálogo | Estoque → "Novo item do catálogo" / botão Editar na tabela | Permissão "Gerenciar itens" |
| Desativar um item (não é apagar — some das buscas normais) | Estoque → botão "Desativar" na linha do item | Permissão "Gerenciar itens" |
| Cadastrar/editar um setor solicitante | Setores | Permissão "Gerenciar setores" |
| Cadastrar/editar/desativar um login da equipe | Usuários | Permissão "Gestão de usuários" |
| Importar um catálogo grande de itens/setores por planilha, de uma vez | `backend/scripts/importar_itens_planilha.py` (linha de comando) | Ver `docs/05_INSTALACAO_SERVIDOR_LOCAL.md`, seção 3 |
| Decidir o que Coordenador/Atendente podem fazer | Permissões | Exclusivo do Admin |
| Trocar a própria senha | Link "Trocar senha" no topo do menu | Qualquer login |

Detalhes de cada tela (campos, regras, mensagens de erro) estão no
[`MANUAL_DO_SISTEMA.md`](MANUAL_DO_SISTEMA.md).
