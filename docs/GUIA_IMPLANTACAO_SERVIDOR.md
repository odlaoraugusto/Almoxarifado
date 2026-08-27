# Guia prático de build e implantação — máquina oficial do servidor

Passo a passo real, na ordem certa, para quando o código for trazido
(via `git clone`) para o computador definitivo do servidor. Baseado no
`docs/05_INSTALACAO_SERVIDOR_LOCAL.md` (referência genérica, cobre Docker
e nativo) + no guia equivalente do projeto irmão (farmácia), adaptado
pro cenário real desta máquina: **instalação nativa** (sem Docker,
mesmo padrão já usado pela farmácia nesta mesma máquina).

**Portas deste sistema no servidor**: já existem 3 outros apps nesta
máquina — 2 apps em `8000`/`8001` (backend) e `80`/`8080` (frontend), e o
sistema da farmácia em `8002` (backend) e `8081` (frontend). O
almoxarifado é o **4º app**, usando **`8003`** (backend) e **`8082`**
(frontend). Todo comando/config abaixo já está com essas portas.

**PostgreSQL já está instalado** nesta máquina (a farmácia usa) — não
precisa instalar de novo, só criar um banco e um usuário próprios do
almoxarifado dentro da instância existente (nunca reaproveitar o usuário
da farmácia).

**Convenção usada neste guia**: cada bloco de comando tem uma etiqueta
antes dizendo onde rodar:
- 🟢 **Janela comum** — PowerShell normal, sem "Executar como
  administrador". A maioria dos comandos é assim.
- 🔴 **Janela como Administrador** — clique direito no ícone do
  PowerShell → "Executar como administrador", aprovar o UAC. Só os
  pontos marcados precisam disso.

Como o usuário desta instalação já é administrador local, o item "a
conta é admin de verdade?" do checklist da farmácia não se aplica aqui —
mantidas só as outras duas checagens (foram problemas reais na rodada de
teste local e não têm relação com a conta usada).

## 0. Antes de começar — checklist da máquina

🟢 **Janela comum.**

```powershell
# cmd.exe (64-bit) existe? (se não existir, npm/instaladores quebram)
Test-Path C:\Windows\system32\cmd.exe

# Windows está atualizado? (ucrtbase.dll desatualizado quebra instaladores
# nativos com erros como STATUS_STACK_BUFFER_OVERRUN)
(Get-Item C:\Windows\System32\ucrtbase.dll).VersionInfo.FileVersion
# Se a versão parecer muito antiga comparado a outra máquina saudável,
# rodar Windows Update antes de seguir.
```

## 1. Trazer o código para o servidor

🟢 **Janela comum.** O repositório é público — `git clone` direto, sem
precisar de credencial:

```powershell
cd C:\caminho
git clone https://github.com/odlaoraugusto/Almoxarifado.git ALMOXARIFADO
cd ALMOXARIFADO
```

Isso já traz tudo que interessa (o `.gitignore` do projeto exclui
`.venv/`, `node_modules/` e qualquer `.env` real — só ficam os
`.env.*.example`). Nada a excluir manualmente, diferente de uma cópia
por pasta/rede.

**Para atualizar depois de uma mudança no código** (nova versão,
correção, etc.), sem precisar clonar de novo:

```powershell
cd C:\caminho\ALMOXARIFADO
git pull
```

Depois de um `git pull` que mexeu no backend, rodar de novo os passos de
migração (seção 3) e, se mexeu no frontend, o rebuild (seção 4) — um
`git pull` sozinho não reinicia os serviços nem reconstrói nada.

## 2. Banco de dados — criar o schema do almoxarifado no Postgres existente

🟢 **Janela comum** — não precisa de admin nem de instalador, o
PostgreSQL já está rodando (serviço da farmácia). Gerar uma senha forte
antes:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(24))"
```

Guardar o valor num cofre de senhas (não em texto plano em lugar
nenhum), depois criar o usuário e o banco via `psql` (pede a senha do
superusuário `postgres`, a mesma já usada para instalar a farmácia):

```powershell
& "C:\Program Files\PostgreSQL\17\bin\psql.exe" -U postgres
```

```sql
CREATE USER almoxarifado WITH PASSWORD 'senha-forte-gerada-aqui';
CREATE DATABASE almoxarifado OWNER almoxarifado;
\q
```

**`pg_hba.conf` normalmente não precisa mudar**: o backend roda nesta
mesma máquina e conecta em `localhost`, e o instalador oficial do
PostgreSQL já vem com uma regra padrão liberando `127.0.0.1/32` para
qualquer usuário/banco. Só mexer nisso se a conexão falhar com erro de
autenticação/rede (aí sim, adicionar uma linha `host almoxarifado
almoxarifado 127.0.0.1/32 scram-sha-256` no mesmo arquivo já editado
para a farmácia).

## 3. Backend — porta 8003

🟢 **Janela comum.**

```powershell
cd "C:\caminho\ALMOXARIFADO\backend"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Editar `backend\.env` (arquivo criado agora, novo — nenhum valor vem
copiado da máquina de teste):

