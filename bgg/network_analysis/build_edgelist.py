import pandas as pd
import itertools
import os

base_path = 'e:/Data/bgg/data/'

print("Loading mechanics and themes data...")
mech_df = pd.read_csv(os.path.join(base_path, 'mechanics.csv'))
theme_df = pd.read_csv(os.path.join(base_path, 'themes.csv'))

# Merge them on BGGId so we can cross-pollinate Mechanics AND Themes
combined_df = pd.merge(mech_df, theme_df, on='BGGId', how='inner')
print(f"Loaded {len(combined_df)} games for network processing.")

# We don't need BGGId for the co-occurrence matrix
combined_df = combined_df.drop(columns=['BGGId'])

edges = {}

print("Calculating co-occurrences (this might take a minute)...")
# Iterate row by row
for idx, row in combined_df.iterrows():
    # Find all active mechanics/themes in this specific game
    active_features = row.index[row == 1].tolist()
    
    # If a game has fewer than 2 features, it can't form an edge
    if len(active_features) < 2:
        continue
        
    # Generate all unique pairs (edges) of features in this game
    for pair in itertools.combinations(active_features, 2):
        # Sort to ensure (A, B) is treated the same as (B, A)
        pair = tuple(sorted(pair))
        edges[pair] = edges.get(pair, 0) + 1

print(f"Extracted {len(edges)} unique edges.")

# Convert to DataFrame
edge_list = []
for (source, target), weight in edges.items():
    edge_list.append({
        'Source': source,
        'Target': target,
        'Weight': weight
    })

edge_df = pd.DataFrame(edge_list)

# Filter out very weak connections (noise) to make the graph readable
# E.g. only keep edges where the mechanic/theme combo appears in at least 50 games
threshold = 50
filtered_edge_df = edge_df[edge_df['Weight'] >= threshold].copy()

print(f"Filtered down to {len(filtered_edge_df)} edges (minimum weight {threshold}).")

# Save the edge list
out_path = 'e:/Data/bgg/network_analysis/mech_theme_edgelist.csv'
filtered_edge_df.to_csv(out_path, index=False)
print(f"Edge list saved to {out_path}.")
