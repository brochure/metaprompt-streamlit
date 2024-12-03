# app/config.py
import os


class Settings:
    PROJECT_TITLE = "Metaprompt-Streamlit"
    API_PREFIX = "/api/v1"
    PROJECT_DESCRIPTION: str = "A web interface for prompt optimization and chat"
    VERSION: str = "0.1.0"
    DEBUG: bool = bool(os.getenv("DEBUG", ""))

    # CORS配置
    ALLOWED_ORIGINS: list[str] = ["*"]
    ALLOWED_METHODS: list[str] = ["*"]
    ALLOWED_HEADERS: list[str] = ["*"]


settings = Settings()
