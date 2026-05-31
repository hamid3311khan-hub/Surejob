import sqlite3
conn = sqlite3.connect('surejob.db')
c = conn.cursor()
try:
    c.execute('ALTER TABLE candidates ADD COLUMN resume TEXT')
    conn.commit()
    print("Resume column add ho gaya candidates table me")
except Exception as e:
    print("Error:", e)
conn.close()
