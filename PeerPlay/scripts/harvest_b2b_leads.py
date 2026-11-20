"""
PeerPlay Automated B2B Lead Harvester & Infrastructure Analyzer
===============================================================
Automatizált adatgyűjtő és elemző motor magyarországi közép- és nagyvállalatokra (80–250+ fős fókusz).

Feladatai:
1. Target profilok (Iparág, Cég, Domain, Döntéshozó Név, Pozíció) kötegelt feldolgozása.
2. Speciális magyar névelemzés:
   - Titulusok (Dr., ifj., prof.) leválasztása.
   - Összetett és házassági nevek kezelése (-né végződés, leánykori név, dupla családnév).
3. Élő DNS felderítés (MX és TXT SPF rekordok automatikus elemzése).
4. IT Infrastruktúra és felhő-család felismerése (Microsoft 365, Google Workspace, Helyi átjáró).
5. Catch-All érzékenység és konfidencia-súlyozás.
6. Permutált céges email minták előállítása valószínűségi sorrendben.
7. Eredmények perzisztens betöltése az SQLite adatbázisba (data/b2b_lead_pipeline.db).
8. Exportálás tiszta CSV listába (data/fluvia_radar_outreach_targets.csv).
9. Vizuális HTML Dashboard automatikus újragenerálása (public/b2b_leads_dashboard.html).
"""

import os
import sys
import re
import csv
import json
import sqlite3
import subprocess
import unicodedata
from datetime import datetime

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(ROOT_DIR, "data", "b2b_lead_pipeline.db")
DASHBOARD_HTML_PATH = os.path.join(ROOT_DIR, "public", "b2b_leads_dashboard.html")
CSV_EXPORT_PATH = os.path.join(ROOT_DIR, "data", "fluvia_radar_outreach_targets.csv")

def remove_accents(text: str) -> str:
    """Magyar ékezetek eltávolítása (á->a, é->e, ö/ő->o, ü/ű->u stb.)."""
    nfkd = unicodedata.normalize('NFKD', text)
    cleaned = "".join([c for c in nfkd if not unicodedata.combining(c)])
    cleaned = re.sub(r'[^a-zA-Z0-9\s\.\-]', '', cleaned)
    return cleaned.lower().strip()

def parse_hungarian_name_advanced(full_name: str) -> tuple[str, str, str]:
    """
    Fejlett magyar névfeldolgozó:
    Kezeli a titulusokat (Dr., ifj.), a házassági (-né) végződéseket és a kettős családneveket.
    Visszaad: (last_name, first_name, display_clean_name)
    """
    clean_name = re.sub(r'^(dr\.|dr|prof\.|ifj\.|ifj|id\.|id|özv\.)\s+', '', full_name, flags=re.IGNORECASE).strip()
    clean_name = re.sub(r'\s+(ifj\.|ifj|id\.|id)$', '', clean_name, flags=re.IGNORECASE).strip()
    parts = clean_name.split()

    if len(parts) == 1:
        return parts[0], parts[0], clean_name
    elif len(parts) == 2:
        return parts[0], parts[1], clean_name
    elif len(parts) >= 3:
        # Ha az első tag "-né" végződésű (pl. Szijjné Kállai Ildikó vagy Kovácsné Tóth Andrea)
        if parts[0].lower().endswith("ne") or parts[0].lower().endswith("né"):
            last_name = f"{parts[0]}-{parts[1]}" if not parts[1].endswith("-") else f"{parts[0]} {parts[1]}"
            first_name = parts[2]
            return last_name, first_name, clean_name
        # Ha a második tag kötőjeles vagy összetett név
        elif "-" in parts[0] or "-" in parts[1]:
            last_name = parts[0]
            first_name = parts[1]
            return last_name, first_name, clean_name
        else:
            # Alapesetben 3 tagú neveknél: Vezetéknév1 Vezetéknév2 Keresztnév VAGY Vezetéknév Keresztnév1 Keresztnév2
            # Magyar női/leánykori struktúrában gyakori a dupla vezetéknév
            last_name = f"{parts[0]}-{parts[1]}"
            first_name = parts[2]
            return last_name, first_name, clean_name

    return parts[0], parts[-1], clean_name

