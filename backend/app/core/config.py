from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg2://localhost/box_office_forecaster"
    tmdb_api_key: str = ""
    omdb_api_key: str = ""
    anthropic_api_key: str = ""
    allowed_origins: list[str] = ["http://localhost:3000"]
    model_artifact_dir: str = "app/ml/artifacts"
    env: str = "development"

    @field_validator("database_url")
    @classmethod
    def _use_psycopg2_driver(cls, value: str) -> str:
        # Railway/Heroku-style providers hand out "postgres://" or driverless
        # "postgresql://" URLs; SQLAlchemy needs the explicit psycopg2 driver.
        if value.startswith("postgres://"):
            return value.replace("postgres://", "postgresql+psycopg2://", 1)
        if value.startswith("postgresql://"):
            return value.replace("postgresql://", "postgresql+psycopg2://", 1)
        return value


settings = Settings()
