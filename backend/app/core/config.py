from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    app_name: str = 'WiseChecks MVP'
    database_url: str = 'postgresql+psycopg2://wise:wise@localhost:5432/wisechecks'
    jwt_secret: str = 'dev-secret'
    jwt_algorithm: str = 'HS256'
    access_token_minutes: int = 480
    minio_endpoint: str = 'localhost:9000'
    minio_access_key: str = 'minioadmin'
    minio_secret_key: str = 'minioadmin'
    minio_bucket: str = 'docs'
    minio_secure: bool = False


settings = Settings()
