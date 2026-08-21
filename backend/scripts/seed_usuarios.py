"""Cria os 5 usuários iniciais do Almoxarifado (1 coordenador + 4
atendentes), todos com senha temporária e `deve_trocar_senha=True`.

Uso (a partir da pasta backend/, com o venv ativado e o .env configurado):

    python scripts/seed_usuarios.py

Idempotente: usuários cujo `login` já existir são pulados (não
sobrescreve senha de quem já trocou a própria senha).

IMPORTANTE: troque a senha temporária logo no primeiro login de cada
usuário (POST /auth/trocar-senha) — o backend usa esse mesmo flag
(`deve_trocar_senha`) para sinalizar ao frontend que a troca é
obrigatória.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.security import hash_senha  # noqa: E402
from app.database.database import SessionLocal  # noqa: E402
from app.models.enums import PerfilEnum  # noqa: E402
from app.models.usuario import Usuario  # noqa: E402

# Senha temporária padrão de todos os usuários de seed — óbvio que é
# temporária: `deve_trocar_senha=True` obriga a troca antes de liberar o
# resto do painel (POST /auth/trocar-senha).
SENHA_TEMPORARIA = "Almox@2026"

USUARIOS_INICIAIS = [
    {"nome": "Nome do Coordenador", "login": "coordenador", "perfil": PerfilEnum.coordenador},
    {"nome": "Nome do Atendente 1", "login": "atendente1", "perfil": PerfilEnum.atendente},
    {"nome": "Nome do Atendente 2", "login": "atendente2", "perfil": PerfilEnum.atendente},
    {"nome": "Nome do Atendente 3", "login": "atendente3", "perfil": PerfilEnum.atendente},
    {"nome": "Nome do Atendente 4", "login": "atendente4", "perfil": PerfilEnum.atendente},
]


def main() -> None:
    db = SessionLocal()
    try:
        for dados in USUARIOS_INICIAIS:
            if db.query(Usuario).filter(Usuario.login == dados["login"]).first():
                print(f"Usuário '{dados['login']}' já existe — pulando.")
                continue

            usuario = Usuario(
                nome=dados["nome"],
                login=dados["login"],
                senha_hash=hash_senha(SENHA_TEMPORARIA),
                perfil=dados["perfil"],
                ativo=True,
                deve_trocar_senha=True,
            )
            db.add(usuario)
            db.commit()
            print(f"Usuário '{dados['login']}' ({dados['perfil'].value}) criado. id={usuario.id}")

        print(f"\nSenha temporária de todos os usuários criados agora: {SENHA_TEMPORARIA}")
        print("Cada um deve trocá-la no primeiro login (POST /auth/trocar-senha).")
    finally:
        db.close()


if __name__ == "__main__":
    main()
