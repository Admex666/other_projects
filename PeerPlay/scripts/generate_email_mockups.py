import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
from PIL import Image, ImageDraw, ImageFont

os.makedirs('public/images', exist_ok=True)

def generate_mobile_hud():
    w, h = 640, 1080
    img = Image.new('RGB', (w, h), color='#F8FAFC')
    draw = ImageDraw.Draw(img)

    # Phone outer frame / card
    draw.rounded_rectangle([20, 20, w-20, h-20], radius=32, fill='#FFFFFF', outline='#CBD5E1', width=3)
    
    # Phone speaker notch
    draw.rounded_rectangle([w//2 - 50, 32, w//2 + 50, 40], radius=4, fill='#E2E8F0')

    # Top Status / Session Header
    draw.rectangle([22, 55, w-22, 115], fill='#FFFFFF')
    draw.line([36, 115, w-36, 115], fill='#F1F5F9', width=2)
    
    # Brand / Participant name
    draw.text((40, 72), "Kovács Péter", fill='#0F172A', font=None)
    draw.text((40, 88), "Alfa Vállalat · Pénzügy & Kontrolling", fill='#64748B', font=None)
    
    # Phase pill & PIN
    draw.rounded_rectangle([w - 180, 72, w - 105, 96], radius=6, fill='#EFF6FF', outline='#BFDBFE', width=1)
    draw.text((w - 170, 77), "KÖZÉPIDŐ", fill='#1D4ED8', font=None)
    
    draw.rounded_rectangle([w - 95, 72, w - 40, 96], radius=6, fill='#F1F5F9', outline='#E2E8F0', width=1)
    draw.text((w - 85, 77), "PIN: DEMO01", fill='#475569', font=None)

    # Main Card: Team Balance Summary (Dark slate theme)
    draw.rounded_rectangle([40, 135, w-40, 325], radius=16, fill='#0F172A')
    draw.text((60, 155), "SAJÁT VÁLLALATI MÉRLEG", fill='#94A3B8', font=None)
    draw.text((60, 180), "Alfa Vállalat (Tőkeerős Profil)", fill='#FFFFFF', font=None)
    
    # Cash Balance
    draw.text((w - 200, 155), "KÉSZPÉNZ", fill='#94A3B8', font=None)
    draw.text((w - 200, 175), "$1,250", fill='#34D399', font=None)

    # Inventory Pills Grid
    pills = [
        ("PAPÍR", "4 ív", 60),
        ("OLLÓ", "2 db", 195),
        ("VONALZÓ", "1 db", 330),
        ("SABLON", "1 db", 465),
    ]
    for label, val, x in pills:
        draw.rounded_rectangle([x, 245, x + 115, 305], radius=10, fill='#1E293B')
        draw.text((x + 15, 255), label, fill='#94A3B8', font=None)
        draw.text((x + 15, 275), val, fill='#F8FAFC', font=None)

    # Tab bar: Csereüzlet / Banki eladás
    draw.rounded_rectangle([40, 345, w-40, 395], radius=12, fill='#E2E8F0')
    draw.rounded_rectangle([44, 349, w//2 - 5, 391], radius=10, fill='#FFFFFF')
    draw.text((105, 362), "Csereüzlet (P2P)", fill='#2563EB', font=None)
    draw.text((w//2 + 65, 362), "Banki Eladás", fill='#64748B', font=None)

    # Section 1: Active Trade Offer Card
    draw.rounded_rectangle([40, 415, w-40, 615], radius=16, fill='#FFFFFF', outline='#E2E8F0', width=2)
    draw.rounded_rectangle([55, 430, 180, 452], radius=6, fill='#EFF6FF')
    draw.text((65, 434), "BEÉRKEZŐ AJÁNLAT", fill='#1D4ED8', font=None)
    draw.text((w - 180, 434), "Béta Vállalat ➔", fill='#0F172A', font=None)

    # Offered & Requested boxes
    draw.rounded_rectangle([55, 465, w//2 - 10, 535], radius=10, fill='#F8FAFC', outline='#CBD5E1', width=1)
    draw.text((70, 475), "FELAJÁNLVA:", fill='#64748B', font=None)
    draw.text((70, 498), "3 ív A4 Papírlap", fill='#0F172A', font=None)

    draw.rounded_rectangle([w//2 + 10, 465, w - 55, 535], radius=10, fill='#F8FAFC', outline='#CBD5E1', width=1)
    draw.text((w//2 + 25, 475), "KÉRNEK CSERÉBE:", fill='#64748B', font=None)
    draw.text((w//2 + 25, 498), "$40 Készpénz", fill='#0F172A', font=None)

    # Action buttons
    draw.rounded_rectangle([55, 555, w//2 - 10, 595], radius=8, fill='#2563EB')
    draw.text((105, 568), "Elfogadás ✓", fill='#FFFFFF', font=None)

    draw.rounded_rectangle([w//2 + 10, 555, w - 55, 595], radius=8, fill='#F1F5F9', outline='#CBD5E1', width=1)
    draw.text((w//2 + 60, 568), "Elutasítás ✕", fill='#475569', font=None)

    # Section 2: Post-Game Peer Feedback (Live preview)
    draw.rounded_rectangle([40, 635, w-40, 895], radius=16, fill='#FFFFFF', outline='#CBD5E1', width=2)
    draw.rounded_rectangle([55, 650, 205, 672], radius=6, fill='#FDF4FF')
    draw.text((65, 654), "1 ÉRINTÉSES KÉRDŐÍV", fill='#A21CAF', font=None)

    draw.text((55, 685), "1. Ki segítette leginkább a megállapodást kívülről?", fill='#0F172A', font=None)
    
    # Candidate badges
    candidates = [
        ("Horváth Balázs (Gamma · K+F)", 715, True),
        ("Szabó Tamás (Béta · Gyártás)", 760, True),
        ("Kiss Gergely (Delta · Értékesítés)", 805, False)
    ]
    for c_text, c_y, selected in candidates:
        bg = '#EFF6FF' if selected else '#F8FAFC'
        bc = '#3B82F6' if selected else '#E2E8F0'
        tc = '#1E3A8A' if selected else '#475569'
        draw.rounded_rectangle([55, c_y, w - 55, c_y + 38], radius=8, fill=bg, outline=bc, width=1)
        draw.text((75, c_y + 12), c_text, fill=tc, font=None)
        if selected:
            draw.text((w - 95, c_y + 12), "Kiválasztva ✓", fill='#2563EB', font=None)

    # 1..10 Energy Slider
    draw.text((55, 860), "2. Energiaszint a játék végén:  9 / 10 (+3)", fill='#0F172A', font=None)

    # Submit button
    draw.rounded_rectangle([40, 920, w-40, 975], radius=12, fill='#059669')
    draw.text((w//2 - 120, 940), "Válaszok Rögzítése & Frissítés", fill='#FFFFFF', font=None)

    # Real-time sync badge
    draw.text((w//2 - 100, 1010), "⚡ 2 mp valós idejű automata szinkron", fill='#64748B', font=None)

    img.save('public/images/mockup_mobile_hud.png', 'PNG')
    print("✓ Saved public/images/mockup_mobile_hud.png")

def generate_ona_network():
    fig, ax = plt.subplots(figsize=(12, 8), dpi=150)
    fig.patch.set_facecolor('#F8FAFC')
    ax.set_facecolor('#F8FAFC')

    cx, cy = 0.0, 0.0

    participants = [
        {"id": "P1", "name": "Kovács Péter", "dept": "Pénzügy & Kontrolling", "color": "#059669", "x": -2.8, "y": 1.6, "delta": "+2", "votes": 8},
        {"id": "P2", "name": "Nagy Anna", "dept": "Pénzügy & Kontrolling", "color": "#059669", "x": -1.8, "y": 2.7, "delta": "+2", "votes": 4},
        
        {"id": "P3", "name": "Szabó Tamás", "dept": "Termelés & Gyártás", "color": "#D97706", "x": 1.8, "y": 2.7, "delta": "+2", "votes": 8},
        {"id": "P4", "name": "Tóth Eszter", "dept": "Beszerzés & Logisztika", "color": "#475569", "x": 2.8, "y": 1.6, "delta": "+2", "votes": 3},
        
        {"id": "P5", "name": "Horváth Balázs", "dept": "Kutatás-Fejlesztés (K+F)", "color": "#2563EB", "x": 2.6, "y": -1.8, "delta": "+2", "votes": 5},
        {"id": "P6", "name": "Varga Dóra", "dept": "Minőségbiztosítás (QA)", "color": "#E11D48", "x": 1.5, "y": -2.8, "delta": "+2", "votes": 4},
        
        {"id": "P7", "name": "Kiss Gergely", "dept": "Értékesítés & Ügyfél", "color": "#7C3AED", "x": -1.5, "y": -2.8, "delta": "+1", "votes": 6},
        {"id": "P8", "name": "Molnár Zsófia", "dept": "Termékmenedzsment", "color": "#0891B2", "x": -2.6, "y": -1.8, "delta": "+3", "votes": 5},
    ]

    # Draw Central Bank Hub Connections
    for p in participants:
        ax.plot([cx, p["x"] * 0.6], [cy, p["y"] * 0.6], color='#10B981', alpha=0.35, linewidth=2.5, linestyle=':')

    # Draw Peer Trade Edges
    trade_edges = [
        ("P1", "P3", 2, "Papír ➔ Pénz"),
        ("P1", "P5", 1, "Sablon bérlet"),
        ("P3", "P7", 1, "Olló átadás"),
        ("P5", "P7", 1, "Vonalzó csere"),
        ("P1", "P7", 1, "Tőkeinjekció"),
    ]
    p_map = {p["id"]: p for p in participants}

    for src_id, dst_id, weight, label in trade_edges:
        p1 = p_map[src_id]
        p2 = p_map[dst_id]
        ax.annotate("",
            xy=(p2["x"], p2["y"]), xycoords='data',
            xytext=(p1["x"], p1["y"]), textcoords='data',
            arrowprops=dict(arrowstyle="<->", color="#2563EB", lw=weight * 1.8, alpha=0.75, shrinkA=18, shrinkB=18)
        )

    # Draw Peer Nomination Edges
    nomination_edges = [
        ("P7", "P3"), ("P5", "P3"), ("P2", "P3"), ("P4", "P3"),
        ("P3", "P1"), ("P7", "P1"), ("P6", "P1"), ("P8", "P1"),
    ]
    for src_id, dst_id in nomination_edges:
        p1 = p_map[src_id]
        p2 = p_map[dst_id]
        ax.plot([p1["x"], p2["x"]], [p1["y"], p2["y"]], color='#A855F7', linestyle='--', linewidth=1.2, alpha=0.45)

    # Central Bank Box
    bank_box = patches.FancyBboxPatch(
        (cx - 0.8, cy - 0.45), 1.6, 0.9,
        boxstyle="round,pad=0.1,rounding_size=0.15",
        facecolor='#065F46', edgecolor='#10B981', linewidth=2.5, zorder=5
    )
    ax.add_patch(bank_box)
    ax.text(cx, cy + 0.12, "KÖZPONTI BANK", color='#FFFFFF', fontsize=11, fontweight='bold', ha='center', va='center', zorder=6)
    ax.text(cx, cy - 0.15, "Összes kifizetés: $4,900\n8 átvett forma", color='#A7F3D0', fontsize=8, ha='center', va='center', zorder=6)

    # Participant Nodes
    for p in participants:
        radius = 0.38 + (p["votes"] * 0.02)
        circle = patches.Circle((p["x"], p["y"]), radius, facecolor=p["color"], edgecolor='#FFFFFF', linewidth=3, zorder=4, alpha=0.95)
        ax.add_patch(circle)

        ax.text(p["x"], p["y"] + 0.08, p["name"], color='#FFFFFF', fontsize=9.5, fontweight='bold', ha='center', va='center', zorder=6)
        ax.text(p["x"], p["y"] - 0.12, f"ΔE: {p['delta']} · {p['votes']} szavazat", color='#F8FAFC', fontsize=7.5, ha='center', va='center', zorder=6)

        ax.text(p["x"], p["y"] - 0.55, p["dept"], color='#0F172A', fontsize=8, fontweight='semibold', ha='center', va='center',
            bbox=dict(boxstyle="round,pad=0.2", facecolor='#FFFFFF', edgecolor='#CBD5E1', alpha=0.95), zorder=6)

    # Highlight Informal Brokers
    ax.text(-2.8, 2.45, "⭐ FŐ TŐKEKÖZVETÍTŐ (BROKER)", color='#065F46', fontsize=8, fontweight='bold',
        bbox=dict(boxstyle="round,pad=0.25", facecolor='#D1FAE5', edgecolor='#10B981', alpha=0.95))

    ax.text(1.8, 3.55, "⭐ BÁZIS ÉS SZÁLLÍTÓ (BROKER)", color='#92400E', fontsize=8, fontweight='bold',
        bbox=dict(boxstyle="round,pad=0.25", facecolor='#FEF3C7', edgecolor='#F59E0B', alpha=0.95))

    # Silo Alert Banner
    silo_text = "⚠️ SILÓ ÉSZLELVE: Termelés (Béta) és K+F (Gamma) között 0 közvetlen csere történt!\nCsak az Alfa (Pénzügy) és Delta (Értékesítés) tudta összekötni őket."
    ax.text(-4.2, 3.4, silo_text, color='#991B1B', fontsize=8.5, fontweight='bold', va='top',
        bbox=dict(boxstyle="round,pad=0.4", facecolor='#FEE2E2', edgecolor='#F87171', alpha=0.95))

    # KPI Metrics Banner
    kpi_text = "HÁLÓZATI MUTATÓK (ONA):\n• Összekapcsoltság: 83.3%\n• Átl. Energia: +1.75 pont\n• Tárgyalási Elégedettség: 9.0/10\n• Központi Bank Függőség: 97.4%"
    ax.text(4.2, 3.4, kpi_text, color='#1E293B', fontsize=8.5, fontfamily='monospace', va='top', ha='right',
        bbox=dict(boxstyle="round,pad=0.4", facecolor='#F1F5F9', edgecolor='#CBD5E1', alpha=0.95))

    # Legend
    legend_elements = [
        patches.Patch(facecolor='#059669', label='Pénzügy & Kontrolling'),
        patches.Patch(facecolor='#D97706', label='Termelés & Gyártás'),
        patches.Patch(facecolor='#2563EB', label='Kutatás-Fejlesztés (K+F)'),
        patches.Patch(facecolor='#7C3AED', label='Értékesítés & Ügyfél'),
        patches.Patch(facecolor='#E11D48', label='Minőségbiztosítás (QA)'),
        patches.Patch(facecolor='#0891B2', label='Termékmenedzsment'),
    ]
    ax.legend(handles=legend_elements, loc='lower center', ncol=3, frameon=True, facecolor='#FFFFFF', edgecolor='#CBD5E1', fontsize=8, title="VALÓS SZERVEZETI OSZTÁLYOK SZERINTI CSOMÓPONT-SZÍNEZÉS")

    ax.set_xlim(-4.5, 4.5)
    ax.set_ylim(-3.8, 4.0)
    ax.axis('off')

    plt.tight_layout()
    plt.savefig('public/images/mockup_ona_network.png', dpi=180, facecolor=fig.get_facecolor(), bbox_inches='tight')
    plt.close()
    print("✓ Saved public/images/mockup_ona_network.png")

if __name__ == '__main__':
    generate_mobile_hud()
    generate_ona_network()
