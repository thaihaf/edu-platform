"""Framework-independent production security policies."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Role(StrEnum):
    ADMIN = "ADMIN"
    RESEARCHER = "RESEARCHER"
    REVIEWER = "REVIEWER"
    EDITOR = "EDITOR"
    VIEWER = "VIEWER"


class AuthorizationError(PermissionError):
    """Raised when a verified principal lacks a required role."""


@dataclass(frozen=True)
class Principal:
    subject: str
    roles: frozenset[Role]


def require_role(principal: Principal | None, *allowed: Role) -> Principal:
    """Return a verified principal only when it has one of ``allowed`` roles."""

    if principal is None:
        raise AuthorizationError("A verified principal is required")
    if not principal.roles.intersection(allowed):
        raise AuthorizationError("The principal does not have the required role")
    return principal
