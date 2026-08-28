"""Importa o catálogo de itens (e, opcionalmente, o estoque inicial de
cada um) e/ou a lista de setores a partir de planilhas .xlsx ou .csv —
sempre via API (nunca acesso direto ao banco), então respeita as mesmas
regras de validação que o cadastro manual pela tela.

Uso — só itens:
    python scripts/importar_itens_planilha.py itens.xlsx \
        --api-url http://localhost:8000 --login coordenador --senha "..."

Uso — itens e setores juntos (planilhas separadas, cada uma com sua
própria aba/formato):
    python scripts/importar_itens_planilha.py itens.xlsx --setores setores.xlsx \
        --api-url http://localhost:8000 --login coordenador --senha "..."

Uso — só setores (sem planilha de itens):
    python scripts/importar_itens_planilha.py --setores setores.xlsx \
        --api-url http://localhost:8000 --login coordenador --senha "..."

Idempotente nos dois casos: itens cujo `codigo` já existir no catálogo,
e setores cujo `nome` já existir, são pulados (não atualiza nada, só
avisa) — seguro rodar de novo se a importação for interrompida no meio
ou se quiser importar um lote novo depois.

## Planilha de setores (`--setores`)

Só uma coluna, obrigatória: `nome` (texto, único — mesmo nome que já
existir é pulado). Qualquer outra coluna é ignorada. Exemplo mínimo:

| nome |
|---|
| UTI Neonatal |
| Centro Cirúrgico |

## Colunas da planilha de itens

A primeira linha tem que ter os nomes das colunas (não importa a ordem,
maiúsculo/minúsculo e acento não fazem diferença).

**Obrigatórias** (uma linha sem alguma dessas é pulada, com aviso):

| Coluna | Formato | Exemplo |
|---|---|---|
| `codigo` | texto, único no catálogo | `MAT001` |
| `nome` | texto | `Luvas de Procedimento (M)` |
| `apresentacao` | texto | `Caixa c/ 100` |
| `categoria` | uma das 5 categorias fixas — aceita a chave OU o rótulo, sem diferenciar maiúsculo/acento (ver tabela abaixo) | `Material Médico` ou `material_medico` |

Valores aceitos pra `categoria` (qualquer um dos dois lados de cada linha):

| Categoria | Rótulo aceito | Chave aceita |
|---|---|---|
| Material Médico | `Material Médico`, `Material Medico`, `Mat. Med.` | `material_medico` |
| EPI | `EPI`, `EPI/SIAST` | `epi` |
| Higienização | `Higienização`, `Higienizacao` | `higienizacao` |
| Material de Expediente | `Material de Expediente`, `Expediente` | `expediente` |
| Enxoval | `Enxoval` | `enxoval` |

**Opcionais** — se `quantidade` vier preenchida, o script também registra
uma ENTRADA de estoque pra aquele item (cria um lote), com os outros
campos opcionais como atributos desse lote. Se `quantidade` vier vazia,
o item é cadastrado sem estoque inicial (fica em 0, dá pra dar entrada
depois pela tela "Entrada por Compra"):

| Coluna | Formato | Observação |
|---|---|---|
| `estoque_minimo` | número inteiro | opcional — 0 se vazio ou não numérico |
| `quantidade` | número inteiro | dispara a criação do lote se preenchido |
| `numero_lote` | texto | opcional mesmo com quantidade preenchida |
| `data_validade` | `AAAA-MM-DD`, ou data nativa do Excel | opcional — nem todo item vence |
| `valor_unitario` | número (use ponto, não vírgula, decimal) | opcional |
| `numero_nota_fiscal` | texto | opcional |
| `fabricante` | texto | opcional — vira o campo "Fabricante" do cadastro do item, não do lote |

Qualquer outra coluna na planilha é ignorada (pode manter colunas de
controle interno da sua planilha antiga sem precisar apagar).
"""

import argparse
import csv
import sys
import unicodedata
from pathlib import Path

import requests

CATEGORIA_ACEITAS = {
    "material_medico": "material_medico",
    "material medico": "material_medico",
    "mat. med.": "material_medico",
    "mat med": "material_medico",
    "epi": "epi",
    "epi/siast": "epi",
    "higienizacao": "higienizacao",
    "higiene": "higienizacao",
    "material de expediente": "expediente",
    "expediente": "expediente",
    "enxoval": "enxoval",
}

COLUNAS_OBRIGATORIAS = ["codigo", "nome", "apresentacao", "categoria"]


def normalizar(texto: str) -> str:
    """minúsculo, sem acento, espaços simples — pra comparar cabeçalho de
    coluna e valor de categoria sem depender de digitação exata."""
    texto = str(texto).strip().lower()
    texto = "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")
    return texto


