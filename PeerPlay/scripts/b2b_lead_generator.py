"""
PeerPlay - Ingyenes B2B Lead & Email Generator Script
Demonstrációs és futtatható algoritmus magyar cégek vezetői emailjeinek generálására és ellenőrzésére.
"""

import re
import socket
import unicodedata

# 1. Magyar ékezetmentesítő segédfüggvény
def remove_accents(input_str: str) -> str:
    nfkd = unicodedata.normalize('NFKD', input_str)
    return "".join([c for c in nfkd if not unicodedata.combining(c)]).lower()

# 2. Tipikus magyar céges email minták előállítása
def generate_email_patterns(first_name: str, last_name: str, domain: str) -> list[str]:
    f = remove_accents(first_name.strip())
    l = remove_accents(last_name.strip())
    dom = domain.strip().lower().replace("http://", "").replace("https://", "").replace("www.", "").split("/")[0]

    patterns = [
        f"{f}.{l}@{dom}",      # peter.kovacs@ceg.hu (Leggyakoribb: ~65%)
        f"{l}.{f}@{dom}",      # kovacs.peter@ceg.hu (~20%)
        f"{f[0]}.{l}@{dom}",   # p.kovacs@ceg.hu (~10%)
        f"{f}@{dom}",          # peter@ceg.hu (KKV-knál gyakori)
        f"{l}@{dom}",          # kovacs@ceg.hu
        f"{f}{l[0]}@{dom}",    # peterk@ceg.hu
    ]
    return patterns

# 3. Domain MX (Levelezőszerver) meglétének ellenőrzése
def check_domain_has_mx(domain: str) -> bool:
    dom = domain.strip().lower().replace("http://", "").replace("https://", "").replace("www.", "").split("/")[0]
    try:
        # Próbálunk host IP-t vagy MX-et feloldani socket szinten
        socket.gethostbyname(dom)
        return True
    except socket.gaierror:
        return False

# Demó tesztelés
if __name__ == '__main__':
    print("=== PEERPLAY INGYENES LEAD & EMAIL MINTAGENERÁTOR ===")
    
    test_leads = [
        {"name": "Kovács Péter", "role": "Ügyvezető Igazgató", "company": "Minta Tech Zrt.", "domain": "mintatech.hu"},
        {"name": "Szabó Katalin", "role": "HR Igazgató", "company": "LogiTrans Kft.", "domain": "logitrans.hu"},
        {"name": "Horváth Balázs", "role": "Gyártási Igazgató", "company": "Precíziós Acél Kft.", "domain": "preciziosacel.hu"},
    ]

    for lead in test_leads:
        first, last = lead["name"].split(" ", 1)
        patterns = generate_email_patterns(first, last, lead["domain"])
        has_host = check_domain_has_mx(lead["domain"])
        
        print(f"\n🏢 Cég: {lead['company']} | Név: {lead['name']} ({lead['role']})")
        print(f"🌐 Domain: {lead['domain']} (Host elérhető: {'IGEN' if has_host else 'NEM'})")
        print("📧 Generált lehetséges címek prioritási sorrendben:")
        for idx, p in enumerate(patterns[:4], 1):
            print(f"   {idx}. {p}")
