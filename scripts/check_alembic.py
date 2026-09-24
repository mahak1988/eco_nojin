#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect("data/econojin.db")
cursor = conn.cursor()
cursor.execute("SELECT version_num FROM alembic_version")
for row in cursor.fetchall():
    print(row[0])
conn.close()