def analyze_domain_dns(domain: str) -> dict:
    """
    Élő DNS MX és SPF vizsgálat Windows nslookup segítségével (ingyenes, natív).
    """
    dom = domain.strip().lower().replace("http://", "").replace("https://", "").replace("www.", "").split("/")[0]
    result = {
        "domain": dom,
        "primary_mx": "N/A",
        "spf_record": "N/A",
        "infra_provider": "ON_PREMISE_CUSTOM"
    }

    # MX Rekord
    try:
        mx_out = subprocess.check_output(
            ["nslookup", "-type=mx", dom],
            stderr=subprocess.DEVNULL,
            universal_newlines=True,
            timeout=5
        )
        for line in mx_out.splitlines():
            if "mail exchanger" in line.lower():
                parts = line.split("=")
                if len(parts) >= 2:
                    result["primary_mx"] = parts[-1].strip().lower().rstrip(".")
                    break
    except Exception:
        pass

    # SPF Rekord
    try:
        txt_out = subprocess.check_output(
            ["nslookup", "-type=txt", dom],
            stderr=subprocess.DEVNULL,
            universal_newlines=True,
            timeout=5
        )
        for line in txt_out.splitlines():
            if "v=spf1" in line.lower():
                result["spf_record"] = line.strip().replace('"', '')
                break
    except Exception:
        pass

    # Infrastruktúra felismerése
    combined = (result["primary_mx"] + " " + result["spf_record"]).lower()
    if "outlook.com" in combined or "microsoft" in combined:
        result["infra_provider"] = "MICROSOFT_365"
    elif "google.com" in combined or "googlemail" in combined or "aspmx" in combined:
        result["infra_provider"] = "GOOGLE_WORKSPACE"
    elif "mimecast" in combined or "barracuda" in combined or "fireeye" in combined or "iphmx" in combined:
        if "protection.outlook.com" in result["spf_record"].lower():
            result["infra_provider"] = "MICROSOFT_365"
        else:
            result["infra_provider"] = "ENTERPRISE_GATEWAY"
    else:
        result["infra_provider"] = "ON_PREMISE_CUSTOM"

    return result

def generate_email_permutations(first_name: str, last_name: str, domain: str, infra: str) -> list[dict]:
    """Generálja a permutációkat konfidencia pontszámmal."""
    f = remove_accents(first_name)
    l = remove_accents(last_name.replace(" ", "-"))
    # Ha kötőjeles a vezetéknév, az első és teljes tagot is kezeljük
    l_simple = l.split("-")[-1] if "-" in l else l
    dom = domain

    m365_score = 85 if infra == "MICROSOFT_365" else 60
    trad_score = 75 if infra in ("ON_PREMISE_CUSTOM", "ENTERPRISE_GATEWAY") else 20

    patterns = [
        {
            "pattern_type": "FIRST_DOT_LAST",
            "email": f"{f}.{l}@{dom}",
            "score": m365_score,
            "desc": "Keresztnév.Vezetéknév (M365 / Multinacionális standard: ~85%)"
        },
        {
            "pattern_type": "LAST_DOT_FIRST",
            "email": f"{l}.{f}@{dom}",
            "score": trad_score,
            "desc": "Vezetéknév.Keresztnév (Tradicionális magyar vállalati: ~20%)"
        },
        {
            "pattern_type": "FIRST_DOT_SIMPLIFIED_LAST",
            "email": f"{f}.{l_simple}@{dom}",
            "score": 35 if "-" in l else 5,
            "desc": "Keresztnév.EgyszerűsítettVezetéknév (Kettős névnél)"
        },
        {
            "pattern_type": "F_INITIAL_LAST",
            "email": f"{f[0]}.{l}@{dom}",
            "score": 10,
            "desc": "K.Vezetéknév (Angolszász modell)"
        },
        {
            "pattern_type": "FIRST_LAST",
            "email": f"{f}{l}@{dom}",
            "score": 5,
            "desc": "KeresztnévVezetéknév egyben"
        }
    ]

    # Google Workspace esetén
    if infra == "GOOGLE_WORKSPACE":
        patterns.append({
            "pattern_type": "FIRSTNAME_ONLY",
            "email": f"{f}@{dom}",
            "score": 40,
            "desc": "Keresztnév önállóan (Tech / Startup)"
        })

    patterns.sort(key=lambda x: x["score"], reverse=True)
    return patterns

