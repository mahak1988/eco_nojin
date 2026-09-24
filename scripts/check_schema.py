import sqlite3

conn = sqlite3.connect("D:/eco_nojin/data/econojin.db")
cursor = conn.cursor()

# Check existing tables
cursor.execute(
    'SELECT name FROM sqlite_master WHERE type="table" AND (name LIKE "%product%" OR name LIKE "%category%" OR name LIKE "%taxonomy%")'
)
tables = cursor.fetchall()
for t in tables:
    print("Table:", t[0])
    cursor.execute("PRAGMA table_info(" + t[0] + ")")
    cols = cursor.fetchall()
    for c in cols:
        print("  ", c[1], "(", c[2], ")")

# Check all tables
cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
all_tables = cursor.fetchall()
print("\nAll tables:")
for t in all_tables:
    print(" ", t[0])

conn.close()
