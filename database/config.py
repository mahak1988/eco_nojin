"""Configuration module - provides the database session factory.

Re-exports the shared declarative ``Base`` from :mod:`database.base`
so the invariant ``database.base.Base is database.config.Base`` holds:
every model registers on a single ``MetaData`` registry no matter which
module it was imported through. Two ``Base`` objects would split the
registry and make ``create_all`` create only half the tables.

``SessionLocal`` is a real sessionmaker bound to the *same* shared
in-memory SQLite database the async engine uses (``database.hub``'s
``_ASYNC_DB_URI``). This used to be a separate private ``:memory:``
database, so a row written through the async plane (for example a user
registered via ``POST /api/v1/auth/register``) was invisible to the
sync-plane routes (``GET /api/v1/admin/users``): the two engines had the
same *schema* and different *data*, which read as "the table is always
empty" rather than as a configuration problem. One database, two drivers.

``StaticPool`` keeps exactly one connection so every session sees the
same data (required for seeded test data), and ``timeout=30`` gives a
colliding writer the same 30-second busy wait the file-database pragma
set installs, because a shared-cache database has no per-connection
pragmas to set.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database.base import Base
from database.hub import SHARED_SQLITE_MEMORY_URI

__all__ = ["Base", "SessionLocal", "engine"]

#: Shared in-memory engine, resolved through ``uri=true`` so the SQLite
#: dialect passes ``mode=memory&cache=shared`` to the driver instead of
#: resolving the name as a filesystem path (see the note in
#: ``database/hub.py``). ``StaticPool`` keeps a single connection so
#: every session sees the same rows (required for seeded test data).
engine = create_engine(
    "sqlite:///" + SHARED_SQLITE_MEMORY_URI + "&uri=true",
    connect_args={"uri": True, "check_same_thread": False, "timeout": 30},
    poolclass=StaticPool,
)

#: Session factory bound to the shared engine.
SessionLocal = sessionmaker(bind=engine)
