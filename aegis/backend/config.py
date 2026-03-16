from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str = ""
    anthropic_api_key: str = ""
    gemini_api_key: str = ""
    target_llm_base_url: str = "https://api.openai.com/v1"
    default_model: str = "gpt-4o-mini"
    port: int = 8000
    frontend_url: str = "http://localhost:3000"


settings = Settings()
