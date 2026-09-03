"""
database.base
=============

Single source of truth for SQLAlchemy Base class.

All models MUST import Base from this module:

    from database.base import Base

    class MyModel(Base):
        __tablename__ = "my_table"

Do NOT define Base anywhere else in the project.
"""

from sqlalchemy.orm import declarative_base

Base = declarative_base()

__all__ = ["Base"]
