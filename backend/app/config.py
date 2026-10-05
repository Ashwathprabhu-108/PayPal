"""
PayGuard AI — Application Configuration
Reads from environment variables / .env file.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central settings object — loaded once per process."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ───────────────────────────────────────────
    app_env: Literal["development", "production", "test"] = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_debug: bool = True
    frontend_url: str = "http://localhost:5173"

    # ── Database ──────────────────────────────────────────────
    database_url: str = "sqlite+aiosqlite:///./payguard.db"

    # ── LLM Provider ──────────────────────────────────────────
    llm_provider: Literal["gemini", "openai", "anthropic", "none"] = "gemini"

    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-haiku-20240307"

    # ── PayPal ────────────────────────────────────────────────
    paypal_client_id: str = ""
    paypal_client_secret: str = ""
    paypal_base_url: str = "https://api-m.sandbox.paypal.com"

    # ── Currency ──────────────────────────────────────────────
    inr_to_usd_demo_rate: float = 84.0

    # ── Risk Engine Weights (all configurable via env) ─────────
    risk_weight_urgency: int = Field(default=20, ge=0, le=50)
    risk_weight_pressure: int = Field(default=15, ge=0, le=50)
    risk_weight_hide_purpose: int = Field(default=25, ge=0, le=50)
    risk_weight_bypass_payment: int = Field(default=15, ge=0, le=50)
    risk_weight_secrecy: int = Field(default=10, ge=0, le=50)
    risk_weight_impersonation: int = Field(default=20, ge=0, le=50)
    risk_weight_high_amount_tier1: int = Field(default=10, ge=0, le=30)  # > ₹50,000
    risk_weight_high_amount_tier2: int = Field(default=20, ge=0, le=40)  # > ₹1,00,000
    risk_weight_individual_business_mismatch: int = Field(default=15, ge=0, le=40)
    risk_weight_purpose_description_mismatch: int = Field(default=20, ge=0, le=40)
    risk_weight_time_pressure: int = Field(default=10, ge=0, le=30)

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def llm_available(self) -> bool:
        """True if an LLM provider is configured with a non-empty API key."""
        if self.llm_provider == "none":
            return False
        if self.llm_provider == "gemini" and self.gemini_api_key:
            return True
        if self.llm_provider == "openai" and self.openai_api_key:
            return True
        if self.llm_provider == "anthropic" and self.anthropic_api_key:
            return True
        return False

    @property
    def paypal_configured(self) -> bool:
        return bool(self.paypal_client_id and self.paypal_client_secret)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached singleton Settings instance."""
    return Settings()
