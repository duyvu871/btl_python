from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_URL: str = "http://localhost:8000"
    API_PREFIX: str = "/api/v1"
    CORS_ORIGINS: list[str] = ["*"]

    # Database settings
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_SERVER: str
    POSTGRES_DB: str

    # Redis settings
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # Open AI settings
    OPENAI_API_KEY: str
    GOOGLE_API_KEY: str
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    EMBEDDING_MODEL_DIM: int = 1536
    EMBEDDING_API_KEY: str | None = None
    EMBEDDING_BASE_URL: str = "http://localhost:8000"
    COMPLETION_MODEL: str = "gpt-3.5-turbo"
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # Qdrant settings
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_RECIPE_COLLECTION: str = "recipes"
    QDRANT_PERSONAL_COLLECTION: str = "personal_recommendation"

    # JWT settings
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Email settings (if using)
    SMTP_TLS: bool = True
    SMTP_PORT: int | None = None
    SMTP_HOST: str | None = None
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM: str | None = None
    EMAILS_FROM_EMAIL: str | None = None
    EMAILS_FROM_NAME: str | None = None
    EMAIL_TEMPLATES_DIR: str = "templates"  # Relative to backend root

    # ARQ Worker settings
    ARQ_QUEUE_NAME: str = "arq:queue"
    ARQ_MAX_JOBS: int = 10
    ARQ_JOB_TIMEOUT: int = 600  # 10 minutes

    # Sentry settings
    SENTRY_DSN: str | None = None

    # Loki settings
    LOKI_URL: str = "http://localhost:3100"
    ENABLE_LOKI_LOGGING: bool = False

    # Other settings
    FIRST_SUPERUSER: str
    FIRST_SUPERUSER_PASSWORD: str

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"

    def validate_smtp_config(self) -> bool:
        """Check if SMTP is properly configured"""
        return all([self.SMTP_HOST, self.SMTP_PORT, self.SMTP_USER, self.SMTP_PASSWORD, self.EMAILS_FROM_EMAIL])

    def validate_loki_config(self) -> bool:
        """Check if Loki is properly configured"""
        return self.ENABLE_LOKI_LOGGING and bool(self.LOKI_URL)


# Create an instance of Settings to use throughout the application
env = Settings()
