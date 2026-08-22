from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.database import Base
from app.models.enums import DirecaoEmprestimoEnum


class RegistroEmprestimo(Base):
    """Empréstimo/permuta de material com uma unidade EXTERNA — outra
    instituição, fora do catálogo de `setores` (que são departamentos
    internos, sempre do próprio hospital, que pedem material pelo
    formulário público de `Pedido`). Duas direções:

    - `saida`: a gente empresta pra fora — consome estoque nosso via FEFO
      (mesma função `consumir_fefo` usada por `PedidoService`), gerando
      uma ou mais linhas em `Movimentacao` (`emprestimo_id` preenchido).
    - `entrada`: a gente recebe de volta em devolução ou recebe em
      permuta — cria lote(s) novo(s) (`Lote.origem='emprestimo'`,
      `Lote.emprestimo_id` preenchido), igual à Entrada por compra/doação.

    `unidade_origem` é texto livre (nome da instituição/unidade externa),
    não FK — não faz parte do catálogo interno de `setores`."""

    __tablename__ = "emprestimos"

    id = Column(Integer, primary_key=True)

    direcao = Column(
        Enum(
            DirecaoEmprestimoEnum,
            name="direcao_emprestimo_enum",
            native_enum=False,
            length=10,
        ),
        nullable=False,
    )
    unidade_origem = Column(String(150), nullable=False)
    numero_oficio = Column(String(50), nullable=True)

    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    data_hora = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # lazy="selectin": mesmo cuidado documentado em app/models/lote.py —
    # evita LEFT OUTER JOIN implícito que o Postgres recusa junto de
    # SELECT ... FOR UPDATE em outras consultas do mesmo grafo de models.
    usuario = relationship("Usuario", lazy="selectin")

    # Relacionamentos inversos usados por EmprestimoService para montar o
    # "detalhe" (lotes criados numa entrada, ou movimentações de saída
    # geradas) sem o frontend precisar cruzar IDs manualmente.
    # back_populates explícito (em vez de relationship solta como no
    # resto do arquivo) porque os dois lados mapeiam a mesma FK
    # (`lotes.emprestimo_id`/`movimentacoes.emprestimo_id`) — sem isso o
    # SQLAlchemy emite SAWarning de relacionamento sobreposto.
    lotes_criados = relationship("Lote", back_populates="emprestimo", lazy="selectin")
    movimentacoes = relationship("Movimentacao", back_populates="emprestimo", lazy="selectin")
