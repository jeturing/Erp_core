"""API gateway access levels and permission helpers."""

from __future__ import annotations

from enum import Enum


class ApiAccessLevel(str, Enum):
    INTERNAL = "internal"
    PARTNER = "partner"
    SENSITIVE = "sensitive"


PERMISSION_BY_LEVEL = {
    ApiAccessLevel.INTERNAL: "gateway:level:internal",
    ApiAccessLevel.PARTNER: "gateway:level:partner",
    ApiAccessLevel.SENSITIVE: "gateway:level:sensitive",
}


LEVEL_ORDER = {
    ApiAccessLevel.INTERNAL: 1,
    ApiAccessLevel.PARTNER: 2,
    ApiAccessLevel.SENSITIVE: 3,
}


def normalize_level(value: str | ApiAccessLevel | None) -> ApiAccessLevel:
    if isinstance(value, ApiAccessLevel):
        return value
    raw = str(value or "internal").strip().lower()
    if raw in {"sensitive", "level3", "level_3", "dbbis"}:
        return ApiAccessLevel.SENSITIVE
    if raw in {"partner", "level2", "level_2"}:
        return ApiAccessLevel.PARTNER
    return ApiAccessLevel.INTERNAL


def has_level_permission(permissions: list[str] | None, required_level: ApiAccessLevel) -> bool:
    """Checks hierarchical access by permission list.

    Accepted permission strings:
    - gateway:level:internal
    - gateway:level:partner
    - gateway:level:sensitive
    - *
    """
    granted = set(permissions or [])
    if "*" in granted:
        return True

    max_level = ApiAccessLevel.INTERNAL
    for level, perm in PERMISSION_BY_LEVEL.items():
        if perm in granted:
            if LEVEL_ORDER[level] > LEVEL_ORDER[max_level]:
                max_level = level

    return LEVEL_ORDER[max_level] >= LEVEL_ORDER[required_level]
