import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import MetaData, inspect
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Recommended naming convention used by Alembic
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
metadata = MetaData(naming_convention=convention)


class BaseModel(AsyncAttrs, DeclarativeBase):
    """
    Base class for all SQLAlchemy 2.0 declarative models.
    Provides common columns: id, created_at, updated_at
    """

    metadata = metadata

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert model to dictionary."""
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.id})>"


class SoftDeleteMixin:
    """Mixin to add soft-delete capability."""

    deleted_at: Mapped[datetime | None] = mapped_column(default=None)
