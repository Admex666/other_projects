#pip install sentence_transformers
import requests
import openai
import numpy as np
from sentence_transformers import SentenceTransformer

# Beállítások
NOTION_API_KEY = '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'
NOTES_DB_ID = "86585ef1f1a64ab4b183c4f78a452e21"
HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# AI modell betöltése
model = SentenceTransformer("all-MiniLM-L6-v2")

#%%
def get_notes(note_nr):
    """Lekéri a jegyzeteket a Notion adatbázisból."""
    url = f"https://api.notion.com/v1/databases/{NOTES_DB_ID}/query"
    response = requests.post(url, headers=HEADERS)
    data = response.json()
    
    notes = []
    for result in data["results"][:note_nr]:
        note_id = result["id"]
        title = result["properties"]["Name"]["title"][0]["text"]["content"]
        summary = get_block_content(note_id)
        print(f'{title}:\n {summary[:50]}')
        notes.append({"id": note_id, "title": title, "summary": summary})
    
    return notes

def get_block_content(block_id, depth=0):
    """Lekéri egy blokk szöveges tartalmát és annak alpontjait rekurzívan."""
    url = f"https://api.notion.com/v1/blocks/{block_id}/children"
    response = requests.get(url, headers=HEADERS)
    data = response.json()

    content = []
    if "results" in data:
        for block in data["results"]:
            # Ha a block tartalmaz "rich_text" mezőt, kiolvassuk a szöveget
            if "rich_text" in block.get(block["type"], {}):
                rich_text = block[block["type"]]["rich_text"]
                for text_obj in rich_text:
                    indent = "  " * depth  # Behúzás az alpontoknak
                    content.append(f"{indent}{text_obj['plain_text']}")

            # Ha vannak "children" blokkjai (pl. alpontok), akkor rekurzívan lekérjük őket is
            if block.get("has_children", False):
                content.append(get_block_content(block["id"], depth + 1))

    return "\n".join(content)

def compute_embeddings(notes):
    """Számolja az embeddingeket az AI modell segítségével."""
    texts = [note["title"] + " " + note["summary"] for note in notes]
    embeddings = model.encode(texts, convert_to_tensor=True)
    return embeddings

def find_related_notes(notes, embeddings, top_n=3):
    """Kapcsolódó jegyzeteket keres cosine similarity alapján."""
    similarity_matrix = np.inner(embeddings, embeddings)
    related_notes = {}

    for i, note in enumerate(notes):
        sorted_indices = np.argsort(-similarity_matrix[i])  # Legnagyobb értékek elöl
        related_ids = [notes[idx]["id"] for idx in sorted_indices[1:top_n+1]]  # Első helyen önmaga van, azt kihagyjuk
        related_notes[note["id"]] = related_ids
    
    return related_notes

def update_notion_related_notes(related_notes):
    """Frissíti a Notion adatbázist a kapcsolódó jegyzetekkel."""
    for note_id, related_ids in related_notes.items():
        url = f"https://api.notion.com/v1/pages/{note_id}"
        data = {
            "properties": {
                "Related Notes": {
                    "relation": [{"id": rid} for rid in related_ids]
                }
            }
        }
        response = requests.patch(url, headers=HEADERS, json=data)
        print(f"Updated note {note_id} with related notes: {related_ids}")

#%% Run
notes = get_notes(note_nr=10)
embeddings = compute_embeddings(notes)
related_notes = find_related_notes(notes, embeddings, top_n=2)

#%% Checking related notes
for k, v_list in related_notes.items():
    v_titles = []
    for row in notes:
        if row['id'] == k:
            k_title = row['title']
        else:
            pass
        
        for v in v_list:
            if row['id'] == v:
                v_titles.append(row['title'])
    
    print(k_title, v_titles)        

#%%
update_notion_related_notes(related_notes)
