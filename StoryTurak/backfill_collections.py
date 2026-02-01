import sqlite3
import os

DB_PATH = "backend/data/users.db"

def backfill_collections():
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    print("Backfilling collections based on existing inventory...")
    
    # Select all character items that have a set_id
    query = """
        SELECT ci.character_id, ci.item_id, i.set_id 
        FROM character_items ci 
        JOIN items i ON ci.item_id = i.id 
        WHERE i.set_id IS NOT NULL
    """
    
    c.execute(query)
    rows = c.fetchall()
    
    if not rows:
        print("No items with set_id found in any character inventory.")
    else:
        print(f"Found {len(rows)} potential collection items in inventories.")
        
        added_count = 0
        for r in rows:
            char_id, item_id, set_id = r
            
            # The collection_id column stores the set_id
            # Use INSERT OR IGNORE to add them if missing
            c.execute("""
                INSERT OR IGNORE INTO character_collections (character_id, collection_id, item_id) 
                VALUES (?, ?, ?)
            """, (char_id, set_id, item_id))
            
            if c.rowcount > 0:
                added_count += 1
                
        conn.commit()
        print(f"Successfully backfilled {added_count} missing collection entries.")
        
    conn.close()

if __name__ == "__main__":
    backfill_collections()
