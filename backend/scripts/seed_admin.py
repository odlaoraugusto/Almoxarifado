"""Cria o usuário Admin global do Almoxarifado — o único perfil que
gerencia a matriz de permissões de Coordenador/Atendente (tela
/permissoes). Diferente dos 5 logins operacionais
(scripts/seed_usuarios.py), o Admin não participa do dia a dia
(conferência, estoque, etc.) — é uma conta separada, de uso raro,
normalmente com quem administra o servidor.

Uso (a partir da pasta backend/, com o venv ativado e o .env configurado):

    python scripts/seed_admin.py
    python scripts/seed_admin.py --login admin --nome "Nome de quem administra"

Idempotente: se o login já existir, não mexe em nada (nem senha, nem
perfil) — só avisa. Resete a senha depois pela tela Usuários
(PUT /usuarios/{id}), já logado como Admin.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.security import hash_senha  # noqa: E402
from app.database.database import SessionLocal  # noqa: E402
from app.models.enums import PerfilEnum  # noqa: E402
from app.models.usuario import Usuario  # noqa: E402

# Senha temporária — óbvio que é temporária: `deve_trocar_senha=True`
# obriga a troca antes de liberar o resto do painel
# (POST /auth/trocar-senha).
SENHA_TEMPORARIA = "Admin@2026"


def main() -> None:
    parser = argparse.ArgumentParser(description="Cria o usuário Admin global do Almoxarifado.")
    parser.add_argument("--login", default="admin")
    parser.add_argument("--nome", default="Administrador do Sistema")
    args = parser.parse_args()

    db = SessionLocal()
    try:
        existente = db.query(Usuario).filter(Usuario.login == args.login).first()
        if existente:
            if existente.perfil != PerfilEnum.admin:
                print(
                    f"Usuário '{args.login}' já existe com perfil '{existente.perfil.value}' — "
                    "nada alterado (o script não promove usuário existente automaticamente)."
                )
            else:
                print(f"Usuário Admin '{args.login}' já existe — nada a fazer.")
            return

        usuario = Usuario(
            nome=args.nome,
            login=args.login,
            senha_hash=hash_senha(SENHA_TEMPORARIA),
            perfil=PerfilEnum.admin,
            ativo=True,
            deve_trocar_senha=True,
        )
        db.add(usuario)
        db.commit()
        print(f"Usuário Admin '{args.login}' criado. id={usuario.id}")
        print(f"Senha temporária: {SENHA_TEMPORARIA} — troca obrigatória no primeiro login.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
