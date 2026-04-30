import os
import re
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity
import networkx as nx

# --- CONFIGURATION ---
VAULT_PATH = r"E:\obsidian_safe\obsidian_safe"
MODEL_NAME = 'paraphrase-multilingual-MiniLM-L12-v2'
NUM_CLUSTERS = 15  # Adjust based on your vault size
SIMILARITY_THRESHOLD = 0.7  # For graph connections

def clean_text(text):
    # Remove YAML frontmatter
    text = re.sub(r'^---.*?---', '', text, flags=re.DOTALL)
    # Remove Obsidian links [[link|alias]] -> alias or link
    text = re.sub(r'\[\[(?:.*?\|)?(.*?)\]\]', r'\1', text)
    # Remove URLs
    text = re.sub(r'http\S+', '', text)
    return text.strip()

def main():
    print(f"--- Loading Model: {MODEL_NAME} ---")
    model = SentenceTransformer(MODEL_NAME)
    
    files_data = []
    
    print(f"--- Reading files from {VAULT_PATH} ---")
    for root, dirs, files in os.walk(VAULT_PATH):
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        clean_content = clean_text(content)
                        if len(clean_content) > 50:  # Skip very short files
                            files_data.append({
                                'filename': file,
                                'path': file_path,
                                'content': clean_content[:2000] # Limit context for embedding speed
                            })
                except Exception as e:
                    print(f"Error reading {file}: {e}")

    df = pd.DataFrame(files_data)
    print(f"Total valid files found: {len(df)}")

    print("--- Generating Embeddings (this might take a few minutes) ---")
    embeddings = model.encode(df['content'].tolist(), show_progress_bar=True)
    
    print(f"--- Clustering into {NUM_CLUSTERS} groups ---")
    kmeans = KMeans(n_clusters=NUM_CLUSTERS, random_state=42, n_init=10)
    df['cluster'] = kmeans.fit_predict(embeddings)

    # --- Save Results ---
    output_file = "vault_clusters.csv"
    df[['filename', 'cluster', 'path']].to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"--- Results saved to {output_file} ---")

    # --- Generate a simple summary report ---
    print("\n--- Cluster Preview ---")
    for i in range(NUM_CLUSTERS):
        cluster_files = df[df['cluster'] == i]['filename'].head(5).tolist()
        print(f"Cluster {i}: {', '.join(cluster_files)}...")

if __name__ == "__main__":
    main()
