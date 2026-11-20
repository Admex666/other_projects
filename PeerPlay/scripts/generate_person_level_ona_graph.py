import matplotlib.pyplot as plt
import networkx as nx
import os

def generate_person_level_ona():
    print("🕸️ [ONA GENERATOR] Creating clean person-level ONA graph...")

    G = nx.Graph()

    # 1. Add Persons with metadata
    persons = {
        'Kovács Péter': {'dept': 'Pénzügy', 'team': 'Alfa', 'role': 'Piacszervező Broker', 'color': '#2563EB', 'size': 2600},
        'Nagy Anna': {'dept': 'Pénzügy', 'team': 'Alfa', 'role': 'Pénzügyi Elemző', 'color': '#60A5FA', 'size': 1800},
        'Szabó Tamás': {'dept': 'Gyártás', 'team': 'Béta', 'role': 'Operatív Horgony', 'color': '#059669', 'size': 2600},
        'Tóth Eszter': {'dept': 'Gyártás', 'team': 'Béta', 'role': 'Logisztikus', 'color': '#34D399', 'size': 1800},
        'Horváth Balázs': {'dept': 'K+F', 'team': 'Gamma', 'role': 'Fejlesztési Vezető', 'color': '#7C3AED', 'size': 2100},
        'Varga Dóra': {'dept': 'K+F', 'team': 'Gamma', 'role': 'QA Mérnök', 'color': '#A78BFA', 'size': 1800},
        'Kiss Gergely': {'dept': 'Értékesítés', 'team': 'Delta', 'role': 'Kereskedelmi Vezető', 'color': '#D97706', 'size': 2400},
        'Molnár Zsófia': {'dept': 'Értékesítés', 'team': 'Delta', 'role': 'Termékmenedzser', 'color': '#FBBF24', 'size': 1800},
    }

    for name, data in persons.items():
        G.add_node(name, **data)

    # 2. Add Valid Transactions
    trades = [
        ('Szabó Tamás', 'Kovács Péter', {'weight': 4, 'type': 'solid'}),
        ('Horváth Balázs', 'Kiss Gergely', {'weight': 3, 'type': 'solid'}),
        ('Nagy Anna', 'Varga Dóra', {'weight': 3, 'type': 'solid'}),
        ('Molnár Zsófia', 'Tóth Eszter', {'weight': 3, 'type': 'solid'}),
        ('Kovács Péter', 'Kiss Gergely', {'weight': 4, 'type': 'solid'}),
        ('Kovács Péter', 'Nagy Anna', {'weight': 2, 'type': 'internal'}),
        ('Szabó Tamás', 'Tóth Eszter', {'weight': 2, 'type': 'internal'}),
        ('Horváth Balázs', 'Varga Dóra', {'weight': 2, 'type': 'internal'}),
        ('Kiss Gergely', 'Molnár Zsófia', {'weight': 2, 'type': 'internal'}),
    ]

    for u, v, d in trades:
        G.add_edge(u, v, **d)

    # Manual fixed positions for perfect visual clarity and cluster layout
    # Left: Gyártás (Béta), Right: K+F (Gamma), Top: Pénzügy (Alfa), Bottom: Értékesítés (Delta)
    pos = {
        'Kovács Péter': (-0.15, 0.75),
        'Nagy Anna': (0.35, 0.70),
        'Szabó Tamás': (-0.75, 0.10),
        'Tóth Eszter': (-0.70, -0.45),
        'Kiss Gergely': (-0.10, -0.70),
        'Molnár Zsófia': (-0.45, -0.75),
        'Horváth Balázs': (0.75, -0.15),
        'Varga Dóra': (0.65, 0.40),
    }

    plt.figure(figsize=(10, 5.8), dpi=300, facecolor='#FFFFFF')
    ax = plt.gca()
    ax.set_facecolor('#FFFFFF')

    # Draw Internal team edges (light gray)
    internal_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get('type') == 'internal']
    nx.draw_networkx_edges(G, pos, edgelist=internal_edges, width=1.5, edge_color='#CBD5E1', style='dotted', alpha=0.8, ax=ax)

    # Draw Cross-functional trade edges (dark green / bold)
    trade_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get('type') == 'solid']
    edge_widths = [d['weight'] for u, v, d in G.edges(data=True) if d.get('type') == 'solid']
    nx.draw_networkx_edges(G, pos, edgelist=trade_edges, width=edge_widths, edge_color='#0d4638', alpha=0.85, ax=ax)

    # Draw the Critical Silo gap between Szabó Tamás (Gyártás) and Horváth Balázs (K+F)
    ax.annotate(
        "", xy=pos['Horváth Balázs'], xytext=pos['Szabó Tamás'],
        arrowprops=dict(arrowstyle="-", color='#DC2626', linestyle='dashed', linewidth=2.5, alpha=0.9)
    )
    # Add Silo tag in the middle
    mid_x = (pos['Szabó Tamás'][0] + pos['Horváth Balázs'][0]) / 2
    mid_y = (pos['Szabó Tamás'][1] + pos['Horváth Balázs'][1]) / 2
    ax.text(mid_x, mid_y + 0.08, "KRITIKUS SILÓ (0 kapcsolat)", color='#DC2626', fontsize=8.5,
            fontweight='bold', ha='center', va='center',
            bbox=dict(boxstyle="round,pad=0.3", fc="#FEF2F2", ec="#FCA5A5", lw=1))

    # Draw Nodes
    node_colors = [persons[n]['color'] for n in G.nodes()]
    node_sizes = [persons[n]['size'] for n in G.nodes()]
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes, edgecolors='#FFFFFF', linewidths=2.5, ax=ax)

    # Draw Node Labels (Person Name)
    for name, (x, y) in pos.items():
        role = persons[name]['dept']
        is_broker = 'Broker' in persons[name]['role'] or 'Horgony' in persons[name]['role']
        
        # Name inside or just above
        ax.text(x, y, name.replace(' ', '\n'), color='#FFFFFF', fontsize=8, fontweight='bold',
                ha='center', va='center')
        
        # Dept label underneath
        lbl_y = y - 0.12 if y >= 0 else y - 0.12
        if is_broker:
            ax.text(x, lbl_y, f"★ {role} (Broker)", color='#0d4638', fontsize=7, fontweight='bold',
                    ha='center', va='top', bbox=dict(boxstyle="round,pad=0.2", fc="#ECFDF5", ec="#61f27e", lw=1))
        else:
            ax.text(x, lbl_y, role, color='#64748B', fontsize=6.8, fontweight='600',
                    ha='center', va='top')

    # Add legend at bottom
    legend_elements = [
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#2563EB', markersize=10, label='Pénzügy (Alfa)'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#059669', markersize=10, label='Gyártás (Béta)'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#7C3AED', markersize=10, label='K+F (Gamma)'),
        plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='#D97706', markersize=10, label='Értékesítés (Delta)'),
        plt.Line2D([0], [0], color='#0d4638', lw=2.5, label='Kereskedelmi tranzakció'),
        plt.Line2D([0], [0], color='#DC2626', lw=2, linestyle='dashed', label='Hiányzó kapcsolat (Siló)'),
    ]
    ax.legend(handles=legend_elements, loc='upper center', bbox_to_anchor=(0.5, 1.08),
              ncol=6, frameon=False, fontsize=7.2)

    plt.xlim(-1.05, 1.05)
    plt.ylim(-0.95, 0.95)
    plt.axis('off')
    plt.tight_layout()

    out_path = 'public/images/fluvia_ona_network.png'
    plt.savefig(out_path, format='png', dpi=300, bbox_inches='tight', pad_inches=0.1)
    plt.close()

    print(f"✅ [SUCCESS] Generated clean person-level ONA graph: {out_path}")

if __name__ == '__main__':
    generate_person_level_ona()
