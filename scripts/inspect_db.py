import sqlite3

conn = sqlite3.connect("D:/eco_nojin/data/econojin.db")
cursor = conn.cursor()

cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
tables = cursor.fetchall()
print("Tables:", tables)

cursor.execute("SELECT * FROM land_profiles")
rows = cursor.fetchall()
print("land_profiles:")
for row in rows:
    print(row)

cursor.execute("SELECT * FROM carbon_projects")
rows = cursor.fetchall()
print("carbon_projects:")
for row in rows:
    print(row)

cursor.execute("SELECT * FROM users")
rows = cursor.fetchall()
print("users:")
for row in rows:
    print(row)

cursor.execute('SELECT name FROM sqlite_master WHERE type="table" AND name LIKE "%market%"')
tables = cursor.fetchall()
print("Marketplace tables:", tables)

for t in tables:
    cursor.execute("SELECT * FROM " + t[0])
    rows = cursor.fetchall()
    print(t[0] + ":")
    for row in rows[:5]:
        print(row)

conn.close()
