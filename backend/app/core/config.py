from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_env: str = "development"
    log_level: str = "INFO"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:3000"
    database_url: str = "postgresql+asyncpg://foodinsight:foodinsight@postgres:5432/foodinsight"
    qdrant_url: str = "http://qdrant:6333"
    qdrant_collection: str = "foodinsight_chunks"
    neo4j_uri: str = "bolt://neo4j:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "foodinsight"
    llm_provider: str = "mock"
    llm_model: str = ""
    vision_provider: str = "mock"
    vision_model: str = ""
    embedding_provider: str = "local"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    llm_api_key: str | None = None
    max_upload_mb: int = 20
    top_k: int = 8
    rerank_top_k: int = 5

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
