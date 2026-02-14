import sqlite3
import json

# Connect to database
conn = sqlite3.connect('backend/data/users.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Check if encounter exists
print("=" * 60)
print("Checking for enc_tutorial_dummy...")
print("=" * 60)

cursor.execute("SELECT id, zone_id, title, location_lat, location_lon, type FROM encounters WHERE id = 'enc_tutorial_dummy'")
tutorial_enc = cursor.fetchone()

if tutorial_enc:
    print(f"✅ FOUND: {tutorial_enc['id']}")
    print(f"   Zone: {tutorial_enc['zone_id']}")
    print(f"   Title: {tutorial_enc['title']}")
    print(f"   Type: {tutorial_enc['type']}")
    print(f"   Location: ({tutorial_enc['location_lat']}, {tutorial_enc['location_lon']})")
else:
    print("❌ NOT FOUND in database!")

print("\n" + "=" * 60)
print("All encounters in zone_tutorial:")
print("=" * 60)

cursor.execute("SELECT id, title, location_lat, location_lon FROM encounters WHERE zone_id = 'zone_tutorial'")
zone_encs = cursor.fetchall()

if zone_encs:
    for enc in zone_encs:
        print(f"  - {enc['id']}: {enc['title']} @ ({enc['location_lat']}, {enc['location_lon']})")
else:
    print("  (no encounters found)")

print("\n" + "=" * 60)
print("Quest tutorial_01 stages:")
print("=" * 60)

cursor.execute("SELECT id, stages FROM quests WHERE id = 'quest_tutorial_01'")
quest = cursor.fetchone()

if quest:
    stages = json.loads(quest['stages'])
    for stage in stages:
        print(f"  Stage: {stage['id']}")
        print(f"    Location: {stage.get('location', 'N/A')}")
        print(f"    Encounter: {stage.get('encounter_id', 'N/A')}")
else:
    print("  Quest not found!")

conn.close()
