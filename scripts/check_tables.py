#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect("data/econojin.db")
cursor = conn.cursor()
cursor.execute(
    "SELECT name FROM sqlite_master WHERE type='table' AND (name LIKE '%legal%' OR name LIKE '%tool%')"
)
for row in cursor.fetchall():
    print(row[0])
conn.close()
