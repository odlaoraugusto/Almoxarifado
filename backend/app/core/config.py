from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações da instalação, lidas de variáveis de ambiente/.env.

    Sistema de instalação única (sem multi-tenant): uma organização, um
    almoxarifado, um banco. Os valores abaixo são só placeholder genérico
    — cada instalação real define os seus em `.env`.
    """

    DATABASE_URL: str

    # Autenticação / sessão (JWT assinado pelo servidor).
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8h, cobre um turno de trabalho

    # Identificação institucional (cabeçalho dos relatórios) — mesmo
    # padrão do projeto irmão (farmácia): HOSPITAL_NOME/HOSPITAL_ORGANIZACAO
    # lidos do .env de cada instalação, nunca hardcoded aqui.
    HOSPITAL_NOME: str = "Hospital Exemplo"
    HOSPITAL_ORGANIZACAO: str = "Rede de Saúde Exemplo"

    # Origens liberadas para CORS, separadas por vírgula, ou "*" para
    # liberar geral. Em dev, o frontend (Vite) roda em localhost:5173.
    CORS_ORIGINS: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
