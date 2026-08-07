from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": "config.env", "env_file_encoding": "utf-8"}

    # LLM - Agnes API
    llm_api_key: str = ""
    llm_base_url: str = "https://apihub.agnes-ai.com/v1"
    llm_model_fast: str = "agnes-2.5-flash"
    llm_model_balanced: str = "agnes-2.5-flash"
    llm_model_judge: str = "agnes-2.5-flash"
    llm_max_tokens: int = 8192
    llm_temperature: float = 0

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/resume_interview"
    database_url_sync: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/resume_interview"

    # App
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_env: str = "development"
    app_debug: bool = True
    log_level: str = "DEBUG"

    # CORS — comma-separated in env, parsed to list
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000", "http://localhost:5173"]

    # File upload
    max_upload_size_mb: int = 5
    max_pdf_pages: int = 10

    # Authentication (M2.6)
    jwt_secret_key: str = "dev-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_days: int = 30


settings = Settings()