```dotenv
DATABASE_URL=postgresql+psycopg2://almoxarifado:<senha-do-passo-2>@localhost:5432/almoxarifado
JWT_SECRET_KEY=<gerar novo: python -c "import secrets; print(secrets.token_hex(32))">
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480
HOSPITAL_NOME=<nome real da instituição>
HOSPITAL_ORGANIZACAO=<nome real da organização/rede>
CORS_ORIGINS=http://SEU_IP_FIXO:8082
```

🟢 **Janela comum.** Migrations e dados iniciais:

```powershell
.venv\Scripts\python.exe -m alembic upgrade head
.venv\Scripts\python.exe scripts\seed_usuarios.py
.venv\Scripts\python.exe scripts\seed_setores.py
.venv\Scripts\python.exe scripts\seed_admin.py
```

`seed_usuarios.py` não recebe argumentos (diferente do script da
farmácia) — cria sempre os 5 logins fixos (`coordenador`,
`atendente1`..`atendente4`) com a senha temporária `Almox@2026` e
`deve_trocar_senha=true`. Trocar os nomes/senhas reais depois pela tela
**Usuários**, logado como coordenador.

`seed_admin.py` cria um 6º login, separado dos 5 acima: o **Admin
global** (`admin` / senha temporária `Admin@2026`), a única conta que
acessa a tela **Permissões** e decide o que Coordenador e Atendente
podem fazer (ajustar estoque, gerenciar itens/setores, gestão de
usuários, relatório de movimentações — tudo isso nasce liberado só pro
Coordenador, igual ao comportamento antigo, até o Admin mudar). Aceita
`--login`/`--nome` opcionais; sem eles usa `admin` / "Administrador do
Sistema". Idempotente.

Se houver uma planilha de estoque já existente para importar (catálogo +
saldo inicial) — **mantido como já estava**: ver
`docs/05_INSTALACAO_SERVIDOR_LOCAL.md` seção 3, script
`backend/scripts/importar_itens_planilha.py`, modelo pronto em
`docs/modelo_importacao_itens.xlsx`.

### Serviço do backend (NSSM) — porta 8003

🔴 **Janela como Administrador** — os comandos abaixo recusam com
"Administrator access is needed" numa janela comum, sem nem tentar abrir
um prompt de UAC.

```powershell
# instalar NSSM (se ainda não tiver): winget install NSSM.NSSM
nssm install AlmoxarifadoAPI "C:\caminho\ALMOXARIFADO\backend\.venv\Scripts\uvicorn.exe" "app.main:app --host 0.0.0.0 --port 8003"
nssm set AlmoxarifadoAPI AppDirectory "C:\caminho\ALMOXARIFADO\backend"
nssm start AlmoxarifadoAPI
```

🟢 **Janela comum** para verificar: `Get-Service AlmoxarifadoAPI` deve
mostrar `Running`, e `http://localhost:8003/docs` deve responder mesmo
sem nenhum terminal aberto.

## 4. Frontend — porta 8082

🟢 **Janela comum**, do início ao fim desta seção.

```powershell
cd "C:\caminho\ALMOXARIFADO\frontend"
copy .env.example .env
```

Editar `frontend\.env` com o **IP real do servidor** e a porta 8003 do
backend (não `localhost` — é o navegador de cada estação, não o
servidor, que faz essa chamada):

```dotenv
VITE_API_URL=http://SEU_IP_FIXO:8003
VITE_ORGANIZACAO=<nome real da organização/rede>
VITE_HOSPITAL_NOME=<nome real da instituição>
VITE_HOSPITAL_SIGLA=<sigla>
```

```powershell
npm install
npm run build
```

