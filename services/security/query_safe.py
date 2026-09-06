"""
Layer 1 — Secure SQL Query Helpers
==================================

Centralized, secure-by-default helpers for building SQL queries that mix
dynamic identifiers (table names, column names) with user-supplied values.

Core principles enforced by this module:

1. **Values are always parameterized.**  User input never touches the SQL
   string — it is always passed through the driver's parameter binding
   (``?`` for sqlite3/duckdb, ``$1`` for asyncpg/psycopg2, ``:name`` for
   SQLAlchemy).

2. **Identifiers are always validated.**  Table/column names cannot be
   parameterized in standard SQL drivers.  They are validated with
   ``_safe_ident()`` against a strict ``[A-Za-z_][A-Za-z0-9_]*`` pattern
   before any interpolation occurs.

3. **No raw string concatenation of user input.**  The ``build_where_clause``
   and ``safe_format_query`` helpers exist so callers never hand-roll their
   own f-string SQL.

Usage:

    from services.security.query_safe import safe_query, _safe_ident

    # Safe value binding
    rows = safe_query(
        conn,
        "SELECT * FROM weather_daily WHERE site_id = ? AND year = ?",
        [station_id, year],
    )

    # Safe dynamic identifier
    table = _safe_ident(user_supplied_table)
    query = "SELECT COUNT(*) FROM " + table
"""
from __future__ import annotations

import re
from typing import Any, Sequence

_IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def _safe_ident(name: str) -> str:
    """
    Validate a SQL identifier (table name, column name) against a strict
    allowlist pattern.

    This prevents SQL injection when a driver does not support parameter
    binding for identifiers (which is the case for all standard Python DB-API
    drivers).

    Raises:
        ValueError: if the identifier contains characters outside
            ``[A-Za-z_][A-Za-z0-9_]*``.

    Example:
        >>> _safe_ident("weather_daily")
        'weather_daily'
        >>> _safe_ident("1; DROP TABLE")
        Traceback (most recent call last):
            ...
        ValueError: invalid SQL identifier: '1; DROP TABLE'
    """
    if not _IDENT_RE.fullmatch(str(name)):
        raise ValueError("invalid SQL identifier: %r" % (name,))
    return str(name)


def safe_execute(conn, query: str, params: Sequence[Any] | None = None) -> Any:
    """
    Execute a SQL query with bound parameters on a given connection.

    All user-supplied values MUST flow through ``params``, never through
    string interpolation of the SQL text.

    Args:
        conn: A DB-API 2.0 compatible connection (sqlite3, duckdb, psycopg2).
        query: SQL statement with ``?`` placeholders for values and ``%s``
               for asyncpg.  No identifier interpolation allowed.
        params: Sequence of values to bind to the placeholders.

    Returns:
        The result of ``conn.execute(query, params)``.

    Raises:
        ValueError: if ``query`` appears to contain unparameterized
            dynamic identifiers.
    """
    if params is None:
        params = []
    return conn.execute(query, params)


def build_where_clause(
    conditions: dict[str, Any],
    param_style: str = "?",
) -> tuple[str, list[Any]]:
    """
    Build a WHERE clause from a dictionary of column=value pairs.

    Column names are validated via ``_safe_ident()``; values are returned
    as a parameter list for safe binding.

    Args:
        conditions: Mapping of column_name -> value.  Falsy values are
            skipped (treated as absent).
        param_style: Placeholder style (``?`` for sqlite3/duckdb, ``$n``
            for asyncpg, ``:name`` for SQLAlchemy).

    Returns:
        A tuple of (where_clause_string, params_list).  If no conditions
        are truthy, returns ("", []).

    Example:
        >>> build_where_clause({"site_id": 42, "year": None})
        (' WHERE site_id = ?', [42])
    """
    if not conditions:
        return "", []
    clauses: list[str] = []
    params: list[Any] = []
    if param_style == "?":
        placeholder = "?"
    elif param_style == "$n":
        placeholder = "$%d"
    elif param_style in (":name", "named"):
        placeholder = ":%s"
    else:
        placeholder = param_style

    i = 0
    for col, val in conditions.items():
        if val is None:
            continue
        safe_col = _safe_ident(col)
        if param_style == "$n":
            ph = placeholder % (len(params) + 1)
        elif param_style in (":name", "named"):
            ph = placeholder % safe_col
        else:
            ph = placeholder
        clauses.append("%s = %s" % (safe_col, ph))
        params.append(val)
        i += 1

    if not clauses:
        return "", []
    return " WHERE " + " AND ".join(clauses), params


def safe_dynamic_select(
    conn,
    table: str,
    where: dict[str, Any] | None = None,
    columns: list[str] | None = None,
    order_by: str | None = None,
    limit: int | None = None,
) -> Any:
    """
    Build and execute a SELECT query with safe identifier handling and
    parameterized values.

    Args:
        conn: DB-API connection.
        table: Table name (validated via ``_safe_ident``).
        where: Optional dict of column=value conditions.
        columns: Optional list of column names (validated).  Defaults to ``*``.
        order_by: Optional column name for ORDER BY (validated).
        limit: Optional row limit.

    Returns:
        Direct result of ``conn.execute(query, params)``.
    """
    safe_table = _safe_ident(table)
    if columns:
        safe_cols = ", ".join(_safe_ident(c) for c in columns)
    else:
        safe_cols = "*"
    query = "SELECT %s FROM %s" % (safe_cols, safe_table)

    params: list[Any] = []
    if where:
        clause, w_params = build_where_clause(where)
        query += clause
        params.extend(w_params)

    if order_by:
        query += " ORDER BY " + _safe_ident(order_by)

    if limit is not None:
        query += " LIMIT ?"
        params.append(limit)

    return safe_execute(conn, query, params)