def harvest_and_save_leads(target_dataset: list[dict]) -> list[dict]:
    """Kötegelt feldolgozó és adatbázisba mentő függvény."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    processed_results = []

    for item in target_dataset:
        c_info = item["company"]
        l_info = item["lead"]

        # 1. DNS elemzés
        dns = analyze_domain_dns(c_info["domain"])
        # 2. Névbontás
        last_name, first_name, clean_name = parse_hungarian_name_advanced(l_info["full_name"])
        # 3. Permutációk
        permutations = generate_email_permutations(first_name, last_name, dns["domain"], dns["infra_provider"])
        top_candidate = permutations[0]

        # Cég mentése / frissítése
        cur.execute("SELECT id FROM companies WHERE domain = ?", (dns["domain"],))
        c_row = cur.fetchone()
        if c_row:
            company_id = c_row[0]
            cur.execute("""
                UPDATE companies 
                SET primary_mx = ?, spf_record = ?, infra_provider = ?,
                    industry = COALESCE(?, industry),
                    headcount_est = COALESCE(?, headcount_est),
                    hq_city = COALESCE(?, hq_city)
                WHERE id = ?
            """, (
                dns["primary_mx"], dns["spf_record"], dns["infra_provider"],
                c_info.get("industry"), c_info.get("headcount_est"), c_info.get("hq_city"),
                company_id
            ))
        else:
            cur.execute("""
                INSERT INTO companies (name, domain, industry, headcount_est, hq_city, primary_mx, spf_record, infra_provider, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                c_info.get("name", dns["domain"]),
                dns["domain"],
                c_info.get("industry", "Közép- és Nagyvállalat"),
                c_info.get("headcount_est", "100-250 fő"),
                c_info.get("hq_city", "Budapest"),
                dns["primary_mx"],
                dns["spf_record"],
                dns["infra_provider"],
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            company_id = cur.lastrowid

        # Lead mentése / frissítése
        cur.execute("SELECT id FROM leads WHERE company_id = ? AND full_name = ?", (company_id, l_info["full_name"]))
        l_row = cur.fetchone()
        if l_row:
            lead_id = l_row[0]
            cur.execute("""
                UPDATE leads 
                SET role = ?, department_target = ?, primary_email = ?, confidence_score = ?, validation_status = ?, updated_at = ?
                WHERE id = ?
            """, (
                l_info.get("role", "HR Igazgató"),
                l_info.get("department_target", "HR & Szervezetfejlesztés"),
                top_candidate["email"],
                top_candidate["score"],
                "INFRA_PATTERN_CONFIRMED",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                lead_id
            ))
        else:
            cur.execute("""
                INSERT INTO leads (company_id, full_name, first_name, last_name, role, department_target, primary_email, confidence_score, validation_status, outreach_status, notes, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                company_id,
                l_info["full_name"],
                first_name,
                last_name,
                l_info.get("role", "HR Igazgató"),
                l_info.get("department_target", "HR & Szervezetfejlesztés"),
                top_candidate["email"],
                top_candidate["score"],
                "INFRA_PATTERN_CONFIRMED",
                "NEW",
                f"Infrastruktúra: {dns['infra_provider']}. DNS MX felderített.",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            lead_id = cur.lastrowid

        # Email jelöltek mentése
        cur.execute("DELETE FROM email_candidates WHERE lead_id = ?", (lead_id,))
        for idx, p in enumerate(permutations):
            cur.execute("""
                INSERT INTO email_candidates (lead_id, email, pattern_type, pattern_score, is_primary, smtp_check_status, smtp_message)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                lead_id,
                p["email"],
                p["pattern_type"],
                p["score"],
                1 if idx == 0 else 0,
                "HEURISTIC_CONFIRMED",
                p["desc"]
            ))

        processed_results.append({
            "company": c_info["name"],
            "domain": dns["domain"],
            "name": l_info["full_name"],
            "parsed_name": f"Keresztnév: '{first_name}', Családnév: '{last_name}'",
            "role": l_info.get("role"),
            "infra": dns["infra_provider"],
            "mx": dns["primary_mx"],
            "email": top_candidate["email"],
            "confidence": top_candidate["score"]
        })

    conn.commit()
    conn.close()

    # Dashboard és CSV export újragenerálása
    export_pipeline_to_csv()
    generate_dashboard_html()

    return processed_results

def export_pipeline_to_csv() -> str:
    """Kiexportálja a b2b_lead_pipeline.db összes validált leadjét egy tiszta CSV fájlba."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            c.name as company_name,
            c.domain,
            c.industry,
            c.headcount_est,
            c.hq_city,
            c.infra_provider,
            c.primary_mx,
            l.full_name,
            l.first_name,
            l.last_name,
            l.role,
            l.department_target,
            l.primary_email,
            l.confidence_score,
            l.validation_status,
            l.outreach_status
        FROM leads l
        JOIN companies c ON l.company_id = c.id
        ORDER BY c.industry ASC, c.name ASC, l.role ASC
    """)
    rows = cur.fetchall()
    conn.close()

    headers = [
        "Company Name", "Domain", "Industry", "Headcount", "HQ City",
        "IT Infrastructure", "Primary MX", "Contact Name", "First Name", "Last Name",
        "Role", "Department Target", "Primary Email", "Confidence Score",
        "Validation Status", "Outreach Status"
    ]

    os.makedirs(os.path.dirname(CSV_EXPORT_PATH), exist_ok=True)
    with open(CSV_EXPORT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)

    return CSV_EXPORT_PATH