def ler_planilha(caminho: Path) -> list[dict]:
    if caminho.suffix.lower() == ".csv":
        with open(caminho, encoding="utf-8-sig", newline="") as f:
            leitor = csv.reader(f)
            linhas = list(leitor)
    else:
        import openpyxl

        wb = openpyxl.load_workbook(caminho, data_only=True)
        ws = wb.active
        linhas = [[c.value for c in row] for row in ws.iter_rows()]

    if not linhas:
        return []

    cabecalho = [normalizar(c) if c is not None else "" for c in linhas[0]]
    registros = []
    for linha in linhas[1:]:
        if all(v is None or str(v).strip() == "" for v in linha):
            continue  # linha em branco
        registro = {}
        for i, valor in enumerate(linha):
            if i < len(cabecalho) and cabecalho[i]:
                registro[cabecalho[i]] = valor
        registros.append(registro)
    return registros


def validar_e_montar_item(registro: dict, numero_linha: int) -> tuple[dict | None, dict | None, list[str]]:
    """Retorna (payload_item, payload_entrada_ou_None, erros)."""
    erros = []

    faltando = [c for c in COLUNAS_OBRIGATORIAS if not str(registro.get(c, "")).strip()]
    if faltando:
        erros.append(f"linha {numero_linha}: faltando coluna(s) obrigatória(s): {', '.join(faltando)}")
        return None, None, erros

    categoria_bruta = normalizar(registro["categoria"])
    categoria = CATEGORIA_ACEITAS.get(categoria_bruta)
    if categoria is None:
        erros.append(
            f"linha {numero_linha}: categoria '{registro['categoria']}' não reconhecida "
            "(ver tabela de categorias aceitas no topo deste script)"
        )
        return None, None, erros

    estoque_minimo_bruto = registro.get("estoque_minimo")
    if estoque_minimo_bruto in (None, ""):
        estoque_minimo = 0
    else:
        try:
            estoque_minimo = int(float(estoque_minimo_bruto))
        except (TypeError, ValueError):
            erros.append(f"linha {numero_linha}: estoque_minimo '{estoque_minimo_bruto}' não é um número — usando 0")
            estoque_minimo = 0

    item_payload = {
        "codigo": str(registro["codigo"]).strip(),
        "nome": str(registro["nome"]).strip(),
        "apresentacao": str(registro["apresentacao"]).strip(),
        "categoria": categoria,
        "estoque_minimo": estoque_minimo,
    }
    fabricante = registro.get("fabricante")
    if fabricante not in (None, ""):
        item_payload["fabricante"] = str(fabricante).strip()

    entrada_payload = None
    quantidade_bruta = registro.get("quantidade")
    if quantidade_bruta not in (None, ""):
        try:
            quantidade = int(float(quantidade_bruta))
        except (TypeError, ValueError):
            erros.append(f"linha {numero_linha}: quantidade '{quantidade_bruta}' não é um número — item será criado sem estoque inicial")
            quantidade = None
        if quantidade and quantidade > 0:
            entrada_payload = {"quantidade": quantidade, "origem": "compra"}
            numero_lote = registro.get("numero_lote")
            if numero_lote not in (None, ""):
                entrada_payload["numero_lote"] = str(numero_lote).strip()
            valor_unitario = registro.get("valor_unitario")
            if valor_unitario not in (None, ""):
                entrada_payload["valor_unitario"] = str(valor_unitario).strip()
            numero_nf = registro.get("numero_nota_fiscal")
            if numero_nf not in (None, ""):
                entrada_payload["numero_nota_fiscal"] = str(numero_nf).strip()
            data_validade = registro.get("data_validade")
            if data_validade not in (None, ""):
                if hasattr(data_validade, "date"):
                    entrada_payload["data_validade"] = data_validade.date().isoformat()
                elif hasattr(data_validade, "isoformat"):
                    entrada_payload["data_validade"] = data_validade.isoformat()
                else:
                    entrada_payload["data_validade"] = str(data_validade).strip()

    return item_payload, entrada_payload, erros


