import sqlite3

conn = sqlite3.connect("D:/eco_nojin/data/econojin.db")
cursor = conn.cursor()

cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
tables = cursor.fetchall()

for t in tables:
    name = t[0]
    cursor.execute("SELECT COUNT(*) FROM " + name)
    count = cursor.fetchone()[0]
    if count > 0:
        print(name + ": " + str(count) + " rows")
        cursor.execute("SELECT * FROM " + name + " LIMIT 3")
        rows = cursor.fetchall()
        for row in rows:
            print("  ", row)

conn.close()
