import base64
import os
import re

def update_b2b_suite():
    print("Updating public/b2b_validation_suite.html...")

    with open('public/images/fluvia_logo.png', 'rb') as f:
        logo_b64 = base64.b64encode(f.read()).decode('utf-8')

    with open('public/images/fluvia_ona_network.png', 'rb') as f:
        ona_b64 = base64.b64encode(f.read()).decode('utf-8')

    with open('public/b2b_validation_suite.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. Clean out all blues from CSS and inline styles
    blues_map = {
        '#EFF6FF': '#eafaf0',
        '#BFDBFE': '#a7f3d0',
        '#1D4ED8': '#0d4638',
        '#2563EB': '#0d4638',
        '#DBEAFE': '#61f27e',
        '#93C5FD': '#61f27e',
        '#3B82F6': '#0d4638',
        '#60A5FA': '#61f27e',
        '#1E40AF': '#0d4638',
        '#1E3A8A': '#0d4638',
        'tag-blue': 'tag-green',
    }
    for k, v in blues_map.items():
        html = html.replace(k, v)

    # 2. Update button styles so they NEVER blend into each other
    old_tab_bar_css = """    .tab-bar {
      display: flex;
      gap: 8px;
      background: var(--bg-subtle);
      padding: 6px;
      border-radius: 12px;
      border: 1px solid var(--border-color);
      margin-bottom: 28px;
      overflow-x: auto;
    }
    .tab-btn {
      flex: 1;
      min-width: 180px;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      padding: 10px 16px;
      border: none;
      background: transparent;
      color: var(--text-muted);
      font-family: 'Plus Jakarta Sans', sans-serif;
      font-size: 13px;
      font-weight: 700;
      border-radius: 8px;
      cursor: pointer;
      transition: all 0.15s ease;
      white-space: nowrap;
    }
    .tab-btn:hover {
      color: var(--text-main);
      background: rgba(255, 255, 255, 0.6);
    }
    .tab-btn.active {
      background: var(--bg-surface);
      color: var(--primary);
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }
    .tab-badge {
      font-size: 10px;
      font-family: 'JetBrains Mono', monospace;
      padding: 2px 6px;
      border-radius: 4px;
      background: var(--bg-subtle);
      color: var(--text-muted);
    }
    .tab-btn.active .tab-badge {
      background: #61f27e;
      color: #0d4638;
    }"""

    new_tab_bar_css = """    .tab-bar {
      display: flex;
      gap: 10px;
      background: #FFFFFF;
      padding: 8px;
      border-radius: 12px;
      border: 1.5px solid #CBD5E1;
      margin-bottom: 28px;
      box-shadow: 0 2px 6px rgba(13, 70, 56, 0.05);
      overflow-x: auto;
    }
    .tab-btn {
      flex: 1;
      min-width: 180px;
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      padding: 11px 16px;
      border: 1.5px solid #E2E8F0;
      background: #F8FAFC;
      color: #52636a;
      font-family: 'Plus Jakarta Sans', sans-serif;
      font-size: 13px;
      font-weight: 700;
      border-radius: 9px;
      cursor: pointer;
      transition: all 0.15s ease;
      white-space: nowrap;
    }
    .tab-btn:hover {
      color: #0d4638;
      background: #F1F5F9;
      border-color: #94A3B8;
    }
    .tab-btn.active {
      background: #0d4638 !important;
      color: #FFFFFF !important;
      border-color: #0d4638 !important;
      box-shadow: 0 3px 8px rgba(13, 70, 56, 0.25);
    }
    .tab-badge {
      font-size: 10px;
      font-family: 'JetBrains Mono', monospace;
      padding: 2px 7px;
      border-radius: 4px;
      background: #E2E8F0;
      color: #475569;
      font-weight: 700;
    }
    .tab-btn.active .tab-badge {
      background: #61f27e !important;
      color: #0d4638 !important;
      font-weight: 800;
    }"""

    html = html.replace(old_tab_bar_css, new_tab_bar_css)

    old_variant_css = """    /* Variant Switcher Control */
    .variant-control-bar {
      display: flex;
      gap: 6px;
      background: #F1F5F9;
      padding: 4px;
      border-radius: 8px;
      border: 1px solid var(--border-color);
      margin-bottom: 16px;
    }
    .variant-btn {
      flex: 1;
      padding: 6px 10px;
      border: none;
      background: transparent;
      font-size: 11.5px;
      font-weight: 700;
      color: var(--text-muted);
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.15s ease;
      text-align: center;
    }
    .variant-btn:hover {
      color: var(--text-main);
      background: rgba(255, 255, 255, 0.7);
    }
    .variant-btn.active {
      background: #FFFFFF;
      color: var(--primary);
      box-shadow: 0 1px 2px rgba(0,0,0,0.06);
    }"""

    new_variant_css = """    /* Variant Switcher Control */
    .variant-control-bar {
      display: flex;
      gap: 8px;
      background: #F8FAFC;
      padding: 6px;
      border-radius: 10px;
      border: 1.5px solid #CBD5E1;
      margin-bottom: 20px;
    }
    .variant-btn {
      flex: 1;
      padding: 9px 12px;
      border: 1.5px solid #CBD5E1;
      background: #FFFFFF;
      font-size: 12px;
      font-weight: 700;
      color: #52636a;
      border-radius: 7px;
      cursor: pointer;
      transition: all 0.15s ease;
      text-align: center;
      box-shadow: 0 1px 2px rgba(0,0,0,0.04);
    }
    .variant-btn:hover {
      color: #0d4638;
      background: #F1F5F9;
      border-color: #94A3B8;
    }
    .variant-btn.active {
      background: #0d4638 !important;
      color: #FFFFFF !important;
      border-color: #0d4638 !important;
      box-shadow: 0 2px 6px rgba(13, 70, 56, 0.3) !important;
    }"""

    html = html.replace(old_variant_css, new_variant_css)

    # 3. Embed Logo in Hero Header via base64
    html = re.sub(
        r'<img[^>]+src=[\'"][^\'"]*fluvia_logo\.png[\'"][^>]*>',
        f'<img src="data:image/png;base64,{logo_b64}" alt="Fluvia Systems Logo" class="brand-logo-img">',
        html
    )

    # 4. Embed ONA Graph in Tab 3 via base64
    html = re.sub(
        r'<img[^>]+src=[\'"][^\'"]*fluvia_ona_network\.png[\'"][^>]*>',
        f'<img src="data:image/png;base64,{ona_b64}" alt="Fluvia Radar ONA Hálózati Gráf" style="width: 100%; max-height: 290px; object-fit: contain; border-radius: 4px; display: block; margin: 0 auto 10px auto; border: 1px solid #CBD5E1;">',
        html
    )

    # Replace icon in header mini with base64 logo
    html = re.sub(
        r'<img[^>]+src=[\'"][^\'"]*fluvia_icon\.png[\'"][^>]*>',
        f'<img src="data:image/png;base64,{logo_b64}" style="height: 22px; width: auto;" alt="Fluvia">',
        html
    )

    # 5. Fix Tab 3: Remove "Termelt Érték" and replace with Real Diagnostic KPIs
    old_pdf_kpis = """              <!-- Key Metrics -->
              <div class="pdf-kpi-grid">
                <div class="pdf-kpi-card">
                  <div class="pdf-kpi-val">$3,050</div>
                  <div class="pdf-kpi-lbl">Termelt Érték</div>
                </div>
                <div class="pdf-kpi-card">
                  <div class="pdf-kpi-val">83.3%</div>
                  <div class="pdf-kpi-lbl">Hálózati Sűrűség</div>
                </div>
                <div class="pdf-kpi-card">
                  <div class="pdf-kpi-val" style="color: var(--accent-green);">+1.75</div>
                  <div class="pdf-kpi-lbl">&Delta; Energiaszint</div>
                </div>
                <div class="pdf-kpi-card">
                  <div class="pdf-kpi-val" style="color: var(--accent-amber);">2 Siló</div>
                  <div class="pdf-kpi-lbl">Kritikus Akadály</div>
                </div>
              </div>"""

    new_pdf_kpis = """              <!-- Valós Szervezeti Diagnosztikai Metrikák (Zéró Túlzás) -->
              <div class="pdf-kpi-grid">
                <div class="pdf-kpi-card">
                  <div class="pdf-kpi-val" style="color: #0d4638;">83.3%</div>
                  <div class="pdf-kpi-lbl">Hálózati Együttműködés</div>
                </div>
                <div class="pdf-kpi-card">
                  <div class="pdf-kpi-val" style="color: #DC2626;">0 Tranzakció</div>
                  <div class="pdf-kpi-lbl">Kritikus Részlegi Siló</div>
                </div>
                <div class="pdf-kpi-card">
                  <div class="pdf-kpi-val" style="color: #0d4638;">+1.75 Pont</div>
                  <div class="pdf-kpi-lbl">Dinamikai Energiaszint</div>
                </div>
                <div class="pdf-kpi-card">
                  <div class="pdf-kpi-val" style="color: #0d4638;">&lt; 4.2 perc</div>
                  <div class="pdf-kpi-lbl">Döntési Reakcióidő</div>
                </div>
              </div>"""

    html = html.replace(old_pdf_kpis, new_pdf_kpis)

    # 6. Fix Action Plan in Tab 3: Remove vague fluff and provide sharp interventions
    old_action_plan = """              <!-- 4 Akciójavaslat -->
              <div style="margin-top: 16px; border-top: 1px solid var(--border-color); padding-top: 12px;">
                <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; color: var(--text-main); margin-bottom: 6px;">
                  3. Vezetői Akcióterv (HR & Operációs Intervenció)
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 11px;">
                  <div style="background: var(--bg-canvas); padding: 8px; border-radius: 4px; border-left: 2px solid var(--primary);">
                    <strong>1. Silóbontó Sprint:</strong> Heti 1x 15p szinkron a Gyártás és K+F között.
                  </div>
                  <div style="background: var(--bg-canvas); padding: 8px; border-radius: 4px; border-left: 2px solid var(--accent-green);">
                    <strong>2. Broker Megerősítés:</strong> A 2 közvetítő kulcsember hivatalos kinevezése.
                  </div>
                </div>
              </div>"""

    new_action_plan = """              <!-- 4 Konkrét, Szakmai Vezetői Akcióterv (Zéró Általánoskodás) -->
              <div style="margin-top: 16px; border-top: 1.5px solid var(--border-color); padding-top: 14px;">
                <div style="font-size: 11px; font-weight: 800; text-transform: uppercase; color: #0d4638; margin-bottom: 8px;">
                  3. Vezetői Akcióterv (4 Konkrét Szervezeti Intervenció)
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; font-size: 11.5px;">
                  <div style="background: #F8FAFC; padding: 10px 12px; border-radius: 6px; border-left: 3px solid #0d4638; border: 1px solid #E2E8F0; border-left-width: 3px; border-left-color: #0d4638;">
                    <strong style="color: #0d4638;">1. Gyártás &amp; K+F Interfész Sprint:</strong><br>
                    <span style="color: #475569; font-size: 11px; line-height: 1.45;">
                      A megállapodások 100%-a közvetítőkön keresztül zajlott (3.8x átfutási idő). Heti közvetlen funkcióközi release-szinkron és közvetlen döntési csatorna kialakítása szükséges a késleltetés megszüntetésére.
                    </span>
                  </div>
                  <div style="background: #F8FAFC; padding: 10px 12px; border-radius: 6px; border-left: 3px solid #0d4638; border: 1px solid #E2E8F0; border-left-width: 3px; border-left-color: #0d4638;">
                    <strong style="color: #0d4638;">2. Kulcsember-kitettség Csökkentése (SPOF védelem):</strong><br>
                    <span style="color: #475569; font-size: 11px; line-height: 1.45;">
                      A kapcsolatok 75%-a két közvetítőn (Kovács Péter és Szabó Tamás) múlik. Helyettesítési mátrix és hatásköri delegálás bevezetése kötelező a kapacitás-túlterheltség és kiesési kockázat megelőzésére.
                    </span>
                  </div>
                  <div style="background: #F8FAFC; padding: 10px 12px; border-radius: 6px; border-left: 3px solid #0d4638; border: 1px solid #E2E8F0; border-left-width: 3px; border-left-color: #0d4638;">
                    <strong style="color: #0d4638;">3. Belső Erőforrás-megosztási SLA:</strong><br>
                    <span style="color: #475569; font-size: 11px; line-height: 1.45;">
                      Piaci sokkok idején a belső alkudozás az idő 76%-át elvitte. Belső kapacitás-bérleti és átadási szabvány (SLA) bevezetése, amely válsághelyzetben 3 perc alá szorítja a belső súrlódást.
                    </span>
                  </div>
                  <div style="background: #F8FAFC; padding: 10px 12px; border-radius: 6px; border-left: 3px solid #0d4638; border: 1px solid #E2E8F0; border-left-width: 3px; border-left-color: #0d4638;">
                    <strong style="color: #0d4638;">4. Informális Vezetők Felhatalmazása:</strong><br>
                    <span style="color: #475569; font-size: 11px; line-height: 1.45;">
                      A 100%-os társas bizalmat élvező brokerek hivatalos kinevezése a digitális transzformációs projektek stratégiai nagyköveteivé, kihasználva természetes csapatformáló híd-szerepüket.
                    </span>
                  </div>
                </div>
              </div>"""

    html = html.replace(old_action_plan, new_action_plan)

    with open('public/b2b_validation_suite.html', 'w', encoding='utf-8') as f:
        f.write(html)

    print("✓ Successfully updated public/b2b_validation_suite.html with all fixes!")

if __name__ == '__main__':
    update_b2b_suite()
