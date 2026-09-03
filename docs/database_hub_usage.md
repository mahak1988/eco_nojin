# DataHub Usage Guide

## Overview

The DataHub (`database.hub.DataHub`) is the unified data access layer
for the Eco Nojin project.

## Basic Usage

### Import the hub

```python
from database.hub import hub
```

### SQLAlchemy (Transactional Data)

```python
from database.hub import hub
from database.models import User

# Automatic transaction management
with hub.get_session() as session:
    users = session.query(User).all()
    # commit() happens automatically on success
    # rollback() happens on exception
```

### DuckDB (Analytics)

```python
from database.hub import hub

# Get connection
conn = hub.get_duckdb("master")

# Execute query
result = conn.execute("""
    SELECT * FROM climate_monthly_300sites
    WHERE year = 2020
""").fetchall()

# Or get as pandas DataFrame
df = conn.execute("SELECT * FROM my_table").fetchdf()

# Close when done
conn.close()
```

### SQLite (Manual Data)

```python
from database.hub import hub

conn = hub.get_sqlite("manual")
cursor = conn.cursor()
cursor.execute("SELECT * FROM climate_normals")
rows = cursor.fetchall()
conn.close()
```

### Redis (Cache)

```python
from database.hub import hub

redis = hub.get_redis()
redis.set("key", "value", ex=3600)
value = redis.get("key")
```

## Best Practices

1. **Always use context manager for sessions**

   ```python
   with hub.get_session() as session:
       # ...
   ```

2. **Use the global hub instance**

   ```python
   from database.hub import hub
   # NOT: hub = DataHub()
   ```

3. **Close DuckDB and SQLite connections**

   ```python
   conn = hub.get_duckdb("master")
   try:
       # use conn
   finally:
       conn.close()
   ```

4. **Handle exceptions**

   ```python
   try:
       with hub.get_session() as session:
           # ...
   except Exception as e:
       logger.error(f"Database error: {e}")
       raise
   ```

## Migration Guide

### Old Pattern

```python
from database.config import SessionLocal

session = SessionLocal()
try:
    user = session.query(User).first()
    session.commit()
finally:
    session.close()
```

### New Pattern

```python
from database.hub import hub

with hub.get_session() as session:
    user = session.query(User).first()
```

## Testing

Run the test suite:

```bash
python database/hub/test_hub.py
```

## Troubleshooting

### Module not found: duckdb

```bash
pip install duckdb
```

### Module not found: redis

```bash
pip install redis
```

### Database connection error

Check environment variable:

```bash
echo $DATABASE_URL
```

Or set it manually:

```python
import os
os.environ["DATABASE_URL"] = "sqlite:///data/econojin.db"
```
