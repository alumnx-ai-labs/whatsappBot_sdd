from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./data/app.db"
    port: int = 8000
    environment: str = "development"

    admin_session_secret: str = "dev-only-insecure-secret-change-me"
    admin_session_cookie_name: str = "admin_session"
    admin_session_ttl_minutes: int = 60

    proposal_expiry_minutes: int = 30
    default_phone_country: str = "IN"
    business_timezone: str = "UTC"
    supported_locations: str = ""

    google_api_key: str = ""
    llm_provider_api_key: str = ""
    llm_model: str = "gpt-4o-mini"

    hello_oscar_base_url: str = ""
    hello_oscar_api_key: str = ""
    hello_oscar_timeout_ms: int = 8000

    csv_max_file_bytes: int = 5 * 1024 * 1024
    csv_max_rows: int = 5000

    @model_validator(mode="after")
    def validate_session_secret(self) -> "Settings":
        if (
            self.environment != "development"
            and self.admin_session_secret == "dev-only-insecure-secret-change-me"
        ):
            raise ValueError("ADMIN_SESSION_SECRET must be configured outside development")
        return self


settings = Settings()
