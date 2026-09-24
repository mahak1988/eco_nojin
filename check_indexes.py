import sqlite3
conn = sqlite3.connect('data/econojin.db')
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='escrow_record'")
for row in cursor.fetchall():
    print(row)
conn.close()