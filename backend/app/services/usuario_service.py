from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import hash_senha
from app.models.usuario import Usuario
from app.repositories.usuario_repository import UsuarioRepository
from app.schemas.usuario import UsuarioCreate, UsuarioMe, UsuarioUpdate


class UsuarioService:
    """Gestão de usuários — exclusiva do Coordenador (router garante o
    perfil)."""

    def __init__(self):
        self.usuario_repository = UsuarioRepository()

    def listar(self, db: Session, incluir_inativos: bool) -> list[Usuario]:
        return self.usuario_repository.list(db, incluir_inativos)

    def criar(self, db: Session, dados: UsuarioCreate) -> Usuario:
        if self.usuario_repository.get_by_login(db, dados.login):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Já existe um usuário com login '{dados.login}'.",
            )

        usuario = Usuario(
            nome=dados.nome,
            login=dados.login,
            senha_hash=hash_senha(dados.senha),
            perfil=dados.perfil,
            ativo=True,
            # Senha informada pelo Coordenador é temporária — o próprio
            # usuário é obrigado a trocá-la no primeiro login
            # (POST /auth/trocar-senha).
            deve_trocar_senha=True,
        )

        return self.usuario_repository.create(db, usuario)

    def atualizar(
        self, db: Session, usuario_logado: UsuarioMe, usuario_id: int, dados: UsuarioUpdate
    ) -> Usuario:
        usuario = self.usuario_repository.get_by_id(db, usuario_id)
        if usuario is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado."
            )

        # Trava de segurança: ninguém edita o próprio acesso por aqui —
        # evita o Coordenador se desativar ou se rebaixar de perfil sem
        # querer e ficar trancado pra fora da própria gestão de usuários
        # (equipe de 5 pessoas, pode não ter um segundo coordenador pra
        # desfazer). Nome do próprio usuário continua editável.
        if usuario_logado.id == usuario_id:
            if dados.ativo is False:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Você não pode desativar a própria conta.",
                )
            if dados.perfil is not None and dados.perfil != usuario.perfil:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Você não pode alterar o próprio perfil de acesso.",
                )

        if dados.senha:
            usuario.senha_hash = hash_senha(dados.senha)
            # Reset manual pelo Coordenador (ex.: usuário esqueceu a
            # senha) exige troca no próximo login, mesma regra do usuário
            # recém-criado.
            usuario.deve_trocar_senha = True

        return self.usuario_repository.update(db, usuario, dados)
