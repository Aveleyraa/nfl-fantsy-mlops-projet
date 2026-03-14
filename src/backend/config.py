from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Cache nflreadpy
    cache_dir: str = "./.nfl_cache"
    cache_duration: int = 86400  # 24h en segundos

    # Entorno
    environment: str = "local"

    # ML models
    models_dir: str = "./ml_models"

    # AWS (dejar vacío en local)
    aws_region: str = "us-east-1"
    s3_bucket_cache: str = ""

    class Config:
        env_file = ".env"

    @property
    def cache_path(self) -> Path:
        path = Path(self.cache_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def models_path(self) -> Path:
        path = Path(self.models_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path


settings = Settings()