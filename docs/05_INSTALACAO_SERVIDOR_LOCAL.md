# Instalação — Servidor Local (computador novo)

Guia passo a passo para instalar o Almoxarifado do zero num computador novo,
do build até o sistema no ar na rede interna — **sem depender de internet**
depois de instalado (só precisa de internet durante a instalação, pra baixar
código/pacotes). Cobre as duas rotas possíveis:

- **[Rota A — Docker](#rota-a--docker-recomendado)**: mais simples, menos
  passos manuais, mesmo método já validado no ambiente de teste (VPS).
- **[Rota B — Instalação nativa (sem Docker)](#rota-b--instalação-nativa-sem-docker)**:
  segue a decisão original do projeto (`docs/00_PROJETO_ALMOXARIFADO.md`:
  "sem Docker"), instalando Python/Node/PostgreSQL direto no sistema
  operacional do servidor.

Escolha uma das duas — não precisa fazer as duas. Se não tiver certeza,
use a Rota A.

## 0. Checklist rápido (antes de considerar "pronto")

- [ ] PostgreSQL com senha forte gerada na hora (nunca a de um `.env.example`)
- [ ] `JWT_SECRET_KEY` gerado novo — nunca reaproveitar o de outra instalação
- [ ] Servidor com **IP fixo** na rede interna
- [ ] Backend rodando como serviço (reinicia sozinho se o servidor reiniciar)
- [ ] Frontend buildado apontando para o **IP do servidor**, nunca `localhost`
- [ ] Os 5 usuários reais cadastrados (coordenador + 4 atendentes) — **não** os
      de teste do seed, ou pelo menos com as senhas temporárias já trocadas
- [ ] Firewall liberando as portas só para a rede interna, nunca para a internet
- [ ] Backup (`pg_dump`) agendado e testado pelo menos uma vez com restauração

## 1. Preparar o servidor

- Um computador ou mini-PC dedicado, ligado na rede interna (o mesmo
  princípio do documento de planejamento: 6 a 15 estações acessando por
  navegador, servidor único).
- **IP fixo**: reserva de DHCP pelo endereço MAC (configurar no roteador/
  switch da rede), ou IP estático direto na máquina. Todas as estações vão
  apontar para esse IP — se ele mudar depois, o sistema para de funcionar
  para todo mundo.
  - Descobrir o IP atual da máquina: `ipconfig` (Windows, procurar "Endereço
    IPv4") ou `ip addr` / `hostname -I` (Linux).
- Windows ou Linux — os passos abaixo cobrem os dois.

## 2. Obter o código

```bash
git clone https://github.com/odlaoraugusto/Almoxarifado.git
cd Almoxarifado
```

Repositório público — não precisa de login/token do GitHub para clonar.

---

## Rota A — Docker (recomendado)

### A.1 — Instalar o Docker

- **Windows**: instalar o [Docker Desktop](https://www.docker.com/products/docker-desktop/)
  (exige WSL2, o instalador já orienta como ativar). Depois de instalado,
  abrir o Docker Desktop uma vez e confirmar que está rodando (ícone na
  bandeja do sistema).
- **Linux**: seguir o guia oficial de instalação do Docker Engine para a
  distribuição (`docs.docker.com/engine/install/`) — já inclui o plugin
  `docker compose`. Depois, habilitar o serviço:
  ```bash
  sudo systemctl enable --now docker
  ```

Confirmar que funcionou:

```bash
docker --version
docker compose version
```

### A.2 — Configurar as variáveis de ambiente

```bash
cp .env.local.example .env
```

Editar o `.env` recém-criado (raiz do repositório, não dentro de `backend/`
nem `frontend/`) com os valores reais:

| Variável | Como preencher |
|---|---|
| `BACKEND_PORT` | porta do host pro backend — só mude se `8000` já estiver em uso por outro serviço nesta máquina (default `8000` se deixar em branco) |
| `FRONTEND_PORT` | porta do host pro frontend — só mude se `80` já estiver em uso (default `80`) |
| `POSTGRES_PASSWORD` | gerar uma senha forte, ex.: `python -c "import secrets; print(secrets.token_urlsafe(24))"` (ou `openssl rand -base64 24`) |
| `DATABASE_URL` | mesma senha do `POSTGRES_PASSWORD`, colada dentro da URL (ver comentário no próprio arquivo) |
| `JWT_SECRET_KEY` | gerar novo — `python -c "import secrets; print(secrets.token_hex(32))"` |
| `HOSPITAL_NOME` / `HOSPITAL_ORGANIZACAO` | nome real da instituição |
| `CORS_ORIGINS` | `http://SEU_IP_FIXO` + `:FRONTEND_PORT` se não for `80` (o IP da seção 1, **sem** `localhost`) |
| `VITE_API_URL` | `http://SEU_IP_FIXO:BACKEND_PORT` (a porta do **backend**, mesmo valor de `BACKEND_PORT`) |
| `VITE_ORGANIZACAO` / `VITE_HOSPITAL_NOME` / `VITE_HOSPITAL_SIGLA` | mesmos nomes reais, exibidos na tela |

**Exemplo** — se já houver outro serviço usando `8000`/`80` nesta máquina
e você optar por `8001`/`8080` (IP fixo `192.168.10.50`, por exemplo):

```
BACKEND_PORT=8001
FRONTEND_PORT=8080
CORS_ORIGINS=http://192.168.10.50:8080
VITE_API_URL=http://192.168.10.50:8001
```

**Erro mais comum nesta etapa**: deixar `VITE_API_URL`/`CORS_ORIGINS` como
`localhost`. Funciona perfeito testando na própria máquina do servidor,
mas quebra para todas as outras estações, porque cada navegador delas
precisa saber o IP de rede do servidor, não o "localhost" dele mesmo.

### A.3 — Subir os containers

```bash
docker compose -f docker-compose.local.yml up -d --build
```

Isso builda e sobe 3 containers: `almoxarifado-postgres`,
`almoxarifado-backend` (já roda `alembic upgrade head` sozinho ao iniciar)
e `almoxarifado-frontend` (nginx servindo o build de produção). Conferir
que os três subiram:

```bash
docker compose -f docker-compose.local.yml ps
docker compose -f docker-compose.local.yml logs backend --tail 30
```

### A.4 — Popular os dados iniciais (só na primeira vez)

```bash
docker compose -f docker-compose.local.yml exec backend python scripts/seed_usuarios.py
docker compose -f docker-compose.local.yml exec backend python scripts/seed_setores.py
```

Cria os 5 logins (`coordenador`, `atendente1`..`atendente4`) com senha
temporária `Almox@2026` (troca obrigatória no primeiro login) e os setores
padrão. Pule esta etapa em atualizações futuras — só roda uma vez, na
instalação nova.

### A.5 — Testar

De qualquer computador **da mesma rede**, abrir o navegador em
`http://SEU_IP_FIXO` (ou `http://SEU_IP_FIXO:FRONTEND_PORT`, se tiver
mudado a porta do frontend — não precisa digitar `:80`, só as portas
diferentes de 80) — deve aparecer o formulário público. Em
`http://SEU_IP_FIXO/login` (mesma porta), testar o login do coordenador.

Pule para a [seção 4](#4-rede-e-firewall).

---

## Rota B — Instalação nativa (sem Docker)

### B.1 — Instalar o PostgreSQL

- **Windows**: baixar o instalador oficial em
  `postgresql.org/download/windows` (versão 14+) e instalar normalmente —
  ele já registra como serviço do Windows automaticamente. Definir uma
  senha forte para o usuário `postgres` durante a instalação.
- **Linux**: `sudo apt install postgresql` (Debian/Ubuntu) ou equivalente
  da distribuição — já instala como serviço `systemd` habilitado.

Criar o banco e um usuário dedicado (evitar usar o superusuário `postgres`
direto em produção):

```sql
CREATE USER almoxarifado WITH PASSWORD 'senha-forte-gerada-aqui';
CREATE DATABASE almoxarifado OWNER almoxarifado;
```

Se alguma estação de trabalho vai rodar algo que precise falar direto com
o Postgres (normalmente não é o caso — só o backend fala com o banco),
ajustar o `pg_hba.conf` para aceitar conexões da rede interna. Por padrão,
deixar o Postgres escutando só em `localhost` (o backend roda na mesma
máquina) é mais seguro e é o suficiente aqui.

### B.2 — Instalar o Python e preparar o backend

Requisito: Python 3.12+ (`python.org/downloads`, ou `apt install python3.12`
no Linux).

```bash
cd backend
python -m venv .venv

.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux

pip install -r requirements.txt

copy .env.example .env          # Windows
# cp .env.example .env          # Linux
```

Editar `backend/.env` com os valores reais:

| Variável | Valor de produção |
|---|---|
| `DATABASE_URL` | `postgresql+psycopg2://almoxarifado:senha-forte-gerada-aqui@localhost:5432/almoxarifado` |
| `JWT_SECRET_KEY` | gerar novo — `python -c "import secrets; print(secrets.token_hex(32))"` |
| `HOSPITAL_NOME` / `HOSPITAL_ORGANIZACAO` | nome real da instituição |
| `CORS_ORIGINS` | `http://SEU_IP_FIXO` (o IP da seção 1 — **nunca** `localhost`) |

Rodar as migrations e criar os usuários/setores iniciais:

```bash
alembic upgrade head
python scripts/seed_usuarios.py
python scripts/seed_setores.py
```

### B.3 — Rodar o backend como serviço

Não deixar rodando manualmente num terminal aberto — se alguém fechar o
terminal ou o servidor reiniciar, o sistema cai.

**Windows — [NSSM](https://nssm.cc/)** (mais simples que o Agendador de
Tarefas para manter um processo de longa duração vivo e reiniciando
sozinho):

```bash
nssm install AlmoxarifadoAPI "C:\caminho\Almoxarifado\backend\.venv\Scripts\uvicorn.exe" "app.main:app --host 0.0.0.0 --port 8000"
nssm set AlmoxarifadoAPI AppDirectory "C:\caminho\Almoxarifado\backend"
nssm start AlmoxarifadoAPI
```

**Linux — systemd** (criar `/etc/systemd/system/almoxarifado-backend.service`):

```ini
[Unit]
Description=Almoxarifado API
After=network.target postgresql.service

[Service]
User=almoxarifado
WorkingDirectory=/opt/almoxarifado/backend
ExecStart=/opt/almoxarifado/backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now almoxarifado-backend
```

Note o `--host 0.0.0.0` (não `127.0.0.1`) — necessário para que as outras
estações da rede consigam alcançar o backend.

### B.4 — Instalar o Node.js e buildar o frontend

Requisito: Node.js 20+ (`nodejs.org`).

```bash
cd frontend
copy .env.example .env    # Windows
# cp .env.example .env    # Linux
```

Editar `frontend/.env` com o **IP real do servidor**:

```
VITE_API_URL=http://SEU_IP_FIXO:8000
VITE_ORGANIZACAO=Nome da Organização/Rede
VITE_HOSPITAL_NOME=Nome do Hospital
VITE_HOSPITAL_SIGLA=SIGLA
```

```bash
npm install
npm run build
```

Isso gera `frontend/dist/` — arquivos estáticos prontos, **sem precisar do
Node.js rodando em produção**. Servir esses arquivos com qualquer servidor
web simples:

- **Windows**: IIS apontando para a pasta `dist/`, ou instalar o `nginx`
  para Windows.
- **Linux**: `nginx` servindo `dist/` como raiz — o `frontend/nginx.conf`
  deste repositório já tem a configuração mínima certa (inclusive o
  `try_files` necessário para as rotas do React Router funcionarem):

  ```bash
  sudo cp frontend/nginx.conf /etc/nginx/sites-available/almoxarifado
  sudo sed -i 's#/usr/share/nginx/html#/opt/almoxarifado/frontend/dist#' /etc/nginx/sites-available/almoxarifado
  sudo ln -s /etc/nginx/sites-available/almoxarifado /etc/nginx/sites-enabled/
  sudo systemctl reload nginx
  ```

### B.5 — Testar

De qualquer computador da mesma rede, abrir `http://SEU_IP_FIXO` — deve
aparecer o formulário público. Em `http://SEU_IP_FIXO/login`, testar o
login do coordenador.

---

## 3. Primeiro acesso

1. Logar como `coordenador` / `Almox@2026` — o sistema força a troca de
   senha no primeiro acesso.
2. Repetir o login/troca de senha para `atendente1`..`atendente4`, ou
   trocar os logins/nomes pela tela **Usuários** para os nomes reais da
   equipe (exclusivo do Coordenador).
3. Cadastrar o catálogo de itens de verdade em **Estoque** — o seed não
   cria nenhum item (só setores e usuários), de propósito, para não
   inventar dado de produção.
4. Testar os fluxos principais uma vez com dado real: um pedido pelo
   formulário público, uma conferência (inclusive uma parcial, de
   propósito, para confirmar que o status calcula certo), uma Entrada por
   Compra, um Ajuste de estoque.

## 4. Rede e firewall

Liberar no firewall do servidor, **só para a sub-rede interna**, nunca
para a internet:
- Porta do backend (`8000` por padrão, ou o valor que você colocou em
  `BACKEND_PORT` no `.env`, se mudou por conflito com outro app)
- Porta do frontend (`80` por padrão, ou `FRONTEND_PORT`)
- Porta 5432 (Postgres) **não precisa ficar liberada** — nem no Docker
  (fica só na rede interna dos containers) nem na instalação nativa (só o
  backend, na mesma máquina, fala com ele).

## 5. Backup

```bash
pg_dump -Fc -U almoxarifado almoxarifado > /backup/almoxarifado_$(date +%F).dump
```

Com Docker, rodar de dentro do container:

```bash
docker compose -f docker-compose.local.yml exec postgres pg_dump -Fc -U almoxarifado almoxarifado > /backup/almoxarifado_$(date +%F).dump
```

**Windows** — Agendador de Tarefas, ação diária chamando um `.bat` com o
comando acima. **Linux** — `cron`:

```
0 2 * * * pg_dump -Fc -U almoxarifado almoxarifado > /backup/almoxarifado_$(date +\%F).dump
```

O destino do backup deve ser um disco ou pasta de rede **separada** do
servidor principal. E testar a restauração pelo menos uma vez antes de
confiar nela:

```bash
pg_restore -d almoxarifado_teste -U postgres /backup/almoxarifado_2026-08-27.dump
```

Um backup nunca testado é uma suposição, não uma garantia.

## 6. Atualizar depois de uma mudança no código

**Docker**:

```bash
git pull
docker compose -f docker-compose.local.yml up -d --build
```

Migrations novas rodam sozinhas (o backend chama `alembic upgrade head` a
cada início). Se só o frontend mudou, pode reconstruir só ele:
`docker compose -f docker-compose.local.yml up -d --build frontend`.

**Nativa**:

```bash
git pull
cd backend && .venv\Scripts\activate && pip install -r requirements.txt && alembic upgrade head
# reiniciar o serviço (nssm restart AlmoxarifadoAPI / systemctl restart almoxarifado-backend)

cd ../frontend && npm install && npm run build
# recopiar dist/ para onde o nginx/IIS está servindo, se o caminho não for direto
```

## 7. Checklist final

Repita o checklist da seção 0 depois de tudo no ar — em especial, teste o
backup com uma restauração de verdade antes de considerar a instalação
pronta para uso real.
