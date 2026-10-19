from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./certgen.db"
    PROCESSING_MODE: str = "background"
    MAX_RECIPIENTS: int = 1000
    BATCH_SIZE: int = 25
    LEASE_SECONDS: int = 300
    TIME_BUDGET_SECONDS: int = 240
    API_KEY: str = ""
    DEFAULT_ISSUER_NAME: str = "Certificate Authority"
    SERVERLESS: bool = False

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
