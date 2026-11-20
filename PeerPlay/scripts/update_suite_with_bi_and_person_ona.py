import base64
import os
import re

def update_suite():
    print("Updating public/b2b_validation_suite.html with BI dashboard link and person-level ONA...")

    with open('public/images/fluvia_ona_network.png', 'rb') as f:
        ona_b64 = base64.b64encode(f.read()).decode('utf-8')

    with open('public/b2b_validation_suite.html', 'r', encoding='utf-8') as f:
        html = f.read()

    # 1. Update Tab 3 navigation button label
    html = html.replace(
        '<span>3. Fluvia Radar PDF Riport</span>',
        '<span>3. BI Dashboard &amp; PDF Riport</span>'
    )

    # 2. In Tab 3 header, add the BI Dashboard Launch Button next to PDF download
    old_pdf_header = """          <div class="artifact-header">
            <div class="artifact-title-box">
              <span class="artifact-title">Fluvia Radar Vezetői Diagnosztikai Riport (DEMO01 PDF)</span>
              <span class="artifact-tag tag-green">A Megdönthetetlen Bizonyíték</span>
            </div>
            <a href="/Fluvia_Radar_Vezetoi_Mintariport_DEMO01.pdf" target="_blank" class="copy-btn">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
              Eredeti PDF Megnyitása
            </a>
          </div>"""

    new_pdf_header = """          <div class="artifact-header">
            <div class="artifact-title-box">
              <span class="artifact-title">Fluvia Radar Vezetői BI Dashboard &amp; Diagnosztikai Riport</span>
              <span class="artifact-tag tag-green">Interaktív + PDF Bizonyíték</span>
            </div>
            <div style="display: flex; gap: 8px;">
              <a href="fluvia_radar_bi.html" target="_blank" class="copy-btn" style="background: #0d4638; color: #61f27e; border-color: #0d4638; text-decoration: none;">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><polygon points="10 8 16 12 10 16 10 8"></polygon></svg>
                Élő BI Dashboard Megnyitása
              </a>
              <a href="Fluvia_Radar_Vezetoi_Mintariport_DEMO01.pdf" target="_blank" class="copy-btn" style="text-decoration: none;">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
                PDF Letöltése
              </a>
            </div>
          </div>"""

    html = html.replace(old_pdf_header, new_pdf_header)

    # 3. Add BI Dashboard Promotion Banner above the PDF preview box
    bi_promo_banner = """            <!-- BI Dashboard Quick Launcher Banner -->
            <div style="background: linear-gradient(135deg, #0d4638 0%, #175445 100%); color: #FFFFFF; border-radius: 8px; padding: 14px 18px; margin-bottom: 16px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 8px rgba(13, 70, 56, 0.15);">
              <div>
                <div style="font-size: 13.5px; font-weight: 800; color: #FFFFFF; display: flex; align-items: center; gap: 8px;">
                  <span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #61f27e;"></span>
                  Új: Interaktív Vezetői BI Dashboard (Kattintás- és Figyelemkövetéssel)
                </div>
                <div style="font-size: 11.5px; color: #cbd5e1; margin-top: 3px;">
                  PDF helyett küldhető modern BI felület: a vezérigazgató kattintásait, szűréseit és nézettartamát valós időben méri a beépített telemetria.
                </div>
              </div>
              <a href="fluvia_radar_bi.html" target="_blank" style="background: #61f27e; color: #0d4638; padding: 8px 16px; border-radius: 6px; font-size: 12px; font-weight: 800; text-decoration: none; white-space: nowrap; transition: all 0.15s ease;">
                BI Felület Megnyitása &rarr;
              </a>
            </div>"""

    html = html.replace('<div class="artifact-body">\n            <!-- Simulated PDF Page 1 -->', f'<div class="artifact-body">\n{bi_promo_banner}\n            <!-- Simulated PDF Page 1 -->')

    # 4. In Tab 3 ONA description, emphasize person-level nodes
    html = html.replace(
        '2. Szociometriai ONA Hálózati Térkép',
        '2. Ember Szintű Szociometriai ONA Hálózati Gráf'
    )
    html = html.replace(
        'A gráf csomópontjai a résztvevőket jelölik a valós vállalati részlegük színei szerint (Kék: Pénzügy, Zöld: Gyártás, Lila: K+F, Narancs: Értékesítés).',
        'A gráf csomópontjai a 8 konkrét résztvevő személyt jelölik (Kovács Péter, Szabó Tamás, Horváth Balázs, Kiss Gergely stb.) a valós részlegük színeivel. A csomópont mérete a közvetítői súlyt (Betweenness centrality) mutatja.'
    )

    # 5. In Tab 3 Sidebar, add the Strategy on why BI dashboard beats static PDF
    old_reasoning_pdf = """          <div class="reasoning-card">
            <span class="reasoning-badge">Riport Szabály #1</span>
            <div class="reasoning-title">Miért nem elég egy szöveges összefoglaló?</div>
            <div class="reasoning-desc">
              Egy CEO vagy CHRO nem olvas el 20 oldalas tanulmányokat. A <strong>2 oldalas, feszes vektoros PDF formátum</strong> azonnal jelzi, hogy a módszertan készen van, kiforrott, és a diagnózis a workshop zárása után 10 perccel a vezetőség asztalán lehet.
            </div>
          </div>"""

    new_reasoning_pdf = """          <div class="reasoning-card" style="border-left: 3px solid #61f27e;">
            <span class="reasoning-badge" style="color: #0d4638;">Outreach Forradalom</span>
            <div class="reasoning-title">Miért jobb a BI Dashboard a sima PDF-nél?</div>
            <div class="reasoning-desc">
              A PDF egy <strong>fekete doboz</strong>: ha elküldöd, sosem tudod meg, megnyitotta-e a vezérigazgató, átfutotta-e, vagy azonnal törölte.
              <br><br>
              A <strong>Fluvia Radar BI Dashboard link</strong> ezzel szemben telemetriával működik:
              <br>
              • <strong>Másodpercre pontos figyelemidő:</strong> Látod, mennyi időt töltött rajta.
              <br>
              • <strong>Kattintás-izoláció:</strong> Látod, ha rákattintott Szabó Tamásra vagy a piros Siló gombra.
              <br>
              • <strong>Modern Tech Érzet:</strong> Nem egy statikus papírlap, hanem egy Datadog/Linear szintű prémium diagnosztikai platform.
            </div>
            <div class="reasoning-metric" style="color: #0d4638; background: #eafaf0;">
              <span class="metric-dot" style="background: #61f27e;"></span> Kattintás &amp; Telemetria: 100% Mérhető
            </div>
          </div>

          <div class="reasoning-card">
            <span class="reasoning-badge">Riport Szabály #1</span>
            <div class="reasoning-title">A 2 Oldalas Feszes PDF Szerepe</div>
            <div class="reasoning-desc">
              Ha a vezető letölthető, offline anyagot kér a belső vezetőségi ülésre, a <strong>2 oldalas, feszes vektoros PDF formátum</strong> azonnal kinyomtatható, bemutatható formában adja át az ONA diagnózist.
            </div>
          </div>"""

    html = html.replace(old_reasoning_pdf, new_reasoning_pdf)

    # 6. In Tab 1 (Email variants), update CTA to offer both or the BI Dashboard
    html = html.replace(
        "Átküldöm a 2 oldalas vezetői mintariportot, hogy lásd a gyakorlatban. Mehet?",
        "Átküldöm a 2 oldalas mintariportot és a kattintható BI dashboard linkjét, hogy lásd a gyakorlatban. Mehet?"
    )

    with open('public/b2b_validation_suite.html', 'w', encoding='utf-8') as f:
        f.write(html)

    print("✓ Successfully enhanced public/b2b_validation_suite.html!")

if __name__ == '__main__':
    update_suite()