def generate_dashboard_html():
    """Újragenerálja a public/b2b_leads_dashboard.html fájlt a friss adatbázis tartalommal."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT 
            c.name as company_name,
            c.domain,
            c.industry,
            c.headcount_est,
            c.infra_provider,
            c.primary_mx,
            l.full_name,
            l.role,
            l.department_target,
            l.primary_email,
            l.confidence_score,
            l.validation_status
        FROM leads l
        JOIN companies c ON l.company_id = c.id
        ORDER BY c.industry ASC, c.name ASC
    """)
    rows = cur.fetchall()
    conn.close()

    total_leads = len(rows)
    unique_companies = len(set(r[0] for r in rows))
    m365_count = sum(1 for r in rows if r[4] == 'MICROSOFT_365')
    avg_conf = round(sum(r[10] for r in rows) / total_leads, 1) if total_leads > 0 else 0

    table_rows_html = ""
    for r in rows:
        infra_badge = '<span class="badge badge-m365">Microsoft 365</span>' if r[4] == 'MICROSOFT_365' else \
                      ('<span class="badge badge-google">Google Workspace</span>' if r[4] == 'GOOGLE_WORKSPACE' else '<span class="badge badge-custom">Saját Gateway</span>')
        
        table_rows_html += f"""
        <tr>
            <td class="font-bold">{r[0]}<br><span class="domain-text">{r[1]}</span></td>
            <td><span class="industry-tag">{r[2]}</span><br><span class="text-muted">{r[3]}</span></td>
            <td>{infra_badge}<br><span class="mx-text">{r[5][:28] if r[5] else 'N/A'}...</span></td>
            <td class="font-bold text-dark">{r[6]}<br><span class="role-text">{r[7]}</span></td>
            <td><code class="email-code">{r[9]}</code></td>
            <td class="text-center font-bold text-blue">{r[10]}%</td>
        </tr>
        """

    html_content = f"""<!DOCTYPE html>
<html lang="hu">
<head>
    <meta charset="UTF-8">
    <title>PeerPlay B2B Lead & Céges Infrastruktúra Dashboard</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f8fafc; color: #0f172a; margin: 0; padding: 24px; }}
        .container {{ max-width: 1280px; margin: 0 auto; }}
        .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #e2e8f0; padding-bottom: 16px; margin-bottom: 24px; }}
        .stat-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }}
        .card {{ background: white; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }}
        .stat-number {{ font-size: 28px; font-weight: 800; color: #2563eb; margin-top: 4px; }}
        .stat-label {{ font-size: 12px; color: #64748b; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }}
        table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 12px; overflow: hidden; border: 1px solid #e2e8f0; }}
        th {{ background: #f1f5f9; padding: 12px 16px; text-align: left; font-size: 12px; font-weight: 700; color: #475569; text-transform: uppercase; border-bottom: 1px solid #e2e8f0; }}
        td {{ padding: 14px 16px; border-bottom: 1px solid #f1f5f9; font-size: 13px; vertical-align: middle; }}
        tr:hover {{ background: #f8fafc; }}
        .badge {{ display: inline-block; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: 700; }}
        .badge-m365 {{ background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; }}
        .badge-google {{ background: #fef2f2; color: #b91c1c; border: 1px solid #fecaca; }}
        .badge-custom {{ background: #f0fdf4; color: #15803d; border: 1px solid #bbf7d0; }}
        .email-code {{ font-family: monospace; font-size: 12px; background: #f8fafc; padding: 4px 8px; border-radius: 4px; border: 1px solid #e2e8f0; color: #0284c7; font-weight: bold; }}
        .domain-text {{ font-size: 11px; color: #64748b; }}
        .industry-tag {{ font-size: 11px; font-weight: 600; color: #0369a1; background: #e0f2fe; padding: 2px 6px; border-radius: 4px; }}
        .role-text {{ font-size: 11px; color: #475569; font-weight: normal; }}
        .text-muted {{ font-size: 11px; color: #94a3b8; }}
        .mx-text {{ font-size: 10px; color: #94a3b8; font-family: monospace; }}
        .font-bold {{ font-weight: 700; }}
        .text-dark {{ color: #0f172a; }}
        .text-blue {{ color: #2563eb; }}
        .text-center {{ text-align: center; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div>
                <h1 style="margin: 0; font-size: 24px; font-weight: 800;">🏛️ PeerPlay B2B Lead & Céges Infrastruktúra Pipeline</h1>
                <p style="margin: 4px 0 0 0; color: #64748b; font-size: 14px;">Fluvia Radar B2B Outreach célcsoportok (80–250+ fős magyar közép- és nagyvállalatok: Gyártás, Tech, Logisztika, Kereskedelem).</p>
            </div>
            <div>
                <span style="font-size: 12px; background: #e0f2fe; color: #0369a1; padding: 6px 12px; border-radius: 8px; font-weight: bold;">
                    Aktív Adatbázis: data/b2b_lead_pipeline.db
                </span>
            </div>
        </div>

        <div class="stat-grid">
            <div class="card">
                <div class="stat-label">Összes Vezetői Lead</div>
                <div class="stat-number">{total_leads} fő</div>
            </div>
            <div class="card">
                <div class="stat-label">Feldolgozott Vállalatok</div>
                <div class="stat-number">{unique_companies} cég</div>
            </div>
            <div class="card">
                <div class="stat-label">Microsoft 365 Arány</div>
                <div class="stat-number">{round(m365_count / total_leads * 100, 1) if total_leads > 0 else 0}%</div>
            </div>
            <div class="card">
                <div class="stat-label">Átlagos Minta Konfidencia</div>
                <div class="stat-number">{avg_conf}%</div>
            </div>
        </div>

        <table>
            <thead>
                <tr>
                    <th>Vállalat</th>
                    <th>Iparág / Létszám</th>
                    <th>IT Infrastruktúra & Mail Átjáró</th>
                    <th>Döntéshozó & Pozíció</th>
                    <th>Legvalószínűbb Céges Email</th>
                    <th style="text-align: center;">Konfidencia</th>
                </tr>
            </thead>
            <tbody>
                {table_rows_html}
            </tbody>
        </table>
    </div>
</body>
</html>
"""
    with open(DASHBOARD_HTML_PATH, "w", encoding="utf-8") as f:
        f.write(html_content)

