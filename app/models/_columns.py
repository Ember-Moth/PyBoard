"""PostgreSQL column helpers shared by SQLModel entities."""

from typing import Any

from sqlalchemy import BigInteger, Column, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field

_EPOCH_NOW = text("(floor(extract(epoch from now())))::bigint")
_JSON_OBJECT = text("'{}'::jsonb")
_JSON_ARRAY = text("'[]'::jsonb")


def created_at_field(*, index: bool = False):
    return Field(
        default=None,
        sa_column=Column(BigInteger, nullable=False, index=index, server_default=_EPOCH_NOW),
    )


def updated_at_field(*, index: bool = False):
    return Field(
        default=None,
        sa_column=Column(BigInteger, nullable=False, index=index, server_default=_EPOCH_NOW),
    )


def jsonb_field(*, nullable: bool = True, default: Any = None, default_factory: Any = None):
    kwargs: dict[str, Any] = {
        "sa_column": Column(JSONB, nullable=nullable),
    }
    if default_factory is not None:
        kwargs["default_factory"] = default_factory
    else:
        kwargs["default"] = default
    return Field(**kwargs)


def jsonb_object_field():
    return Field(
        default_factory=dict,
        sa_column=Column(JSONB, nullable=False, server_default=_JSON_OBJECT),
    )


def jsonb_array_field():
    return Field(
        default_factory=list,
        sa_column=Column(JSONB, nullable=False, server_default=_JSON_ARRAY),
    )
