import requests
import json

# A Notion API kulcs és a database ID-k (jegyzetek és global tags adatbázis)
notion_api_token = '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'
headers = {
    "Authorization": f"Bearer {notion_api_token}",
    "Content-Type": "application/json",
    "Notion-Version": "2021-05-13"  # Az aktuális Notion API verzió
}

# Adatbázisok ID-ja
notes_db_id = "86585ef1f1a64ab4b183c4f78a452e21"
global_tags_db_id = "1b6fe7beaf9d8052883fda36c7c49067"

def get_global_tags():
    url = f"https://api.notion.com/v1/databases/{global_tags_db_id}/query"
    response = requests.post(url, headers=headers)
    data = response.json()

    tags = {}
    for result in data["results"]:
        tag_name = result["properties"]["Tag"]["title"][0]["text"]["content"]
        tag_id = result['id']
        tags[tag_name] = tag_id
    
    return tags

def get_notes():
    url = f"https://api.notion.com/v1/databases/{notes_db_id}/query"
    response = requests.post(url, headers=headers)
    data = response.json()

    notes = []
    for result in data["results"]:
        note_id = result["id"]
        tags = [tag["name"] for tag in result["properties"]["Tags"]["multi_select"]]
        notes.append({"id": note_id, "tags": tags})
    
    return notes

def update_tags(notes, global_tags):
    for note in notes:
        note_id = note["id"]
        current_tags = note["tags"]

        # Új tags listát készítünk, ami csak a globális címkéket tartalmazza
        updated_tags = [global_tags[tag] for tag in current_tags if tag in global_tags]

        # Ha a címkék változtak, frissítjük a jegyzetet
        if updated_tags != current_tags:
            url = f"https://api.notion.com/v1/pages/{note_id}"
            data = {
                "properties": {
                    "Global Tags [PT]": {
                        "relation": [{"id": tag_id} for tag_id in updated_tags]
                    }
                }
            }
            response = requests.patch(url, headers=headers, json=data)
            print(f"Updated tags for note {note_id}: {updated_tags}")


def main():
    # Lekérjük a címkéket és a jegyzeteket
    global_tags = get_global_tags()
    notes = get_notes()

    # Frissítjük a jegyzetek címkéit
    update_tags(notes, global_tags)

if __name__ == "__main__":
    main()
