"""Cria os setores iniciais desta instalação, a partir dos mesmos nomes já
usados no protótipo em planilha (`../docs/prototipo_formulario_publico.html`,
`SETORES_DEMO`) — não são dados de exemplo, é a lista real de setores que
já pediam material pelo formulário antigo.

Uso (a partir da pasta backend/, com o venv ativado e o .env configurado):

    python scripts/seed_setores.py

Idempotente: setores cujo `nome` já existir são pulados. O Coordenador
pode cadastrar/editar mais setores depois pela tela `/setores`
(`POST /setores`) — este script só bootstrapa a instalação para o
formulário público não nascer com o <select> vazio.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database.database import SessionLocal  # noqa: E402
from app.models.setor import Setor  # noqa: E402

SETORES_INICIAIS = [
    "UTI Neonatal",
    "Maternidade - Ala A",
    "Centro Cirúrgico",
    "Emergência Obstétrica",
    "Farmácia Satélite",
    "Enfermaria Pediátrica",
]


def main() -> None:
    db = SessionLocal()
    try:
        for nome in SETORES_INICIAIS:
            if db.query(Setor).filter(Setor.nome == nome).first():
                print(f"Setor '{nome}' já existe — pulando.")
                continue

            setor = Setor(nome=nome, ativo=True)
            db.add(setor)
            db.commit()
            print(f"Setor '{nome}' criado. id={setor.id}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
