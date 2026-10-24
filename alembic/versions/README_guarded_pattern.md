# Guarded-reconcile pattern for Alembic revisions

Two revisions in this directory express, in Alembic, schema that
`services/api_gateway/main.py::init_db` also builds at runtime with
`Base.metadata.create_all`:

- `20261010_180000_waves_2_6_schema_delta` — the program's own new tables and
  the columns recent waves hung on legacy tables.
- `20261011_090000_remaining_legacy_tables` — every remaining table the
  registry declares that no earlier revision creates.

Both must behave correctly on the two database shapes that exist:

| shape | how it is built | what a guarded op must do |
| --- | --- | --- |
| application/create_all database | `Base.metadata.create_all` — the production shape | **no-op**: every table, column, index and constraint already exists |
| fresh alembic database | `alembic upgrade head` on an empty database | **complete**: create everything the registry declares |

The rules that make both true, learned the hard way:

1. **Read the registry, never re-type it.** The remaining-legacy revision
   iterates `Base.metadata.tables` (frozen table names, live structure).
   Hand-writing 1500 columns is the error this pattern exists to prevent, and
   reading the registry is what keeps the emitted DDL identical to
   `create_all`'s — which is what makes the guarded path a true no-op.
   Freeze the *names*; read the *shape*.
2. **Per-object guards.** `if not inspector.has_table(name)` for tables,
   `name not in live_columns` for columns, `index_name not in live_indexes`
   for indexes, and for unique constraints the column set (SQLite reports
   named *and* inline `UNIQUE` through `get_unique_constraints`, and the
   auto-indexes backing them through neither helper's names — the column set
   is the only reliable identity).
3. **SQLite lessons** (see the docstring of `20261010_180000`):
   - `op.add_column` with a `ForeignKey` raises `NotImplementedError` — use a
     `batch_alter_table` block with a *named* foreign key.
   - A batch `drop_column` on a foreign-key column needs `copy_from`.
   - `alter_column` (e.g. repairing a server default) and
     `create_unique_constraint` (SQLite cannot `ALTER TABLE ... ADD
     CONSTRAINT`) also need batch blocks.
4. **Constraint order is part of the DDL.** The compiler renders constraints
   sorted by `_creation_order`, and `table.constraints` iterates in hash
   order — rebuild constraints in `sorted(..., key=_creation_order)` order or
   the emitted SQL text differs from `create_all`'s (which matters for any
   structural, `sqlite_master`-based before/after comparison).
5. **Foreign-key rule.** Emit a reference only when the referenced table is
   created by this revision or already present in the database (check the
   live `Inspector` online; check the frozen scope offline). A reference to a
   table outside that set would make a fresh database refuse the create.
6. **Offline (`--sql`) mode.** No connection, no `Inspector`: render the
   complete create for the whole scope as if the database were empty, and
   skip the batch-only repair paths. Rendering still exercises the graph,
   every operation call and every type mapping.
7. **Topological order.** Sort tables so every foreign-key target is created
   before its user; a downgrade walks the same order backwards. Deterministic
   tie-breaking (alphabetical per round) keeps two runs identical.
8. **Downgrade symmetry, honestly documented.** `20261011_090000` drops the
   tables it creates. On a create_all-built database that is destructive
   (the upgrade created nothing there), which is why its docstring says to run
   downgrades on scratch databases only.

When adding a wave: enumerate with a diff of `Base.metadata` against the
`_COVERED_BY_EARLIER_REVISIONS` set of the newest revision, add one revision
chained on the current head, and verify on both shapes — fresh database
(`upgrade head` + column/index/constraint samples) and create_all database
(`stamp` the pre-revision head, `upgrade head`, structural dump before/after,
then `downgrade -1` + `upgrade head` and compare again).
