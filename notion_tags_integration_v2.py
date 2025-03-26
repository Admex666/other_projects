#pip install sentence_transformers
import requests
import openai
import numpy as np
from sentence_transformers import SentenceTransformer

# Key, settings
NOTION_API_KEY = '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'
NOTES_DB_ID = "86585ef1f1a64ab4b183c4f78a452e21"
HEADERS = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

# Load AI model
model = SentenceTransformer("all-MiniLM-L6-v2")

#%% Define functions
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
        
        # Címkék lekérése
        tags = result["properties"].get("Tags", {}).get("multi_select", [])
        tag_names = [tag["name"] for tag in tags]
        tags_str = " ".join(tag_names)
        
        notes.append({"id": note_id, "title": title, "summary": summary, "tags": tags_str})
    
    return notes

def get_block_content(block_id, depth=0):
    """Lekéri egy blokk szöveges tartalmát és annak alpontjait rekurzívan."""
    url = f"https://api.notion.com/v1/blocks/{block_id}/children"
    response = requests.get(url, headers=HEADERS)
    data = response.json()

    content = []
    if "results" in data:
        for block in data["results"]:
            if "rich_text" in block.get(block["type"], {}):
                rich_text = block[block["type"]]["rich_text"]
                for text_obj in rich_text:
                    indent = "  " * depth
                    content.append(f"{indent}{text_obj['plain_text']}")

            if block.get("has_children", False):
                content.append(get_block_content(block["id"], depth + 1))

    return "\n".join(content)

def get_page_title(page_id):
    """Lekéri egy oldal címét azonosító alapján."""
    url = f"https://api.notion.com/v1/pages/{page_id}"
    response = requests.get(url, headers=HEADERS)
    data = response.json()
    title_property = data["properties"].get("Name", {}).get("title", [])
    if title_property:
        return title_property[0]["text"]["content"]
    return ""

def compute_embeddings(notes):
    """Számolja az embeddingeket a cím, tartalom és címkék alapján, majd súlyozottan kombinálja őket."""
    title_embeddings = model.encode([note["title"] for note in notes], convert_to_tensor=True)
    content_embeddings = model.encode([note["summary"] for note in notes], convert_to_tensor=True)
    tag_embeddings = model.encode([note["tags"] for note in notes], convert_to_tensor=True)
    
    combined_embeddings = 0.1 * title_embeddings + 0.4 * content_embeddings + 0.5 * tag_embeddings
    return combined_embeddings

def find_related_notes(notes, embeddings, threshold=0.5, max_related=2):
    """Kapcsolódó jegyzeteket keres koszinusz hasonlóság alapján."""
    similarity_matrix = np.inner(embeddings, embeddings)
    related_notes = {}

    for i, note in enumerate(notes):
        similarities = [(j, similarity_matrix[i][j]) for j in range(len(notes)) if i != j]
        filtered_similarities = [item for item in similarities if item[1] >= threshold]
        filtered_similarities.sort(key=lambda x: x[1], reverse=True)
        related_ids = [notes[idx]["id"] for idx, sim in filtered_similarities[:max_related]]
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
        print(f"Frissítve: {note_id} kapcsolódó jegyzetekkel: {related_ids}")

#%% Run
notes = get_notes(note_nr=10)
embeddings = compute_embeddings(notes)
related_notes = find_related_notes(notes, embeddings, threshold=0.3, max_related=2)

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
#update_notion_related_notes(related_notes)
