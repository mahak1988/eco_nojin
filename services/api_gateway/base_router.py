"""Base router and service with common patterns for Eco Nojin API."""

from __future__ import annotations

import logging
from collections.abc import Generator
from typing import Any, TypeVar

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.hub import hub
from services.api_gateway.exceptions import (
    NotFoundException,
)

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)
M = TypeVar("M")


def get_db() -> Generator[Session, None, None]:
    with hub.get_session() as session:
        yield session


class BaseRouter(APIRouter):
    """Base router with common error handling and logging."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)


class BaseService[M]:
    """Base service with common CRUD patterns and standardized exceptions."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.logger = logging.getLogger(self.__class__.__name__)

    def _commit(self) -> None:
        try:
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            self.logger.error("Commit failed: %s", exc)
            raise

    def _get_or_404(self, query: Any, message: str = "Not found") -> Any:
        result = query.first()
        if not result:
            raise NotFoundException(message)
        return result

    def _get_all(self, query: Any, limit: int | None = None) -> list[Any]:
        if limit is not None:
            query = query.limit(limit)
        return list(query.all())

    def _create(self, model: M) -> M:
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return model

    def _update(self, model: M, **fields: Any) -> M:
        for key, value in fields.items():
            if hasattr(model, key):
                setattr(model, key, value)
        self._commit()
        self.db.refresh(model)
        return model

    def _delete(self, model: M) -> None:
        self.db.delete(model)
        self._commit()

    def _paginate(self, query: Any, skip: int = 0, limit: int = 100) -> list[Any]:
        return list(query.offset(skip).limit(limit).all())
