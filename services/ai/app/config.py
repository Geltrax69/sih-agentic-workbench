"""AI service configuration. Secrets and endpoints come from the environment."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = "development"
    log_level: str = "info"

    # Internal shared secret with the Go control plane
    internal_api_secret: str = ""

    # Local model endpoint (OpenAI-compatible)
    ai_provider: str = "openai_compatible"
    ai_base_url: str = "http://localhost:11434/v1"
    ai_model: str = "llama3.2"
    ai_embedding_model: str = "nomic-embed-text"
    ai_allow_cloud: bool = False
    # Reasoning models (e.g. MiniCPM5 on LM Studio) burn max_tokens on thinking; "none" disables it
    ai_reasoning_effort: str = ""
    # Model that double-checks answers against the sources; empty = same as ai_model
    ai_verifier_model: str = ""
    # Multi-model pipeline: comma-separated model ids to fan out to; empty = single model
    ai_multi_models: str = ""

    # PostgreSQL (AI-side tables: chunks, embeddings, graph, memory)
    database_url: str = ""

    # MinIO (document objects)
    s3_endpoint: str = "http://localhost:9000"
    s3_bucket: str = "workbench-documents"
    s3_access_key: str = ""
    s3_secret_key: str = ""

    @property
    def is_local_endpoint(self) -> bool:
        """Sovereign mode: only loopback/private hosts qualify as local."""
        host = self.ai_base_url.split("//")[-1].split("/")[0].split(":")[0]
        return (
            host in {"localhost", "127.0.0.1", "0.0.0.0", "host.docker.internal"}
            or host.startswith("10.")
            or host.startswith("192.168.")
            or host.startswith("172.16.")
            or host.endswith(".local")
        )

    def validate_sovereign_mode(self) -> list[str]:
        """Return policy violations; empty list means compliant."""
        problems: list[str] = []
        if not self.ai_allow_cloud and not self.is_local_endpoint:
            problems.append(
                f"AI_ALLOW_CLOUD=false but AI_BASE_URL ({self.ai_base_url}) is not a local endpoint"
            )
        return problems


settings = Settings()
