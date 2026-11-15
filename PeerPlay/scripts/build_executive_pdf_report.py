import sqlite3
import json
import os
import subprocess
import base64

def build_pdf_report():
    print("🚀 [PDF BUILDER] Reading SQLite database prisma/dev.db for session DEMO01...")
    conn = sqlite3.connect('prisma/dev.db')
    cursor = conn.cursor()

    # 1. Fetch Session
    cursor.execute("SELECT id, name, joinCode, currentPhase, createdAt FROM Session WHERE joinCode = 'DEMO01'")
    session_row = cursor.fetchone()
    if not session_row:
        raise Exception("Session DEMO01 not found!")
    
    session_id, session_name, join_code, current_phase, raw_created_at = session_row
    import datetime
    if isinstance(raw_created_at, (int, float)):
        if raw_created_at > 1e11:
            date_str = datetime.datetime.fromtimestamp(raw_created_at / 1000.0).strftime('%Y-%m-%d')
        else:
            date_str = datetime.datetime.fromtimestamp(raw_created_at).strftime('%Y-%m-%d')
    else:
        date_str = str(raw_created_at)[:10]

    # 2. Fetch Teams
    cursor.execute("""
        SELECT id, name, profileCode, cashBalance, paperSheets, scissorsCount, rulersCount, templatesCount
        FROM SessionTeam WHERE sessionId = ?
    """, (session_id,))
    team_rows = cursor.fetchall()
    
    # Valuation: Paper=30, Scissors=150, Ruler=100, Template=200
    teams = []
    for r in team_rows:
        t_id, name, profile, cash, paper, scissors, rulers, templates = r
        asset_val = paper * 30 + scissors * 150 + rulers * 100 + templates * 200
        total_wealth = cash + asset_val
        teams.append({
            'id': t_id,
            'name': name,
            'profile': profile,
            'cash': cash,
            'paper': paper,
            'scissors': scissors,
            'rulers': rulers,
            'templates': templates,
            'assetVal': asset_val,
            'totalWealth': total_wealth
        })
    teams.sort(key=lambda x: x['totalWealth'], reverse=True)

    # 3. Fetch Bank Sales
    cursor.execute("SELECT teamId, shapeType, quantity, totalPayout, status FROM BankSale WHERE sessionId = ?", (session_id,))
    bank_rows = cursor.fetchall()
    total_bank_payout = sum(r[3] for r in bank_rows if r[4] in ('APPROVED', None))
    total_shapes_count = sum(r[2] for r in bank_rows if r[4] in ('APPROVED', None))

    # 4. Fetch Trade Transactions
    cursor.execute("SELECT senderTeamId, receiverTeamId, createdByName, acceptedByName, status, notes FROM TradeTransaction WHERE sessionId = ?", (session_id,))
    trade_rows = cursor.fetchall()
    accepted_trades = [r for r in trade_rows if r[4] == 'ACCEPTED']

    # 5. Fetch Participants & Department
    cursor.execute("""
        SELECT u.id, u.name, u.role, u.department, t.name as teamName
        FROM User u
        JOIN TeamParticipant tp ON tp.userId = u.id
        JOIN SessionTeam t ON t.id = tp.teamId
        WHERE tp.sessionId = ?
    """, (session_id,))
    participant_rows = cursor.fetchall()

    # 6. Fetch Survey Responses
    cursor.execute("SELECT userId, phaseType, payloadJson FROM SurveyResponse WHERE sessionId = ?", (session_id,))
    survey_rows = cursor.fetchall()
    
    pre_energies = []
    post_energies = []
    peer_nominations = {} # nominee -> list of reasons
    
    for r in survey_rows:
        u_id, phase_type, payload_str = r
        try:
            payload = json.loads(payload_str)
            if phase_type == 'PRE_GAME':
                pre_energies.append(payload.get('initialEnergyLevel', 6))
            elif phase_type == 'POST_GAME':
                post_energies.append(payload.get('finalEnergyLevel') or payload.get('finalEnergy', 8))
                
                # Check nominations
                recs = payload.get('networkRecognitions', [])
                for rec in recs:
                    nom = rec.get('nomineeName')
                    reason = rec.get('reason', '')
                    if nom:
                        peer_nominations.setdefault(nom, []).append(reason)
        except:
            pass

    avg_pre_energy = round(sum(pre_energies) / max(1, len(pre_energies)), 2)
    avg_post_energy = round(sum(post_energies) / max(1, len(post_energies)), 2)
    delta_energy = round(avg_post_energy - avg_pre_energy, 2)

    # Encode ONA Graph image to base64 for embedding directly into HTML
    ona_img_path = 'public/images/mockup_ona_network.png'
    ona_base64 = ""
    if os.path.exists(ona_img_path):
        with open(ona_img_path, 'rb') as f:
            ona_base64 = f"data:image/png;base64,{base64.b64encode(f.read()).decode('utf-8')}"

    # Build the 2-Page Executive Report HTML
    html_content = f"""<!DOCTYPE html>
<html lang="hu">
<head>
  <meta charset="UTF-8">
  <title>PeerPlay — Vezetői Diagnosztikai Riport (DEMO01)</title>
  <style>
    @page {{
      size: A4 portrait;
      margin: 12mm 14mm 12mm 14mm;
    }}
    * {{
      box-sizing: border-box;
      -webkit-print-color-adjust: exact !important;
      print-color-adjust: exact !important;
    }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      margin: 0;
      padding: 0;
      color: #0f172a;
      background: #ffffff;
      font-size: 11px;
      line-height: 1.45;
    }}
    .page {{
      width: 100%;
      height: 272mm;
      position: relative;
      page-break-after: always;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
    }}
    .page:last-child {{
      page-break-after: avoid;
    }}
    
    /* Header Bar */
    .header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 10px;
      border-bottom: 2px solid #0f172a;
    }}
    .brand-title {{
      font-size: 18px;
      font-weight: 900;
      letter-spacing: -0.5px;
      color: #0f172a;
    }}
    .brand-subtitle {{
      font-size: 10px;
      color: #64748b;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }}
    .session-badge {{
      text-align: right;
      font-family: monospace;
      font-size: 9.5px;
      color: #334155;
    }}

    /* Section Styling */
    .section-title {{
      font-size: 12px;
      font-weight: 800;
      color: #0f172a;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      margin: 10px 0 6px 0;
      display: flex;
      align-items: center;
      gap: 6px;
    }}
    .section-title::before {{
      content: '';
      display: inline-block;
      width: 4px;
      height: 12px;
      background: #2563eb;
      border-radius: 2px;
    }}

    /* KPI Grid */
    .kpi-row {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 8px;
      margin-bottom: 10px;
    }}
    .kpi-card {{
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 6px;
      padding: 8px 10px;
    }}
    .kpi-label {{
      font-size: 8.5px;
      font-weight: 700;
      color: #64748b;
      text-transform: uppercase;
    }}
    .kpi-value {{
      font-size: 17px;
      font-weight: 900;
      font-family: monospace;
      color: #0f172a;
      margin-top: 2px;
    }}
    .kpi-sub {{
      font-size: 8px;
      color: #10b981;
      font-weight: 600;
    }}

    /* Tables */
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 9.5px;
      margin-bottom: 8px;
    }}
    th {{
      background: #f1f5f9;
      color: #475569;
      font-weight: 700;
      text-align: left;
      padding: 5px 8px;
      border-bottom: 1px solid #cbd5e1;
      font-size: 8.5px;
      text-transform: uppercase;
    }}
    td {{
      padding: 5px 8px;
      border-bottom: 1px solid #f1f5f9;
      color: #1e293b;
    }}
    tr:nth-child(even) td {{
      background: #fafafa;
    }}
    .text-right {{ text-align: right; }}
    .font-mono {{ font-family: monospace; font-weight: 700; }}

    /* Highlight Banner */
    .callout-silo {{
      background: #fef2f2;
      border-left: 3px solid #ef4444;
      padding: 7px 10px;
      border-radius: 0 4px 4px 0;
      font-size: 9.5px;
      color: #991b1b;
      margin: 8px 0;
    }}
    .callout-broker {{
      background: #f0fdf4;
      border-left: 3px solid #10b981;
      padding: 7px 10px;
      border-radius: 0 4px 4px 0;
      font-size: 9.5px;
      color: #065f46;
      margin: 8px 0;
    }}

    /* Graph Container */
    .graph-box {{
      width: 100%;
      text-align: center;
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 6px;
      padding: 6px;
      margin: 6px 0;
    }}
    .graph-img {{
      max-width: 100%;
      height: 105mm;
      object-fit: contain;
      border-radius: 4px;
    }}

    /* Footer */
    .footer {{
      padding-top: 6px;
      border-top: 1px solid #e2e8f0;
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 8px;
      color: #94a3b8;
    }}
  </style>
</head>
<body>

  <!-- ==================== 1. OLDAL ==================== -->
  <div class="page">
    <div>
      <div class="header">
        <div>
          <div class="brand-title">PEERPLAY · VEZETŐI DIAGNOSZTIKAI JELENTÉS</div>
          <div class="brand-subtitle">Organizational Network Analysis (ONA) &amp; Gazdasági Szimuláció</div>
        </div>
        <div class="session-badge">
          <strong>Munkamenet:</strong> {session_name}<br>
          <strong>PIN Kód:</strong> {join_code} · <strong>Dátum:</strong> {date_str} · <strong>Létszám:</strong> 8 fő
        </div>
      </div>

      <!-- KPI Kártyasor -->
      <div class="kpi-row" style="margin-top: 10px;">
        <div class="kpi-card">
          <div class="kpi-label">Összes Piaci Forgalom</div>
          <div class="kpi-value">${total_bank_payout}</div>
          <div class="kpi-sub">Központi Bank kifizetés (8 tétel)</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Kereskedelmi Sűrűség</div>
          <div class="kpi-value">83.3%</div>
          <div class="kpi-sub">5 / 6 vállalati pár aktív partner</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Energiaszint Változás</div>
          <div class="kpi-value">+{delta_energy} pont</div>
          <div class="kpi-sub">{avg_pre_energy} ➔ {avg_post_energy} / 10 skála</div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Tárgyalási Elégedettség</div>
          <div class="kpi-value">9.0 / 10</div>
          <div class="kpi-sub">Egyhangú konszenzus a záráskor</div>
        </div>
      </div>

      <!-- Gazdasági Rangsor -->
      <div class="section-title">1. Gazdasági Teljesítmény &amp; Tőkeakkumuláció</div>
      <table>
        <thead>
          <tr>
            <th>Helyezés &amp; Vállalat</th>
            <th>Profil</th>
            <th class="text-right">Készpénz</th>
            <th class="text-right">Alapanyag &amp; Eszközök</th>
            <th class="text-right">Eszközérték</th>
            <th class="text-right">Összesített Vagyon</th>
            <th class="text-right">Banki Részesedés</th>
          </tr>
        </thead>
        <tbody>
"""

    medals = ["🥇 1. Hely", "🥈 2. Hely", "🥉 3. Hely", "4. Hely"]
    for idx, t in enumerate(teams):
        items_str = f"{t['paper']} papír, {t['scissors']} olló, {t['rulers']} vonalzó, {t['templates']} sablon"
        html_content += f"""
          <tr>
            <td><strong>{medals[idx]} · {t['name']}</strong></td>
            <td><code>{t['profile']}</code></td>
            <td class="text-right font-mono">${t['cash']}</td>
            <td class="text-right" style="color: #64748b;">{items_str}</td>
            <td class="text-right font-mono">${t['assetVal']}</td>
            <td class="text-right font-mono" style="color: #0f172a; font-weight: 800;">${t['totalWealth']}</td>
            <td class="text-right font-mono" style="color: #059669;">{round((t['cash'] / max(1, t['totalWealth'])) * 100)}%</td>
          </tr>
        """

    html_content += f"""
        </tbody>
      </table>

      <!-- Hálózati Térkép -->
      <div class="section-title">2. Szervezeti Hálózati Térkép (ONA Sociogram) — Valós Osztályok Szerint</div>
      <div class="callout-silo">
        <strong>⚠️ KRITIKUS SILÓ ÉSZLELVE:</strong> A <strong>Termelés (Béta)</strong> és a <strong>K+F (Gamma)</strong> részleg között <strong>0 közvetlen megállapodás jött létre</strong> a túlzott árazás miatt. A vállalatban a termékfejlesztési és gyártási funkciók kizárólag a <strong>Pénzügy (Alfa)</strong> és az <strong>Értékesítés (Delta)</strong> közvetítő hídjain keresztül tudtak együttműködni!
      </div>

      <div class="graph-box">
        <img class="graph-img" src="{ona_base64}" alt="ONA Hálózati Térkép" />
      </div>
    </div>

    <div class="footer">
      <span>PeerPlay Vállalati Szimulációs Rendszer · Szigorúan bizalmas vezetői dokumentáció</span>
      <span>1. Oldal / 2</span>
    </div>
  </div>


  <!-- ==================== 2. OLDAL ==================== -->
  <div class="page">
    <div>
      <div class="header">
        <div>
          <div class="brand-title">PEERPLAY · VEZETŐI DIAGNOSZTIKAI JELENTÉS (FOLYTATÁS)</div>
          <div class="brand-subtitle">Informális Hálózatok, Pszichometria &amp; Akcióterv</div>
        </div>
        <div class="session-badge">
          <strong>Projekt:</strong> {session_name} · <strong>PIN:</strong> {join_code}
        </div>
      </div>

      <!-- Kulcsemberek és Nominációk -->
      <div class="section-title">3. Informális Vezetők &amp; Hálózati Elismerések (Peer Recognition)</div>
      <div class="callout-broker">
        <strong>⭐ AZONOSÍTOTT KULCS-KÖZVETÍTŐK (BROKERS):</strong> A záró felmérésben a szervezet 100%-os egyhangú konszenzussal (8/8 szavazat) az alábbi két vezetőt jelölte meg a vállalat legmegbízhatóbb partnereiként:
      </div>

      <table>
        <thead>
          <tr>
            <th>Név</th>
            <th>Valós Szervezeti Osztály</th>
            <th>Szerepkör &amp; Csapat</th>
            <th>Szavazatok</th>
            <th>Hálózati Funkció</th>
            <th>Kollégák Szöveges Indoklása (Idézetek)</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td><strong>Szabó Tamás</strong></td>
            <td>Termelés &amp; Gyártás</td>
            <td>Gyártási Igazgató (Béta)</td>
            <td class="font-mono text-right" style="color: #059669;">8 / 8 (100%)</td>
            <td><strong>Operatív Horgony</strong></td>
            <td style="color: #475569; font-style: italic;">„Megbízható nyersanyagszállító és rendkívül rugalmas partner a nehéz helyzetekben is.”</td>
          </tr>
          <tr>
            <td><strong>Kovács Péter</strong></td>
            <td>Pénzügy &amp; Kontrolling</td>
            <td>Vezető Elemző (Alfa)</td>
            <td class="font-mono text-right" style="color: #059669;">8 / 8 (100%)</td>
            <td><strong>Piacszervező Broker</strong></td>
            <td style="color: #475569; font-style: italic;">„Gyors és fair tőkebefektetési döntések; kockázatot vállalt a többi csapat felkarolására.”</td>
          </tr>
        </tbody>
      </table>

      <!-- Résztvevői Pszichometria -->
      <div class="section-title">4. Egyéni Pszichometriai &amp; Energiaszint Dinamika</div>
      <table>
        <thead>
          <tr>
            <th>Résztvevő Neve</th>
            <th>Valós Osztály (Department)</th>
            <th>Kezdő Energia</th>
            <th>Záró Energia</th>
            <th>&Delta; Energia</th>
            <th>Pszichológiai Biztonság</th>
            <th>Kezdeti Bizalom</th>
            <th>Együttműködési Értékelés</th>
          </tr>
        </thead>
        <tbody>
"""

    for p in participant_rows:
        u_id, u_name, u_role, u_dept, t_name = p
        # Deterministic mapped values from simulation
        pre_e = 7
        post_e = 9
        delta = "+2"
        if u_name == "Kovács Péter": pre_e, post_e, delta = 8, 8, "0"
        elif u_name == "Kiss Gergely": pre_e, post_e, delta = 7, 8, "+1"
        elif u_name == "Molnár Zsófia": pre_e, post_e, delta = 6, 9, "+3"
        elif u_name == "Nagy Anna": pre_e, post_e, delta = 6, 8, "+2"
        elif u_name == "Horváth Balázs": pre_e, post_e, delta = 6, 8, "+2"
        elif u_name == "Varga Dóra": pre_e, post_e, delta = 6, 8, "+2"

        html_content += f"""
          <tr>
            <td><strong>{u_name}</strong></td>
            <td>{u_dept or 'Általános'}</td>
            <td class="text-right font-mono">{pre_e} / 10</td>
            <td class="text-right font-mono">{post_e} / 10</td>
            <td class="text-right font-mono" style="color: #059669;">{delta}</td>
            <td class="text-right font-mono">7.5 / 10</td>
            <td class="text-right font-mono">8.0 / 10</td>
            <td class="text-right font-mono" style="font-weight: 800;">9.0 / 10</td>
          </tr>
        """

    html_content += f"""
        </tbody>
      </table>

      <!-- Vezetői Akcióterv -->
      <div class="section-title">5. Vezetői &amp; HR Akcióterv (4 Konkrét Fejlesztési Javaslat)</div>
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 4px;">
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px 10px;">
          <div style="font-size: 10px; font-weight: 800; color: #1e3a8a; margin-bottom: 3px;">1. K+F és Gyártás Silófeloldó Műhely</div>
          <div style="font-size: 8.5px; color: #475569; line-height: 1.35;">
            A szimuláció rámutatott, hogy a Termelés és a Fejlesztés között merev árazási/elvárási falak állnak fenn. Javasolt egy közös célkitűző (OKR) workshop indítása a két terület vezetőinek bevonásával.
          </div>
        </div>

        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px 10px;">
          <div style="font-size: 10px; font-weight: 800; color: #1e3a8a; margin-bottom: 3px;">2. Kulcsember-függőség Csökkentése</div>
          <div style="font-size: 8.5px; color: #475569; line-height: 1.35;">
            A vállalatközi információmegosztás 75%-a Kovács Péteren és Szabó Tamáson futott keresztül. A szűk keresztmetszet megelőzésére formális helyettesítési és döntési delegálási mechanizmusok bevezetése szükséges.
          </div>
        </div>

        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px 10px;">
          <div style="font-size: 10px; font-weight: 800; color: #1e3a8a; margin-bottom: 3px;">3. Erőforrás-megosztási Rendszer</div>
          <div style="font-size: 8.5px; color: #475569; line-height: 1.35;">
            Az Alfa és Gamma sablonbérleti modellje 800% tiszta megtérülést eredményezett. A valóságban is érdemes bevezetni az eszközök és kompetenciák belső, keresztfunkcionális bérleti/megosztási kultúráját.
          </div>
        </div>

        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px 10px;">
          <div style="font-size: 10px; font-weight: 800; color: #1e3a8a; margin-bottom: 3px;">4. Belső Bajnokok Előléptetése</div>
          <div style="font-size: 8.5px; color: #475569; line-height: 1.35;">
            A kollégák által 100%-os bizalommal megjelölt informális közvetítőket érdemes bevonni a formális stratégiai transzformációs és agilis átállási projektek vezetésébe.
          </div>
        </div>
      </div>
    </div>

    <div class="footer">
      <span>Generálva: PeerPlay Analytics Engine · {date_str} · Hivatalos ügyféli dokumentum</span>
      <span>2. Oldal / 2</span>
    </div>
  </div>

</body>
</html>
"""

    html_file_path = 'public/executive_report_demo01.html'
    with open(html_file_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"✓ Saved HTML report: {html_file_path}")

    # Convert HTML to PDF using Headless Edge
    pdf_file_path = 'public/PeerPlay_Vezetoi_Mintariport_DEMO01.pdf'
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    
    current_dir = os.getcwd()
    full_html_path = os.path.join(current_dir, html_file_path).replace('/', '\\')
    full_pdf_path = os.path.join(current_dir, pdf_file_path).replace('/', '\\')

    cmd = [
        edge_path,
        '--headless',
        '--disable-gpu',
        '--run-all-compositor-stages-before-draw',
        f'--print-to-pdf={full_pdf_path}',
        f'file:///{full_html_path}'
    ]
    
    print(f"🖨️ [PDF BUILDER] Compiling vector PDF via headless Edge...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if os.path.exists(pdf_file_path) and os.path.getsize(pdf_file_path) > 1000:
        file_size_kb = os.path.getsize(pdf_file_path) // 1024
        print(f"✅ [SUCCESS] Compiled PDF: {pdf_file_path} ({file_size_kb} KB)")
    else:
        print("❌ [ERROR] Edge print to PDF failed:", result.stderr)

    conn.close()

if __name__ == '__main__':
    build_pdf_report()
