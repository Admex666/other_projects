import pandas as pd
import networkx as nx
from pyvis.network import Network
import community as community_louvain # python-louvain
import os

base_path = 'e:/Data/bgg/network_analysis/'
edge_list_file = os.path.join(base_path, 'mech_theme_edgelist.csv')

print(f"Loading edge list from {edge_list_file}...")
edges_df = pd.read_csv(edge_list_file)

# --- 1. Graph Construction ---
print("Building the NetworkX graph...")
# Create an undirected graph from the pandas edgelist
G = nx.from_pandas_edgelist(
    edges_df, 
    source='Source', 
    target='Target', 
    edge_attr='Weight'
)

print(f"Graph initialized with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")

# --- 2. Graph Analytics ---
print("Calculating centrality metrics...")
# Degree: Number of connections
degrees = dict(G.degree(weight='Weight'))
# Betweenness: Bottleneck probability
betweenness = nx.betweenness_centrality(G, weight='Weight')
# PageRank: Influential connection score
pagerank = nx.pagerank(G, weight='Weight')

print("Detecting communities (Louvain method)...")
# partition is a dict of {node: community_id}
partition = community_louvain.best_partition(G, weight='Weight')
num_communities = len(set(partition.values()))
print(f"Detected {num_communities} distinct design communities.")

# Combine analytics into a DataFrame for reporting
node_metrics = []
for node in G.nodes():
    node_metrics.append({
        'Node': node,
        'Degree': degrees[node],
        'Betweenness': betweenness[node],
        'PageRank': pagerank[node],
        'Community': partition[node]
    })

metrics_df = pd.DataFrame(node_metrics)
# Sort by PageRank to find the most "foundational" mechanics/themes
metrics_df = metrics_df.sort_values(by='PageRank', ascending=False)

metrics_out_path = os.path.join(base_path, 'network_metrics.csv')
metrics_df.to_csv(metrics_out_path, index=False)
print(f"Node metrics saved to {metrics_out_path}.")

# Print top 10 most influential nodes
print("\n--- Top 10 Most Influential Nodes (by PageRank) ---")
print(metrics_df[['Node', 'PageRank', 'Community', 'Degree']].head(10))

# --- 3. Visualization Mapping ---
print("\nGenerating PyVis interactive network...")
# Color map for the communities
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
          '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']

net = Network(height='800px', width='100%', bgcolor='#222222', font_color='white')
# Configure physics simulation to layout the graph beautifully
net.barnes_hut()

for node in G.nodes():
    comm_id = partition[node]
    color = colors[comm_id % len(colors)]
    
    # Scale node size logarithmically by degree so big hubs don't blot out the screen entirely
    import math
    size = math.log(degrees[node] + 2) * 4
    
    # Tooltip with metrics
    title = (f"Feature: {node}\n"
             f"Community: {comm_id}\n"
             f"Degree (Co-occurrences): {degrees[node]}\n"
             f"PageRank: {pagerank[node]:.4f}")
             
    net.add_node(node, label=node, title=title, size=size, color=color)

# Add edges, scale visual thickness by log of the weight
for src, dst, data in G.edges(data=True):
    weight = data['Weight']
    # Scaling the line width
    width = math.log1p(weight)
    title = f"Co-occurrences: {weight}"
    net.add_edge(src, dst, value=width, title=title, color='#444444')

viz_out_path = os.path.join(base_path, 'board_game_network.html')
net.save_graph(viz_out_path)
print(f"Interactive visualization saved to {viz_out_path}.")
print("Done!")
