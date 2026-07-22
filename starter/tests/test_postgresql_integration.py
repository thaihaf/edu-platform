"""PostgreSQL integration coverage intentionally requires external infrastructure."""

import os

import pytest


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("POSTGRES_INTEGRATION_URL"), reason="requires PostgreSQL infrastructure"
)
def test_postgresql_integration_placeholder() -> None:
    """Reserved for Docker-capable validation of the production PostgreSQL adapter."""
    pytest.fail("Configure POSTGRES_INTEGRATION_URL and implement against the external database")
