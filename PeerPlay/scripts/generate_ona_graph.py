import os
import matplotlib.pyplot as plt
import networkx as nx

def generate_ona_graph(output_path="public/images/fluvia_ona_network.png"):
    print("🕸️ [ONA GENERATOR] Creating clean person-level ONA graph...")

    G = nx.Graph()

    # 1. Add Persons with real department colors and centrality
    persons = {
        'Kovács Péter': {'dept': 'Pénzügy (Alfa)', 'color': '#2563EB', 'size': 2800, 'role': 'Broker'},
        'Nagy Anna': {'dept': 'Pénzügy (Alfa)', 'color': '#60A5FA', 'size': 1800, 'role': 'Elemző'},
        'Szabó Tamás': {'dept': 'Gyártás (Béta)', 'color': '#059669', 'size': 2800, 'role': 'Horgony'},
        'Tóth Eszter': {'dept': 'Gyártás (Béta)', 'color': '#34D399', 'size': 1800, 'role': 'Beszerző'},
        'Horváth Balázs': {'dept': 'K+F (Gamma)', 'color': '#7C3AED', 'size': 2200, 'role': 'K+F Vezető'},
        'Varga Dóra': {'dept': 'K+F (Gamma)', 'color': '#A78BFA', 'size': 1800, 'role': 'QA Mérnök'},
        'Kiss Gergely': {'dept': 'Értékesítés (Delta)', 'color': '#D97706', 'size': 2500, 'role': 'Kapuőr'},
        'Molnár Zsófia': {'dept': 'Értékesítés (Delta)', 'color': '#FBBF24', 'size': 1800, 'role': 'Termékmenedzser'},
    }

    for name, data in persons.items():
        G.add_node(name, **data)

    # 2. Add Valid Transactions
    trades = [
        ('Szabó Tamás', 'Kovács Péter', {'weight': 4.5, 'type': 'solid'}),
        ('Horváth Balázs', 'Kiss Gergely', {'weight': 3.5, 'type': 'solid'}),
        ('Nagy Anna', 'Varga Dóra', {'weight': 3.0, 'type': 'solid'}),
        ('Molnár Zsófia', 'Tóth Eszter', {'weight': 3.0, 'type': 'solid'}),
        ('Kovács Péter', 'Kiss Gergely', {'weight': 4.5, 'type': 'solid'}),
        ('Kovács Péter', 'Nagy Anna', {'weight': 1.8, 'type': 'internal'}),
        ('Szabó Tamás', 'Tóth Eszter', {'weight': 1.8, 'type': 'internal'}),
        ('Horváth Balázs', 'Varga Dóra', {'weight': 1.8, 'type': 'internal'}),
        ('Kiss Gergely', 'Molnár Zsófia', {'weight': 1.8, 'type': 'internal'}),
    ]

    for u, v, d in trades:
        G.add_edge(u, v, **d)

    # Fixed positions for maximum clarity: Gyártás (Bal), K+F (Jobb), Pénzügy (Fent), Értékesítés (Lent)
    pos = {
        'Kovács Péter': (-0.15, 0.72),
        'Nagy Anna': (0.35, 0.68),
        'Szabó Tamás': (-0.75, 0.08),
        'Tóth Eszter': (-0.68, -0.45),
        'Kiss Gergely': (-0.10, -0.68),
        'Molnár Zsófia': (-0.45, -0.72),
        'Horváth Balázs': (0.75, -0.12),
        'Varga Dóra': (0.65, 0.42),
    }

    plt.figure(figsize=(10.5, 5.2), dpi=300, facecolor='#FFFFFF')
    ax = plt.gca()
    ax.set_facecolor('#FFFFFF')

    # Draw Internal team edges
    internal_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get('type') == 'internal']
    nx.draw_networkx_edges(G, pos, edgelist=internal_edges, width=1.5, edge_color='#CBD5E1', style='dotted', alpha=0.8, ax=ax)

    # Draw Cross-functional trade edges
    trade_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get('type') == 'solid']
    edge_widths = [d['weight'] for u, v, d in G.edges(data=True) if d.get('type') == 'solid']
    nx.draw_networkx_edges(G, pos, edgelist=trade_edges, width=edge_widths, edge_color='#0d4638', alpha=0.85, ax=ax)

    # Draw Critical Silo line
    ax.annotate(
        "", xy=pos['Horváth Balázs'], xytext=pos['Szabó Tamás'],
        arrowprops=dict(arrowstyle="-", color='#DC2626', linestyle='dashed', linewidth=2.5, alpha=0.9)
    )
    mid_x = (pos['Szabó Tamás'][0] + pos['Horváth Balázs'][0]) / 2
    mid_y = (pos['Szabó Tamás'][1] + pos['Horváth Balázs'][1]) / 2
    ax.text(mid_x, mid_y + 0.08, "KRITIKUS SILÓ (0 tranzakció)", color='#DC2626', fontsize=8.5,
            fontweight='bold', ha='center', va='center',
            bbox=dict(boxstyle="round,pad=0.3", fc="#FEF2F2", ec="#FCA5A5", lw=1))

    # Draw Nodes
    node_colors = [persons[n]['color'] for n in G.nodes()]
    node_sizes = [persons[n]['size'] for n in G.nodes()]
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes, edgecolors='#FFFFFF', linewidths=2.5, ax=ax)

    # Node Labels
    for name, (x, y) in pos.items():
        role = persons[name]['dept'].split(' ')[0]
        is_broker = 'Broker' in persons[name]['role'] or 'Horgony' in persons[name]['role']
        
        ax.text(x, y, name.replace(' ', '\n'), color='#FFFFFF', fontsize=8.2, fontweight='bold',
                ha='center', va='center')
        
        lbl_y = y - 0.13
        if is_broker:
            ax.text(x, lbl_y, f"★ {role} (Broker)", color='#0d4638', fontsize=7.2, fontweight='bold',
                    ha='center', va='top', bbox=dict(boxstyle="round,pad=0.2", fc="#ECFDF5", ec="#61f27e", lw=1))
        else:
            ax.text(x, lbl_y, role, color='#64748B', fontsize=7.0, fontweight='600',
                    ha='center', va='top')

    # Legend at top
    legend_elements = [
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#2563EB', markersize=10, label='Pénzügy (Alfa)'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#059669', markersize=10, label='Gyártás (Béta)'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#7C3AED', markersize=10, label='K+F (Gamma)'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#D97706', markersize=10, label='Értékesítés (Delta)'),
        plt.Line2D([0], [0], color='#0d4638', lw=2.5, label='Kereskedelmi Tranzakció'),
        plt.Line2D([0], [0], color='#DC2626', lw=2, linestyle='dashed', label='Hiányzó Kapcsolat (Siló)'),
    ]
    ax.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, 1.10),
              ncol=6, frameon=False, fontsize=7.5)

    plt.xlim(-1.05, 1.05)
    plt.ylim(-0.95, 0.95)
    plt.axis('off')
    plt.tight_layout()

    plt.savefig(output_path, format='png', dpi=300, bbox_inches='tight', pad_inches=0.1)
    plt.close()
    print(f"✅ [SUCCESS] Generated ONA Graph: {output_path}")

if __name__ == '__main__':
    generate_ona_graph()
