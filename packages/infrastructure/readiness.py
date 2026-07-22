from __future__ import annotations

from collections.abc import Callable

from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from packages.domain.ports import ReadinessProbe
from packages.infrastructure.settings import Settings


class RedisReadinessProbe(ReadinessProbe):
    """Redis adapter used for API readiness checks."""

    def __init__(self, client: Redis) -> None:
        self._client = client

    async def ping(self) -> None:
        await self._client.ping()


class PostgresReadinessProbe(ReadinessProbe):
    """PostgreSQL adapter used for API readiness checks."""

    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    async def ping(self) -> None:
        async with self._engine.connect() as connection:
            await connection.execute(text("SELECT 1"))


def create_readiness_probes(settings: Settings) -> dict[str, ReadinessProbe]:
    """Build runtime adapters without leaking them into the domain package."""

    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    redis_client = Redis.from_url(str(settings.redis_url))
    return {
        "postgres": PostgresReadinessProbe(engine),
        "redis": RedisReadinessProbe(redis_client),
    }


ReadinessProbeFactory = Callable[[Settings], dict[str, ReadinessProbe]]