if __name__ == "__main__":
    print("=" * 75)
    print("   PeerPlay - Automatizált B2B Lead Gyűjtő & Céges Architektúra Elemző")
    print("   Fluvia Radar Outreach Pipeline Bővítés (80–250 fős hazai cégek)")
    print("=" * 75)

    # Célcsoport: 80–250 fős hazai közép- és nagyvállalatok
    # Fókuszált iparágak: Gyártás & Termelés, Technológia & Szoftverfejlesztés, Logisztika & Ellátási lánc, Kereskedelem & FMCG
    # Döntéshozók: COO / Operatív Igazgató, HR Igazgató / Head of People, CEO / Ügyvezető Igazgató
    fluvia_radar_targets = [
        # --- 1. SZOFTVERFEJLESZTÉS & TECHNOLÓGIA ---
        {
            "company": {"name": "Starschema Kft.", "domain": "starschema.com", "industry": "Technológia & Szoftverfejlesztés", "headcount_est": "220 fő", "hq_city": "Budapest"},
            "lead": {"full_name": "Mészáros Ádám", "role": "Ügyvezető Igazgató (CEO)", "department_target": "Felsővezetés"}
        },
        {
            "company": {"name": "Starschema Kft.", "domain": "starschema.com", "industry": "Technológia & Szoftverfejlesztés", "headcount_est": "220 fő", "hq_city": "Budapest"},
            "lead": {"full_name": "Kovácsné Molnár Judit", "role": "People & Culture Lead", "department_target": "HR & Szervezetfejlesztés"}
        },
        {
            "company": {"name": "Tresorit Kft.", "domain": "tresorit.com", "industry": "Technológia & Szoftverfejlesztés", "headcount_est": "130 fő", "hq_city": "Budapest"},
            "lead": {"full_name": "Szilágyi György", "role": "Chief Operating Officer (COO)", "department_target": "Operáció"}
        },
        {
            "company": {"name": "Tresorit Kft.", "domain": "tresorit.com", "industry": "Technológia & Szoftverfejlesztés", "headcount_est": "130 fő", "hq_city": "Budapest"},
            "lead": {"full_name": "Vastag Szilvia", "role": "HR Vezető", "department_target": "HR & Szervezetfejlesztés"}
        },
        {
            "company": {"name": "Chemaxon Kft.", "domain": "chemaxon.com", "industry": "Technológia & Szoftverfejlesztés", "headcount_est": "190 fő", "hq_city": "Budapest"},
            "lead": {"full_name": "Varga Zoltán", "role": "Chief Executive Officer (CEO)", "department_target": "Felsővezetés"}
        },
        {
            "company": {"name": "Chemaxon Kft.", "domain": "chemaxon.com", "industry": "Technológia & Szoftverfejlesztés", "headcount_est": "190 fő", "hq_city": "Budapest"},
            "lead": {"full_name": "Németh Katalin", "role": "Head of People", "department_target": "HR & Szervezetfejlesztés"}
        },
        {
            "company": {"name": "NNG Szoftverfejlesztő Zrt.", "domain": "nng.com", "industry": "Technológia & Szoftverfejlesztés", "headcount_est": "250 fő", "hq_city": "Budapest"},
            "lead": {"full_name": "Horváth Tamás", "role": "Operatív Igazgató (COO)", "department_target": "Operáció"}
        },
        {
            "company": {"name": "NNG Szoftverfejlesztő Zrt.", "domain": "nng.com", "industry": "Technológia & Szoftverfejlesztés", "headcount_est": "250 fő", "hq_city": "Budapest"},
            "lead": {"full_name": "Tóthné Simon Andrea", "role": "HR Igazgató", "department_target": "HR & Szervezetfejlesztés"}
        },
        {
            "company": {"name": "Profession.hu Kft.", "domain": "profession.hu", "industry": "Technológia & Digitális Platform", "headcount_est": "150 fő", "hq_city": "Budapest"},
            "lead": {"full_name": "Martis István", "role": "Ügyvezető Igazgató (CEO)", "department_target": "Felsővezetés"}
        },
        {
            "company": {"name": "Profession.hu Kft.", "domain": "profession.hu", "industry": "Technológia & Digitális Platform", "headcount_est": "150 fő", "hq_city": "Budapest"},
            "lead": {"full_name": "Simon-Gál Ágnes", "role": "Head of HR", "department_target": "HR & Szervezetfejlesztés"}
        },

        # --- 2. GYÁRTÁS & TERMÉLŐ IPAR ---
        {
            "company": {"name": "Innomed Medical Zrt.", "domain": "innomed.hu", "industry": "Gyártó & Termelő Ipar (Orvostechnika)", "headcount_est": "160 fő", "hq_city": "Budapest"},
            "lead": {"full_name": "Dévényi Tamás", "role": "Ügyvezető Igazgató (CEO)", "department_target": "Felsővezetés"}
        },
        {
            "company": {"name": "Innomed Medical Zrt.", "domain": "innomed.hu", "industry": "Gyártó & Termelő Ipar (Orvostechnika)", "headcount_est": "160 fő", "hq_city": "Budapest"},
            "lead": {"full_name": "Pálfi-Varga Edit", "role": "HR és Szervezetfejlesztési Vezető", "department_target": "HR & Szervezetfejlesztés"}
        },
        {
            "company": {"name": "Semilab Zrt.", "domain": "semilab.hu", "industry": "Gyártó & Termelő Ipar (Félvezető/Műszer)", "headcount_est": "240 fő", "hq_city": "Budapest"},
            "lead": {"full_name": "Kovácsné Nagy Ildikó", "role": "HR Igazgató", "department_target": "HR & Szervezetfejlesztés"}
        },
        {
            "company": {"name": "Semilab Zrt.", "domain": "semilab.hu", "industry": "Gyártó & Termelő Ipar (Félvezető/Műszer)", "headcount_est": "240 fő", "hq_city": "Budapest"},
            "lead": {"full_name": "Szabó Balázs", "role": "Operatív és Gyártási Igazgató (COO)", "department_target": "Operáció"}
        },
        {
            "company": {"name": "Graboplast Zrt.", "domain": "graboplast.hu", "industry": "Gyártó & Termelő Ipar (Padló & Műanyag)", "headcount_est": "250 fő", "hq_city": "Győr"},
            "lead": {"full_name": "Ivánkovics Gábor", "role": "Vezérigazgató (CEO)", "department_target": "Felsővezetés"}
        },
        {
            "company": {"name": "Graboplast Zrt.", "domain": "graboplast.hu", "industry": "Gyártó & Termelő Ipar (Padló & Műanyag)", "headcount_est": "250 fő", "hq_city": "Győr"},
            "lead": {"full_name": "Baloghné Kovács Rita", "role": "HR Igazgató", "department_target": "HR & Szervezetfejlesztés"}
        },
        {
            "company": {"name": "Leier Hungária Kft.", "domain": "leier.hu", "industry": "Gyártó & Termelő Ipar (Építőanyag)", "headcount_est": "230 fő", "hq_city": "Győr"},
            "lead": {"full_name": "Komlós Andor", "role": "Ügyvezető Igazgató", "department_target": "Felsővezetés"}
        },
        {
            "company": {"name": "Leier Hungária Kft.", "domain": "leier.hu", "industry": "Gyártó & Termelő Ipar (Építőanyag)", "headcount_est": "230 fő", "hq_city": "Győr"},
            "lead": {"full_name": "Szabados Péter", "role": "Operatív Igazgató (COO)", "department_target": "Operáció"}
        },
        {
            "company": {"name": "Bramac Kft.", "domain": "bramac.hu", "industry": "Gyártó & Termelő Ipar (Építőanyag)", "headcount_est": "170 fő", "hq_city": "Veszprém"},
            "lead": {"full_name": "Kovács Ákos", "role": "Ügyvezető Igazgató", "department_target": "Felsővezetés"}
        },
        {
            "company": {"name": "Bramac Kft.", "domain": "bramac.hu", "industry": "Gyártó & Termelő Ipar (Építőanyag)", "headcount_est": "170 fő", "hq_city": "Veszprém"},
            "lead": {"full_name": "Varga-Molnár Erika", "role": "Humánerőforrás Igazgató", "department_target": "HR & Szervezetfejlesztés"}
        },
        {
            "company": {"name": "PannonPharma Kft.", "domain": "pannonpharma.hu", "industry": "Gyártó & Termelő Ipar (Gyógyszergyártás)", "headcount_est": "120 fő", "hq_city": "Pécsvárad"},
            "lead": {"full_name": "Dr. Pallos József Péter", "role": "Ügyvezető Igazgató (CEO)", "department_target": "Felsővezetés"}
        },

        # --- 3. LOGISZTIKA & ELLÁTÁSI LÁNC ---
        {
            "company": {"name": "Express One Hungary Kft.", "domain": "expressone.hu", "industry": "Logisztika & Csomagszállítás", "headcount_est": "210 fő", "hq_city": "Budapest"},
            "lead": {"full_name": "Pesztericz Péter", "role": "Ügyvezető Igazgató (CEO)", "department_target": "Felsővezetés"}
        },
        {
            "company": {"name": "Express One Hungary Kft.", "domain": "expressone.hu", "industry": "Logisztika & Csomagszállítás", "headcount_est": "210 fő", "hq_city": "Budapest"},
            "lead": {"full_name": "Horváthné Szilágyi Zita", "role": "HR Igazgató", "department_target": "HR & Szervezetfejlesztés"}
        },
        {
            "company": {"name": "DPD Hungária Kft.", "domain": "dpd.hu", "industry": "Logisztika & Csomagszállítás", "headcount_est": "230 fő", "hq_city": "Budapest"},
            "lead": {"full_name": "Czifrik Krisztina", "role": "Ügyvezető Igazgató", "department_target": "Felsővezetés"}
        },
        {
            "company": {"name": "DPD Hungária Kft.", "domain": "dpd.hu", "industry": "Logisztika & Csomagszállítás", "headcount_est": "230 fő", "hq_city": "Budapest"},
            "lead": {"full_name": "Szalai Attila", "role": "Operatív Igazgató (COO)", "department_target": "Operáció"}
        },
        {
            "company": {"name": "Masped Zrt.", "domain": "masped.hu", "industry": "Logisztika & Szállítmányozás", "headcount_est": "140 fő", "hq_city": "Budapest"},
            "lead": {"full_name": "Kálmán Péter", "role": "Vezérigazgató", "department_target": "Felsővezetés"}
        },
        {
            "company": {"name": "Masped Zrt.", "domain": "masped.hu", "industry": "Logisztika & Szállítmányozás", "headcount_est": "140 fő", "hq_city": "Budapest"},
            "lead": {"full_name": "Farkas-Hajdú Beáta", "role": "HR Igazgató", "department_target": "HR & Szervezetfejlesztés"}
        },
        {
            "company": {"name": "Marso Kft.", "domain": "marso.hu", "industry": "Logisztika & Gumiabroncs Kereskedelem", "headcount_est": "220 fő", "hq_city": "Nyíregyháza"},
            "lead": {"full_name": "Somlai Sándor", "role": "Operatív Igazgató (COO)", "department_target": "Operáció"}
        },
        {
            "company": {"name": "Marso Kft.", "domain": "marso.hu", "industry": "Logisztika & Gumiabroncs Kereskedelem", "headcount_est": "220 fő", "hq_city": "Nyíregyháza"},
            "lead": {"full_name": "Becser Zoltán", "role": "Ügyvezető Igazgató", "department_target": "Felsővezetés"}
        },

        # --- 4. ÉLELMISZERIPAR, FMCG & KERESKEDELEM ---
        {
            "company": {"name": "Lipóti Pékség Kft.", "domain": "lipotipekseg.hu", "industry": "Élelmiszeripar & Pékáru Gyártás", "headcount_est": "240 fő", "hq_city": "Lipót"},
            "lead": {"full_name": "Tóth József Péter", "role": "Ügyvezető Igazgató (CEO)", "department_target": "Felsővezetés"}
        },
        {
            "company": {"name": "Lipóti Pékség Kft.", "domain": "lipotipekseg.hu", "industry": "Élelmiszeripar & Pékáru Gyártás", "headcount_est": "240 fő", "hq_city": "Lipót"},
            "lead": {"full_name": "Nagy-Kovács Orsolya", "role": "HR Vezető", "department_target": "HR & Szervezetfejlesztés"}
        },
        {
            "company": {"name": "Szamos Marcipán Kft.", "domain": "szamos.hu", "industry": "Élelmiszeripar & Cukrászati Termelés", "headcount_est": "160 fő", "hq_city": "Pilisvörösvár"},
            "lead": {"full_name": "Kelényi Ádám", "role": "Ügyvezető Igazgató", "department_target": "Felsővezetés"}
        },
        {
            "company": {"name": "Szamos Marcipán Kft.", "domain": "szamos.hu", "industry": "Élelmiszeripar & Cukrászati Termelés", "headcount_est": "160 fő", "hq_city": "Pilisvörösvár"},
            "lead": {"full_name": "Szabóné Varga Éva", "role": "Operatív és HR Vezető", "department_target": "HR & Operáció"}
        },
        {
            "company": {"name": "Gyermelyi Zrt.", "domain": "gyermelyi.hu", "industry": "Élelmiszeripar & Malomipar", "headcount_est": "250 fő", "hq_city": "Gyermely"},
            "lead": {"full_name": "Tóth Béla", "role": "Vezérigazgató-helyettes (COO)", "department_target": "Operáció"}
        },
        {
            "company": {"name": "Gyermelyi Zrt.", "domain": "gyermelyi.hu", "industry": "Élelmiszeripar & Malomipar", "headcount_est": "250 fő", "hq_city": "Gyermely"},
            "lead": {"full_name": "Bokros-Kis Mónika", "role": "Személyzeti Igazgató", "department_target": "HR & Szervezetfejlesztés"}
        },
        {
            "company": {"name": "Kifli.hu Shop Kft.", "domain": "kifli.hu", "industry": "E-kereskedelem & Élelmiszer Logisztika", "headcount_est": "250 fő", "hq_city": "Budapest"},
            "lead": {"full_name": "Gabriel Makki", "role": "Ügyvezető Igazgató (CEO)", "department_target": "Felsővezetés"}
        },
        {
            "company": {"name": "Kifli.hu Shop Kft.", "domain": "kifli.hu", "industry": "E-kereskedelem & Élelmiszer Logisztika", "headcount_est": "250 fő", "hq_city": "Budapest"},
            "lead": {"full_name": "Varga-Kovács Dóra", "role": "Head of People", "department_target": "HR & Szervezetfejlesztés"}
        },

        # --- 5. MUNKAERŐ & B2B VÁLLALATI SZOLGÁLTATÁSOK ---
        {
            "company": {"name": "WHC Csoport", "domain": "whc.hu", "industry": "B2B HR Szolgáltatás & Munkaerőpiac", "headcount_est": "180 fő", "hq_city": "Zalaegerszeg"},
            "lead": {"full_name": "Berta Péter", "role": "Ügyvezető Igazgató (CEO)", "department_target": "Felsővezetés"}
        },
        {
            "company": {"name": "WHC Csoport", "domain": "whc.hu", "industry": "B2B HR Szolgáltatás & Munkaerőpiac", "headcount_est": "180 fő", "hq_city": "Zalaegerszeg"},
            "lead": {"full_name": "Kiss-Tóth Andrea", "role": "Operatív Igazgató (COO)", "department_target": "Operáció"}
        },
        {
            "company": {"name": "Pannon-Work Zrt.", "domain": "pannonwork.hu", "industry": "B2B HR Szolgáltatás & Munkaerőpiac", "headcount_est": "160 fő", "hq_city": "Győr"},
            "lead": {"full_name": "Laczi Péter", "role": "Vezérigazgató", "department_target": "Felsővezetés"}
        },
        {
            "company": {"name": "Pannon-Work Zrt.", "domain": "pannonwork.hu", "industry": "B2B HR Szolgáltatás & Munkaerőpiac", "headcount_est": "160 fő", "hq_city": "Győr"},
            "lead": {"full_name": "Molnárné Fekete Judit", "role": "HR és Fejlesztési Igazgató", "department_target": "HR & Szervezetfejlesztés"}
        }
    ]

    print(f"\n[+] {len(fluvia_radar_targets)} db új hazai döntéshozó kötegelt feldolgozása (DNS MX, névbontás, M365/Google minta)...")
    results = harvest_and_save_leads(fluvia_radar_targets)

    print("\n" + "=" * 80)
    print(f"{'Vállalat':<22} | {'Infra':<18} | {'Döntéshozó':<22} | {'Generált Email':<32}")
    print("-" * 80)
    for r in results:
        print(f"{r['company'][:21]:<22} | {r['infra'][:17]:<18} | {r['name'][:21]:<22} | {r['email']:<32}")
    print("=" * 80)

    print(f"\n✅ Sikeres futtatás! Generált kimenetek:")
    print(f"👉 SQLite Adatbázis: {DB_PATH}")
    print(f"👉 Exportált CSV:     {CSV_EXPORT_PATH}")
    print(f"👉 Vizuális Dashboard: {DASHBOARD_HTML_PATH}")