def importar_itens(sessao: "requests.Session", api_url: str, caminho: Path) -> None:
    print(f"Lendo {caminho}...")
    registros = ler_planilha(caminho)
    print(f"{len(registros)} linha(s) de dados encontrada(s).\n")

    catalogo_atual = sessao.get(f"{api_url}/itens", params={"incluir_inativos": True})
    codigos_existentes = {i["codigo"] for i in catalogo_atual.json()}

    criados, pulados, com_estoque, com_erro = 0, 0, 0, 0
    for numero_linha, registro in enumerate(registros, start=2):  # linha 1 é cabeçalho
        item_payload, entrada_payload, erros = validar_e_montar_item(registro, numero_linha)

        if item_payload is None:
            for e in erros:
                print(f"  ERRO: {e}")
            com_erro += 1
            continue

        if item_payload["codigo"] in codigos_existentes:
            print(f"  linha {numero_linha}: item '{item_payload['codigo']}' já existe no catálogo — pulando")
            pulados += 1
            continue

        r = sessao.post(f"{api_url}/itens", json=item_payload)
        if r.status_code != 201:
            print(f"  ERRO linha {numero_linha} ({item_payload['codigo']}): falha ao criar item — {r.status_code} {r.text[:200]}")
            com_erro += 1
            continue

        item_id = r.json()["id"]
        criados += 1
        codigos_existentes.add(item_payload["codigo"])
        print(f"  {item_payload['codigo']} — {item_payload['nome']}: criado (id={item_id})")

        for e in erros:  # avisos não-fatais (ex.: quantidade inválida, item criado sem estoque)
            print(f"    aviso: {e}")

        if entrada_payload:
            r = sessao.post(f"{api_url}/itens/{item_id}/entrada", json=entrada_payload)
            if r.status_code == 201:
                com_estoque += 1
                print(f"    + entrada de {entrada_payload['quantidade']} unidades registrada")
            else:
                print(f"    ERRO ao registrar entrada inicial: {r.status_code} {r.text[:200]}")

    print("\n== resumo (itens) ==")
    print(f"  itens criados: {criados} ({com_estoque} já com estoque inicial)")
    print(f"  itens pulados (já existiam): {pulados}")
    print(f"  linhas com erro: {com_erro}")


def importar_setores(sessao: "requests.Session", api_url: str, caminho: Path) -> None:
    print(f"\nLendo {caminho}...")
    registros = ler_planilha(caminho)
    print(f"{len(registros)} linha(s) de dados encontrada(s).\n")

    setores_atuais = sessao.get(f"{api_url}/setores", params={"incluir_inativos": True})
    nomes_existentes = {s["nome"] for s in setores_atuais.json()}

    criados, pulados, com_erro = 0, 0, 0
    for numero_linha, registro in enumerate(registros, start=2):  # linha 1 é cabeçalho
        nome = str(registro.get("nome", "")).strip()
        if not nome:
            print(f"  ERRO: linha {numero_linha}: faltando coluna obrigatória 'nome'")
            com_erro += 1
            continue

        if nome in nomes_existentes:
            print(f"  linha {numero_linha}: setor '{nome}' já existe — pulando")
            pulados += 1
            continue

        r = sessao.post(f"{api_url}/setores", json={"nome": nome})
        if r.status_code != 201:
            print(f"  ERRO linha {numero_linha} ({nome}): falha ao criar setor — {r.status_code} {r.text[:200]}")
            com_erro += 1
            continue

        criados += 1
        nomes_existentes.add(nome)
        print(f"  {nome}: criado (id={r.json()['id']})")

    print("\n== resumo (setores) ==")
    print(f"  setores criados: {criados}")
    print(f"  setores pulados (já existiam): {pulados}")
    print(f"  linhas com erro: {com_erro}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("planilha", type=Path, nargs="?", default=None, help="Caminho da planilha de itens (.xlsx ou .csv) — omitir se só for importar --setores")
    parser.add_argument("--setores", type=Path, default=None, help="Caminho da planilha de setores (.xlsx ou .csv), separada da de itens")
    parser.add_argument("--api-url", default="http://localhost:8000")
    parser.add_argument("--login", required=True, help="Login de um usuário Coordenador (só ele cadastra item/setor)")
    parser.add_argument("--senha", required=True)
    parser.add_argument(
        "--no-verify-ssl",
        action="store_true",
        help="Desliga a verificação de certificado HTTPS — só use se souber por quê "
        "(ex.: antivírus/proxy corporativo interceptando HTTPS localmente). "
        "Nunca use isso importando por internet pra um servidor que não seja o seu.",
    )
    args = parser.parse_args()

    if args.planilha is None and args.setores is None:
        sys.exit("Nada a importar — informe a planilha de itens, --setores, ou os dois.")
    if args.planilha is not None and not args.planilha.exists():
        sys.exit(f"Arquivo não encontrado: {args.planilha}")
    if args.setores is not None and not args.setores.exists():
        sys.exit(f"Arquivo não encontrado: {args.setores}")

    sessao = requests.Session()
    if args.no_verify_ssl:
        import urllib3

        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        sessao.verify = False
        print("AVISO: verificação de certificado HTTPS desligada (--no-verify-ssl).\n")
    resp = sessao.post(f"{args.api_url}/auth/login", json={"login": args.login, "senha": args.senha})
    if resp.status_code != 200:
        sys.exit(f"Login falhou ({resp.status_code}): {resp.text}")
    token = resp.json()["access_token"]
    sessao.headers["Authorization"] = f"Bearer {token}"

    if args.planilha is not None:
        importar_itens(sessao, args.api_url, args.planilha)
    if args.setores is not None:
        importar_setores(sessao, args.api_url, args.setores)


if __name__ == "__main__":
    main()
