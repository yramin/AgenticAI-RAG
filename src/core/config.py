"""Configuration management using pydantic-settings."""

import os
from typing import Optional, Dict, Any
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # OpenAI/OpenRouter Configuration
    openai_api_key: str = Field(default="", description="OpenAI or OpenRouter API key")
    openai_base_url: Optional[str] = Field(
        default=None, description="OpenAI/OpenRouter base URL (e.g., https://openrouter.ai/api/v1)"
    )
    openai_model: str = Field(
        default="gpt-4-turbo-preview", description="Model to use (OpenAI or OpenRouter model name)"
    )
    openai_embedding_model: str = Field(
        default="text-embedding-3-small", description="Embedding model to use"
    )
    # OpenRouter specific headers (optional)
    openrouter_http_referer: Optional[str] = Field(
        default=None, description="HTTP-Referer header for OpenRouter (optional)"
    )
    openrouter_title: Optional[str] = Field(
        default=None, description="X-Title header for OpenRouter (optional)"
    )

    # ChromaDB Configuration
    chroma_db_path: str = Field(
        default="./data/chroma_db", description="Path to ChromaDB database"
    )
    chroma_collection_name: str = Field(
        default="documents", description="ChromaDB collection name"
    )

    # MCP Server Configuration
    mcp_server_host: str = Field(
        default="localhost", description="MCP server host"
    )
    mcp_server_port: int = Field(
        default=8001, description="MCP server port"
    )

    # Memory Configuration
    short_term_memory_size: int = Field(
        default=10, description="Number of recent messages to keep in short-term memory"
    )
    long_term_memory_enabled: bool = Field(
        default=True, description="Enable long-term memory"
    )
    max_context_tokens: int = Field(
        default=4000, description="Maximum context tokens for LLM"
    )

    # API Configuration
    api_host: str = Field(
        default="0.0.0.0", description="API server host"
    )
    api_port: int = Field(
        default=8000, description="API server port"
    )
    api_debug: bool = Field(
        default=False, description="Enable API debug mode"
    )

    # Web Search Configuration (Optional)
    tavily_api_key: Optional[str] = Field(
        default=None, description="Tavily API key for web search"
    )
    serper_api_key: Optional[str] = Field(
        default=None, description="Serper API key for web search"
    )

    # Database Configuration (Optional)
    database_url: Optional[str] = Field(
        default="sqlite:///./data/app.db", description="Database connection URL"
    )

    # AWS Configuration (Optional)
    aws_access_key_id: Optional[str] = Field(
        default=None, description="AWS access key ID"
    )
    aws_secret_access_key: Optional[str] = Field(
        default=None, description="AWS secret access key"
    )
    aws_region: str = Field(
        default="us-east-1", description="AWS region"
    )
    aws_s3_bucket: Optional[str] = Field(
        default=None, description="AWS S3 bucket name"
    )

    # GCS Configuration (Optional)
    google_application_credentials: Optional[str] = Field(
        default=None, description="Path to GCS service account JSON"
    )
    gcs_bucket_name: Optional[str] = Field(
        default=None, description="GCS bucket name"
    )

    # Snowflake Configuration (Optional)
    snowflake_account: Optional[str] = Field(
        default=None, description="Snowflake account identifier"
    )
    snowflake_user: Optional[str] = Field(
        default=None, description="Snowflake username"
    )
    snowflake_password: Optional[str] = Field(
        default=None, description="Snowflake password"
    )
    snowflake_warehouse: Optional[str] = Field(
        default=None, description="Snowflake warehouse name"
    )
    snowflake_database: Optional[str] = Field(
        default=None, description="Snowflake database name"
    )
    snowflake_schema: Optional[str] = Field(
        default="PUBLIC", description="Snowflake schema name"
    )
    snowflake_role: Optional[str] = Field(
        default="ACCOUNTADMIN", description="Snowflake role"
    )

    # Logging
    log_level: str = Field(
        default="INFO", description="Logging level"
    )

    def get_openai_client_kwargs(self) -> dict:
        """Get kwargs for OpenAI client initialization (supports OpenRouter)."""
        kwargs = {
            "api_key": self.openai_api_key,
        }
        
        # If base_url is provided, use it (for OpenRouter or custom endpoints)
        if self.openai_base_url:
            kwargs["base_url"] = self.openai_base_url
        
        # Add OpenRouter headers if configured
        headers = {}
        if self.openrouter_http_referer:
            headers["HTTP-Referer"] = self.openrouter_http_referer
        if self.openrouter_title:
            headers["X-Title"] = self.openrouter_title
        
        if headers:
            kwargs["default_headers"] = headers
        
        return kwargs

    def get_chroma_client_kwargs(self) -> dict:
        """Get kwargs for ChromaDB client initialization."""
        return {
            "path": self.chroma_db_path,
        }

    def has_web_search(self) -> bool:
        """Check if web search is configured."""
        return bool(self.tavily_api_key or self.serper_api_key)

    def has_cloud_storage(self) -> bool:
        """Check if cloud storage is configured."""
        return bool(
            (self.aws_access_key_id and self.aws_s3_bucket)
            or (self.google_application_credentials and self.gcs_bucket_name)
        )

    def has_snowflake(self) -> bool:
        """Check if Snowflake is configured."""
        return bool(
            self.snowflake_account
            and self.snowflake_user
            and self.snowflake_password
            and self.snowflake_warehouse
            and self.snowflake_database
        )

    def get_snowflake_config(self) -> Optional[Dict[str, Any]]:
        """Get Snowflake configuration dictionary."""
        if not self.has_snowflake():
            return None
        
        return {
            "account": self.snowflake_account,
            "user": self.snowflake_user,
            "password": self.snowflake_password,
            "warehouse": self.snowflake_warehouse,
            "database": self.snowflake_database,
            "schema": self.snowflake_schema,
            "role": self.snowflake_role,
        }


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings() -> None:
    """Reset the global settings instance (useful for testing)."""
    global _settings
    _settings = None

