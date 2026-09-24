"""Embedding Service — Cloud-Native, Free Tier Only.

Providers: Jina AI v3 → Cloudflare Workers AI → Cohere
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from enum import Enum
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


class EmbeddingProvider(Enum):
    JINA = "jina"
    CLOUDFLARE = "cloudflare"
    COHERE = "cohere"


@dataclass
class EmbeddingConfig:
    name: EmbeddingProvider
    api_key_env: str
    base_url: str
    model: str
    dimensions: int
    rpm_limit: int
    rpd_limit: int
    token_limit_monthly: int | None = None


EMBEDDING_CHAIN = [
    EmbeddingConfig(
        name=EmbeddingProvider.JINA,
        api_key_env="JINA_API_KEY",
        base_url="https://api.jina.ai/v1",
        model="jina-embeddings-v3",
        dimensions=768,
        rpm_limit=100,
        rpd_limit=2000,
        token_limit_monthly=10_000_000,
    ),
    EmbeddingConfig(
        name=EmbeddingProvider.CLOUDFLARE,
        api_key_env="CLOUDFLARE_API_TOKEN",
        base_url="https://api.cloudflare.com/client/v4/accounts",
        model="@cf/baai/bge-m3",
        dimensions=1024,
        rpm_limit=1000,
        rpd_limit=10000,
        token_limit_monthly=None,
    ),
    EmbeddingConfig(
        name=EmbeddingProvider.COHERE,
        api_key_env="COHERE_API_KEY",
        base_url="https://api.cohere.ai/v1",
        model="embed-multilingual-v3.0",
        dimensions=1024,
        rpm_limit=100,
        rpd_limit=1000,
        token_limit_monthly=None,
    ),
]


@dataclass
class EmbeddingQuota:
    provider: EmbeddingProvider
    tokens_today: int = 0
    tokens_this_month: int = 0
    requests_today: int = 0
    requests_this_minute: int = 0
    last_reset_day: str = ""
    last_reset_month: str = ""
    last_reset_minute: str = ""

    def can_make_request(self, config: EmbeddingConfig, est_tokens: int = 0) -> bool:
        from datetime import datetime
        now = datetime.utcnow()
        today = now.strftime("%Y-%m-%d")
        month = now.strftime("%Y-%m")
        minute = now.strftime("%Y-%m-%d-%H-%M")

        if self.last_reset_day != today:
            self.requests_today = 0
            self.tokens_today = 0
            self.last_reset_day = today

        if self.last_reset_month != month:
            self.tokens_this_month = 0
            self.last_reset_month = month

        if self.last_reset_minute != minute:
            self.requests_this_minute = 0
            self.last_reset_minute = minute

        ok = (
            self.requests_today < config.rpd_limit
            and self.requests_this_minute < config.rpm_limit
        )

        if config.token_limit_monthly:
            ok = ok and (self.tokens_this_month + est_tokens) < config.token_limit_monthly

        return ok

    def record(self, tokens: int = 0):
        self.requests_today += 1
        self.requests_this_minute += 1
        self.tokens_today += tokens
        self.tokens_this_month += tokens


class EmbeddingQuotaTracker:
    def __init__(self, state_file: str | None = None):
        self.state_file = state_file
        self.quotas: dict[EmbeddingProvider, EmbeddingQuota] = {
            c.name: EmbeddingQuota(c.name) for c in EMBEDDING_CHAIN
        }
        self._load()

    def _load(self):
        if self.state_file and os.path.exists(self.state_file):
            import json
            with open(self.state_file) as f:
                data = json.load(f)
            for k, v in data.items():
                if k in self.quotas:
                    q = self.quotas[k]
                    q.tokens_today = v.get("tokens_today", 0)
                    q.tokens_this_month = v.get("tokens_this_month", 0)
                    q.requests_today = v.get("requests_today", 0)
                    q.requests_this_minute = v.get("requests_this_minute", 0)
                    q.last_reset_day = v.get("last_reset_day", "")
                    q.last_reset_month = v.get("last_reset_month", "")
                    q.last_reset_minute = v.get("last_reset_minute", "")

    def _save(self):
        if self.state_file:
            import json
            data = {
                k: {
                    "tokens_today": v.tokens_today,
                    "tokens_this_month": v.tokens_this_month,
                    "requests_today": v.requests_today,
                    "requests_this_minute": v.requests_this_minute,
                    "last_reset_day": v.last_reset_day,
                    "last_reset_month": v.last_reset_month,
                    "last_reset_minute": v.last_reset_minute,
                }
                for k, v in self.quotas.items()
            }
            with open(self.state_file, "w") as f:
                json.dump(data, f)

    def get(self, provider: EmbeddingProvider) -> EmbeddingQuota:
        return self.quotas[provider]

    def can_use(self, provider: EmbeddingProvider, est_tokens: int = 0) -> bool:
        config = next(c for c in EMBEDDING_CHAIN if c.name == provider)
        return self.quotas[provider].can_make_request(config, est_tokens)

    def record(self, provider: EmbeddingProvider, tokens: int = 0):
        self.quotas[provider].record(tokens)
        self._save()


class EmbeddingService:
    def __init__(self, quota_file: str | None = None, target_dim: int = 768):
        self.quota = EmbeddingQuotaTracker(quota_file)
        self.target_dim = target_dim
        self._clients: dict[EmbeddingProvider, httpx.AsyncClient] = {}
        self._init_clients()

    def _init_clients(self):
        for config in EMBEDDING_CHAIN:
            api_key = os.getenv(config.api_key_env)
            if api_key:
                headers = self._get_headers(config, api_key)
                self._clients[config.name] = httpx.AsyncClient(
                    base_url=config.base_url,
                    headers=headers,
                    timeout=httpx.Timeout(30.0, connect=10.0),
                )

    def _get_headers(self, config: EmbeddingConfig, api_key: str) -> dict[str, str]:
        if config.name == EmbeddingProvider.JINA:
            return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        elif config.name == EmbeddingProvider.CLOUDFLARE:
            return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        elif config.name == EmbeddingProvider.COHERE:
            return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        return {}

    async def _embed_jina(self, texts: list[str]) -> list[list[float]]:
        config = next(c for c in EMBEDDING_CHAIN if c.name == EmbeddingProvider.JINA)
        client = self._clients[EmbeddingProvider.JINA]
        payload = {
            "model": config.model,
            "input": texts,
            "dimensions": self.target_dim,
            "encoding_type": "float",
        }
        response = await client.post("/embeddings", json=payload)
        response.raise_for_status()
        data = response.json()
        return [item["embedding"] for item in data["data"]]

    async def _embed_cloudflare(self, texts: list[str]) -> list[list[float]]:
        config = next(c for c in EMBEDDING_CHAIN if c.name == EmbeddingProvider.CLOUDFLARE)
        client = self._clients[EmbeddingProvider.CLOUDFLARE]
        account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID")
        url = f"/{account_id}/ai/run/{config.model}"
        response = await client.post(url, json={"text": texts})
        response.raise_for_status()
        data = response.json()
        result = data.get("result", {})
        embeddings = result.get("data", [])
        # Resize to target_dim if needed
        if embeddings and len(embeddings[0]) != self.target_dim:
            import numpy as np
            embeddings = [np.array(e[:self.target_dim]).tolist() for e in embeddings]
        return embeddings

    async def _embed_cohere(self, texts: list[str]) -> list[list[float]]:
        config = next(c for c in EMBEDDING_CHAIN if c.name == EmbeddingProvider.COHERE)
        client = self._clients[EmbeddingProvider.COHERE]
        payload = {
            "model": config.model,
            "texts": texts,
            "input_type": "search_document",
            "embedding_types": ["float"],
        }
        response = await client.post("/embed", json=payload)
        response.raise_for_status()
        data = response.json()
        embeddings = data.get("embeddings", {}).get("float", [])
        if embeddings and len(embeddings[0]) != self.target_dim:
            import numpy as np
            embeddings = [np.array(e[:self.target_dim]).tolist() for e in embeddings]
        return embeddings

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.RequestError)),
    )
    async def embed(self, texts: list[str], provider: EmbeddingProvider | None = None) -> list[list[float]]:
        """Embed texts with fallback."""
        providers = [provider] if provider else [c.name for c in EMBEDDING_CHAIN]

        for p in providers:
            if not self.quota.can_use(p, len(" ".join(texts))):
                continue
            if p not in self._clients:
                continue

            try:
                if p == EmbeddingProvider.JINA:
                    result = await self._embed_jina(texts)
                elif p == EmbeddingProvider.CLOUDFLARE:
                    result = await self._embed_cloudflare(texts)
                elif p == EmbeddingProvider.COHERE:
                    result = await self._embed_cohere(texts)
                else:
                    continue

                # Estimate tokens
                est_tokens = sum(len(t) // 4 for t in texts)
                self.quota.record(p, est_tokens)
                return result
            except httpx.HTTPStatusError as e:
                if e.response.status_code in (429, 500, 502, 503, 504):
                    continue
                raise
            except (httpx.RequestError, httpx.TimeoutException):
                continue

        raise RuntimeError("All embedding providers failed")

    async def embed_query(self, text: str) -> list[float]:
        """Embed single query."""
        result = await self.embed([text])
        return result[0]

    async def close(self):
        for client in self._clients.values():
            await client.aclose()


# Singleton
_embedding_service: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService("data/embedding_quota.json")
    return _embedding_service