Isso gera `frontend\dist\` — arquivos estáticos prontos. **Se o IP ou a
porta mudar depois**, é preciso editar o `.env` e rodar `npm run build`
de novo — o Vite grava o valor dentro dos arquivos em tempo de build,
não é lido em runtime.

**Se `npm run build` falhar** com `spawn C:\Windows\system32\cmd.exe
ENOENT`: 🟢 ainda janela comum — o `cmd.exe` de 64-bit está faltando
(sintoma de Windows desatualizado, ver checklist item 0):

```powershell
$env:ComSpec = "C:\Windows\SysWOW64\cmd.exe"  # só se a versão 32-bit existir
npm run build
```

O certo é resolver a causa raiz (Windows Update) e não depender desse
contorno numa máquina de produção.

### Opção A — nginx para Windows

O repositório já traz `frontend/nginx.conf` (usado dentro do container
Docker) — pra esta instalação nativa, o conteúdo final do arquivo de
configuração do nginx (`C:\nginx\conf\almoxarifado.conf`, ou incluído no
`nginx.conf` principal) fica assim — só a porta e o caminho mudam em
relação ao arquivo do repositório:

```nginx
server {
    listen 8082;
    server_name _;
    root C:/caminho/ALMOXARIFADO/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

⚠️ **Atenção — nginx sozinho NÃO sobrevive a reboot.** Diferente do IIS
(que roda como o serviço `W3SVC`, já configurado para iniciar sozinho),
o `nginx.exe` para Windows é só um executável — se for iniciado
manualmente (`start nginx`), ele para de responder no próximo boot, do
mesmo jeito que o backend fazia antes do NSSM. Registrar como serviço,
com o mesmo NSSM já usado para o backend (🔴 **janela como
Administrador**):

```powershell
nssm install AlmoxarifadoFrontend "C:\nginx\nginx.exe"
nssm set AlmoxarifadoFrontend AppDirectory "C:\nginx"
nssm start AlmoxarifadoFrontend
```

### Opção B — IIS

Criar um novo site (não usar o site padrão da porta 80, ocupado por
outro app) com binding na porta `8082`, apontando para
`frontend\dist`. Criar `frontend\dist\web.config` com o rewrite de SPA
(equivalente ao `try_files` do nginx):

```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
  <system.webServer>
    <rewrite>
      <rules>
        <rule name="SPA fallback" stopProcessing="true">
          <match url=".*" />
          <conditions logicalGrouping="MatchAll">
            <add input="{REQUEST_FILENAME}" matchType="IsFile" negate="true" />
            <add input="{REQUEST_FILENAME}" matchType="IsDirectory" negate="true" />
          </conditions>
          <action type="Rewrite" url="/index.html" />
        </rule>
      </rules>
    </rewrite>
  </system.webServer>
</configuration>
```

Não precisa de NSSM — o IIS já cuida disso pelo `W3SVC`. Requer o módulo
**URL Rewrite** do IIS instalado (`iis.net/downloads/microsoft/url-rewrite`).

## 5. Rede e firewall

🔴 **Janela como Administrador** — regra de firewall exige elevação.

```powershell
New-NetFirewallRule -DisplayName "Almoxarifado Backend 8003" -Direction Inbound -LocalPort 8003 -Protocol TCP -Action Allow -RemoteAddress <sub-rede-interna, ex. 10.10.28.0/24>
New-NetFirewallRule -DisplayName "Almoxarifado Frontend 8082" -Direction Inbound -LocalPort 8082 -Protocol TCP -Action Allow -RemoteAddress <sub-rede-interna, ex. 10.10.28.0/24>
```

🟢 **Janela comum** para testar de uma estação cliente qualquer:
`http://SEU_IP_FIXO:8082` deve mostrar o formulário público, e
`http://SEU_IP_FIXO:8082/login` a tela de login.

## 6. Backup diário

🟢 **Janela comum** para tudo desta seção.

Script pronto: **`backend/scripts/backup_diario.ps1`** (novo neste
projeto — lê usuário/senha/host direto do `backend\.env`, não duplica o
segredo num segundo lugar). Antes de agendar, abrir o script e ajustar
as duas variáveis do topo pra realidade desta máquina:

```powershell
$pgDumpExe = "C:\Program Files\PostgreSQL\17\bin\pg_dump.exe"
$backupDir = "D:\Backups\Almoxarifado"   # disco/pasta SEPARADA do servidor principal
```

Testar rodando manualmente primeiro:

```powershell
powershell -ExecutionPolicy Bypass -File "C:\caminho\ALMOXARIFADO\backend\scripts\backup_diario.ps1"
```

Deve terminar com `Backup criado: D:\Backups\Almoxarifado\almoxarifado_AAAA-MM-DD.dump`.
Só depois de confirmar que funcionou, agendar:

```powershell
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument '-NoProfile -ExecutionPolicy Bypass -File "C:\caminho\ALMOXARIFADO\backend\scripts\backup_diario.ps1"'
$trigger = New-ScheduledTaskTrigger -Daily -At "19:30"
Register-ScheduledTask -TaskName "Almoxarifado_BackupDiario" -Action $action -Trigger $trigger -Description "Backup diario do banco Postgres do Almoxarifado" -Force
```

(Horário `19:30` de propósito — 30 minutos depois do backup da farmácia
às `19:00`, evitando os dois `pg_dump` disputando o mesmo Postgres ao
mesmo tempo.)

Testar a restauração pelo menos uma vez antes de confiar no backup —
"um backup nunca testado é uma suposição, não uma garantia":

```powershell
& "C:\Program Files\PostgreSQL\17\bin\pg_restore.exe" -U postgres -d almoxarifado_teste "D:\Backups\Almoxarifado\almoxarifado_AAAA-MM-DD.dump"
```

(criar antes um banco `almoxarifado_teste` vazio só pra esse teste, com
`CREATE DATABASE almoxarifado_teste OWNER almoxarifado;`.)

## 7. Garantir que tudo sobe sozinho depois de um reboot

🟢 **Janela comum** para as checagens.

```powershell
# PostgreSQL (já deve estar Automatic — instalado para a farmácia)
Get-Service -Name "postgresql*" | Select-Object Name, Status, StartType

# Backend do almoxarifado (NSSM)
Get-Service -Name "AlmoxarifadoAPI" | Select-Object Name, Status, StartType

# Frontend — só se estiver usando nginx via NSSM (opção A da seção 4).
# Se for IIS, checar o W3SVC no lugar.
Get-Service -Name "AlmoxarifadoFrontend" -ErrorAction SilentlyContinue | Select-Object Name, Status, StartType
Get-Service -Name "W3SVC" -ErrorAction SilentlyContinue | Select-Object Name, Status, StartType
```

Todos precisam mostrar `StartType: Automatic`. Se algum vier `Manual`
(🔴 **janela como Administrador**):

```powershell
nssm set AlmoxarifadoAPI Start SERVICE_AUTO_START
nssm set AlmoxarifadoFrontend Start SERVICE_AUTO_START   # se usar nginx
```

**O teste que realmente importa**: reiniciar o servidor de verdade (não
só parar/iniciar os serviços manualmente) e, sem logar em nenhuma conta,
esperar 1-2 minutos e confirmar de uma estação cliente que
`http://SEU_IP_FIXO:8082` carrega o formulário público normalmente. Só
isso prova que o boot automático funciona.

## 8. Validação final

🟢 **Janela comum** para tudo (login pelo navegador, checagem de
serviço).

- Formulário público (`/`) abrindo sem login e listando os setores/itens
  reais (ou os importados pela planilha, seção 3 do
  `docs/05_INSTALACAO_SERVIDOR_LOCAL.md`).
- Login de cada perfil (Coordenador, um Atendente e o Admin).
- Logado como Admin: tela **Permissões** abre e mostra Coordenador com
  tudo liberado e Atendente com tudo bloqueado (comportamento herdado,
  ver seção 3) — ajustar dali se a operação real quiser outra coisa.
- Um pedido pelo formulário público, uma conferência completa e uma
  parcial (confirma que o status calcula certo), uma Entrada por Compra,
  um Ajuste de estoque, um Empréstimo/Permuta.
- Relatório com prévia em tela + exportação PDF/Excel.
- Confirmar que os outros 3 apps (portas 8000/8001/8002, 80/8080/8081)
  continuam respondendo normalmente depois do reboot — nenhuma mudança
  feita aqui deveria afetá-los, mas vale conferir numa máquina com
  múltiplos apps.
- Trocar as senhas temporárias dos 5 usuários reais + a do Admin no
  primeiro login.
- Guardar senha do banco e `JWT_SECRET_KEY` em cofre de senhas da
  equipe de TI, nunca em texto plano em lugar nenhum.
