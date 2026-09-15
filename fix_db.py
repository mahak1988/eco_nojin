import sqlite3, sys

db_path = 'D:/eco_nojin/data/econojin.db'
conn = sqlite3.connect(db_path)
cur = conn.cursor()

# Check if 'used' column already exists
cols = [row[1] for row in cur.execute("PRAGMA table_info(password_reset_tokens)").fetchall()]
print(f"Existing columns: {cols}")

if 'used' not in cols:
    cur.execute("ALTER TABLE password_reset_tokens ADD COLUMN used INTEGER DEFAULT 0 NOT NULL")
    print("Added 'used' column")
else:
    print("'used' column already exists")

# Verify
cols = [row[1] for row in cur.execute("PRAGMA table_info(password_reset_tokens)").fetchall()]
print(f"Final columns: {cols}")

conn.commit()
conn.close()
print("Done")