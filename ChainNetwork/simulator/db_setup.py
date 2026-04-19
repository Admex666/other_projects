import sqlite3
import os

def init_db():
    db_path = os.path.join('simulator', 'chainnetwork.db')
    schema_path = os.path.join('simulator', 'schema.sql')
    
    conn = sqlite3.connect(db_path)
    with open(schema_path, 'r') as f:
        schema = f.read()
    
    conn.executescript(schema)
    conn.commit()
    conn.close()
    print(f"Database initialized at {db_path}")

if __name__ == "__main__":
    init_db()
