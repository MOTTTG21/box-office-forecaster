from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg2://localhost/box_office_forecaster"
    tmdb_api_key: str = ""
    allowed_origins: list[str] = ["http://localhost:3000"]
    model_artifact_dir: str = "app/ml/artifacts"
    env: str = "development"


settings = Settings()
