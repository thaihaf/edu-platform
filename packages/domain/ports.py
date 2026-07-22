from __future__ import annotations

from typing import Protocol


class ReadinessProbe(Protocol):
    """Port used by the API to verify a required runtime dependency."""

    async def ping(self) -> None:
        """Raise an exception when the dependency is unavailable."""
