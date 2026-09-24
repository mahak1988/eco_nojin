"""LLM Router with Fallback Chain — Cloud-Native, Free Tier Only.

Supports: Groq → OpenRouter → Google AI → Mistral → DeepSeek
All OpenAI-compatible endpoints.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from typing import Any

import httpx
from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


class LLMProvider(Enum):
    GROQ = "groq"
    OPENROUTER = "openrouter"
    GOOGLE = "google"
    MISTRAL = "mistral"
    DEEPSEEK = "deepseek"


@dataclass
class ProviderConfig:
    name: LLMProvider
    base_url: str
    api_key_env: str
    models: dict[str, str]  # alias -> model_id
    supports_tools: bool
    rpm_limit: int
    rpd_limit: int


PROVIDER_CHAIN = [
    ProviderConfig(
        name=LLMProvider.GROQ,
        base_url="https://api.groq.com/openai/v1",
        api_key_env="GROQ_API_KEY",
        models={
            "default": "llama-3.3-70b-versatile",
            "fast": "llama-3.1-8b-instant",
            "tools": "qwen/qwen3-32b",
            "reasoning": "openai/gpt-oss-120b",
        },
        supports_tools=True,  # only specific models
        rpm_limit=6000,
        rpd_limit=1000,
    ),
    ProviderConfig(
        name=LLMProvider.OPENROUTER,
        base_url="https://openrouter.ai/api/v1",
        api_key_env="OPENROUTER_API_KEY",
        models={
            "default": "meta-llama/llama-3.3-70b-instruct:free",
            "fast": "meta-llama/llama-3.1-8b-instruct:free",
            "tools": "qwen/qwen-2.5-72b-instruct:free",
        },
        supports_tools=True,
        rpm_limit=60,
        rpd_limit=1000,
    ),
    ProviderConfig(
        name=LLMProvider.GOOGLE,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai",
        api_key_env="GOOGLE_API_KEY",
        models={
            "default": "gemini-1.5-flash",
            "fast": "gemini-1.5-flash-8b",
        },
        supports_tools=True,
        rpm_limit=1500,
        rpd_limit=1500,
    ),
    ProviderConfig(
        name=LLMProvider.MISTRAL,
        base_url="https://api.mistral.ai/v1",
        api_key_env="MISTRAL_API_KEY",
        models={
            "default": "mistral-large-latest",
            "fast": "mistral-small-latest",
        },
        supports_tools=True,
        rpm_limit=60,
        rpd_limit=1000,
    ),
    ProviderConfig(
        name=LLMProvider.DEEPSEEK,
        base_url="https://api.deepseek.com/v1",
        api_key_env="DEEPSEEK_API_KEY",
        models={
            "default": "deepseek-chat",
            "reasoning": "deepseek-reasoner",
        },
        supports_tools=False,
        rpm_limit=60,
        rpd_limit=1000,
    ),
]


@dataclass
class QuotaState:
    provider: LLMProvider
    requests_today: int = 0
    requests_this_minute: int = 0
    last_reset_day: str = ""
    last_reset_minute: str = ""

    def can_make_request(self, config: ProviderConfig) -> bool:
        from datetime import datetime
        now = datetime.utcnow()
        today = now.strftime("%Y-%m-%d")
        minute = now.strftime("%Y-%m-%d-%H-%M")

        if self.last_reset_day != today:
            self.requests_today = 0
            self.last_reset_day = today

        if self.last_reset_minute != minute:
            self.requests_this_minute = 0
            self.last_reset_minute = minute

        return (
            self.requests_today < config.rpd_limit
            and self.requests_this_minute < config.rpm_limit
        )

    def record_request(self):
        self.requests_today += 1
        self.requests_this_minute += 1


class QuotaTracker:
    """In-memory quota tracker with file persistence option."""

    def __init__(self, state_file: str | None = None):
        self.state_file = state_file
        self.quotas: dict[LLMProvider, QuotaState] = {
            p.name: QuotaState(p.name) for p in PROVIDER_CHAIN
        }
        self._load()

    def _load(self):
        if self.state_file and os.path.exists(self.state_file):
            import json
            with open(self.state_file) as f:
                data = json.load(f)
            for k, v in data.items():
                if k in self.quotas:
                    qs = self.quotas[k]
                    qs.requests_today = v.get("requests_today", 0)
                    qs.last_reset_day = v.get("last_reset_day", "")
                    qs.requests_this_minute = v.get("requests_this_minute", 0)
                    qs.last_reset_minute = v.get("last_reset_minute", "")

    def _save(self):
        if self.state_file:
            import json
            data = {
                k: {
                    "requests_today": v.requests_today,
                    "requests_this_minute": v.requests_this_minute,
                    "last_reset_day": v.last_reset_day,
                    "last_reset_minute": v.last_reset_minute,
                }
                for k, v in self.quotas.items()
            }
            with open(self.state_file, "w") as f:
                json.dump(data, f)

    def get_quota(self, provider: LLMProvider) -> QuotaState:
        return self.quotas[provider]

    def can_use(self, provider: LLMProvider) -> bool:
        config = next(p for p in PROVIDER_CHAIN if p.name == provider)
        return self.quotas[provider].can_make_request(config)

    def record(self, provider: LLMProvider):
        self.quotas[provider].record_request()
        self._save()


class LLMRouter:
    """Main router handling provider fallback and quota management."""

    def __init__(self, quota_file: str | None = None):
        self.quota = QuotaTracker(quota_file)
        self._clients: dict[LLMProvider, AsyncOpenAI] = {}
        self._init_clients()

    def _init_clients(self):
        for config in PROVIDER_CHAIN:
            api_key = os.getenv(config.api_key_env)
            if api_key:
                self._clients[config.name] = AsyncOpenAI(
                    base_url=config.base_url,
                    api_key=api_key,
                    timeout=httpx.Timeout(60.0, connect=10.0),
                )

    def _get_client(self, provider: LLMProvider) -> AsyncOpenAI | None:
        return self._clients.get(provider)

    def _get_config(self, provider: LLMProvider) -> ProviderConfig:
        return next(p for p in PROVIDER_CHAIN if p.name == provider)

    def _resolve_model(self, provider: LLMProvider, model_alias: str) -> str:
        config = self._get_config(provider)
        return config.models.get(model_alias, config.models["default"])

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.RequestError)),
    )
    async def _call_provider(
        self,
        provider: LLMProvider,
        model_alias: str,
        messages: list[dict],
        tools: list[dict] | None = None,
        stream: bool = False,
        **kwargs,
    ) -> Any:
        client = self._get_client(provider)
        if not client:
            raise RuntimeError(f"No client for {provider.value}")

        model = self._resolve_model(provider, model_alias)
        config = self._get_config(provider)

        if tools and not config.supports_tools:
            raise ValueError(f"Provider {provider.value} does not support tools")

        self.quota.record(provider)

        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            stream=stream,
            **kwargs,
        )
        return response

    async def chat(
        self,
        messages: list[dict],
        model_alias: str = "default",
        tools: list[dict] | None = None,
        stream: bool = False,
        **kwargs,
    ) -> Any:
        """Chat with automatic fallback across providers."""
        last_error = None

        for config in PROVIDER_CHAIN:
            provider = config.name
            if not self.quota.can_use(provider):
                continue
            if not self._get_client(provider):
                continue

            try:
                return await self._call_provider(
                    provider, model_alias, messages, tools, stream, **kwargs
                )
            except httpx.HTTPStatusError as e:
                if e.response.status_code in (429, 500, 502, 503, 504):
                    last_error = e
                    continue
                raise
            except (httpx.RequestError, httpx.TimeoutException) as e:
                last_error = e
                continue

        raise RuntimeError(f"All providers failed. Last error: {last_error}")

    async def chat_stream(
        self,
        messages: list[dict],
        model_alias: str = "default",
        tools: list[dict] | None = None,
        **kwargs,
    ):
        """Streaming chat with fallback."""
        async for chunk in await self.chat(
            messages, model_alias, tools, stream=True, **kwargs
        ):
            yield chunk

    def get_available_providers(self) -> list[dict]:
        """Get status of all providers."""
        return [
            {
                "provider": p.name.value,
                "available": self.quota.can_use(p.name) and self._get_client(p.name) is not None,
                "quota_today": f"{self.quota.get_quota(p.name).requests_today}/{p.rpd_limit}",
                "models": p.models,
                "supports_tools": p.supports_tools,
            }
            for p in PROVIDER_CHAIN
        ]


# Singleton
_router: LLMRouter | None = None


def get_router() -> LLMRouter:
    global _router
    if _router is None:
        _router = LLMRouter("data/llm_quota.json")
    return _router