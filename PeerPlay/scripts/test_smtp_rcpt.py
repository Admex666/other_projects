"""
SMTP "RCPT TO" Live Validator with Catch-All Detection
======================================================
Ez a script teszteli az email címek létezését tisztán SMTP protokoll szinten,
levélküldés és üzenettörzs NÉLKÜL.

Lépések:
1. MX rekord lekérése a cél domainhez.
2. Kapcsolódás a 25-ös SMTP porton.
3. Catch-All vizsgálat: egy garantáltan nem létező cím tesztelése (pl. probe_nonexistent_xyz@domain).
   - Ha a szerver elfogadja (250): CATCH-ALL szerver (minden címre 250-et mond).
   - Ha elutasítja (550 / 5xx): PONTOS szerver (különbséget tesz létező és nem létező címek között).
4. A tényleges jelölt cím tesztelése (RCPT TO).
5. RSET és QUIT elküldése (a kapcsolat szabályos bontása, zéró email kiküldés).
"""

import os
import sys
import re
import uuid
import socket
import subprocess

def get_mx_host(domain: str) -> str | None:
    """Natív nslookup MX lekérdezés."""
    try:
        out = subprocess.check_output(
            ["nslookup", "-type=mx", domain],
            stderr=subprocess.DEVNULL,
            universal_newlines=True,
            timeout=5
        )
        for line in out.splitlines():
            if "mail exchanger" in line.lower():
                parts = line.split("=")
                if len(parts) >= 2:
                    return parts[-1].strip().rstrip(".")
    except Exception as e:
        print(f"[!] Hiba az MX lekérdezésnél ({domain}): {e}")
    return None

def recv_line(sock: socket.socket) -> str:
    """Egy sor beolvasása az SMTP socketről."""
    buf = b""
    while not buf.endswith(b"\n"):
        chunk = sock.recv(1024)
        if not chunk:
            break
        buf += chunk
    return buf.decode("utf-8", errors="replace").strip()

def send_cmd(sock: socket.socket, cmd: str) -> str:
    """SMTP parancs küldése és a szerver válaszának fogadása."""
    sock.sendall((cmd + "\r\n").encode("utf-8"))
    res = recv_line(sock)
    # Többsoros válaszok kezelése (pl. 250-es felsorolás)
    while len(res) >= 4 and res[3] == "-":
        res += "\n" + recv_line(sock)
    return res

def test_smtp_address(domain: str, candidate_email: str) -> dict:
    result = {
        "domain": domain,
        "candidate": candidate_email,
        "mx_host": None,
        "port_25_open": False,
        "is_catch_all": None,
        "candidate_accepted": None,
        "logs": [],
        "verdict": "UNKNOWN",
        "details": ""
    }

    # 1. MX Keresés
    mx = get_mx_host(domain)
    result["mx_host"] = mx
    if not mx:
        result["verdict"] = "MX_NOT_FOUND"
        result["details"] = f"A {domain} domainnek nincs publikus MX rekordja."
        return result

    result["logs"].append(f"-> Talált MX szerver: {mx}")

    # 2. Port 25 Kapcsolódás
    sock = None
    try:
        result["logs"].append(f"-> Kapcsolódási kísérlet a 25-ös portra: {mx}:25 (timeout: 5 mp)...")
        sock = socket.create_connection((mx, 25), timeout=5)
        result["port_25_open"] = True
        banner = recv_line(sock)
        result["logs"].append(f"<- Szerver Banner: {banner}")
    except socket.timeout:
        result["logs"].append("❌ TIMEOUT: A szerver nem válaszolt 5 mp-en belül.")
        result["verdict"] = "PORT_25_FILTERED_TIMEOUT"
        result["details"] = "A helyi internetszolgáltató (ISP) vagy a céges tűzfal blokkolja a kimenő 25-ös TCP portot."
        return result
    except OSError as e:
        result["logs"].append(f"❌ Hálózati hiba: {e}")
        result["verdict"] = "PORT_25_BLOCKED"
        result["details"] = f"A 25-ös port elérése sikertelen ({e}). Lakossági hálózatokon standard biztonsági szűrés."
        return result

    try:
        # 3. HELO kézfogás
        helo_res = send_cmd(sock, "HELO peerplay.local")
        result["logs"].append(f"-> HELO peerplay.local")
        result["logs"].append(f"<- {helo_res}")

        # 4. MAIL FROM
        from_res = send_cmd(sock, "MAIL FROM:<probe@peerplay.local>")
        result["logs"].append(f"-> MAIL FROM:<probe@peerplay.local>")
        result["logs"].append(f"<- {from_res}")

        # 5. CATCH-ALL TESZT (Garantáltan nem létező kamu cím)
        fake_local = f"nonexistent_probe_{uuid.uuid4().hex[:8]}"
        fake_email = f"{fake_local}@{domain}"
        fake_res = send_cmd(sock, f"RCPT TO:<{fake_email}>")
        result["logs"].append(f"-> [CATCH-ALL TESZT] RCPT TO:<{fake_email}>")
        result["logs"].append(f"<- {fake_res}")

        if fake_res.startswith("250"):
            result["is_catch_all"] = True
            result["logs"].append("⚠️ A szerver elfogadta a KAMU címet is -> CATCH-ALL szerver!")
        else:
            result["is_catch_all"] = False
            result["logs"].append("✅ A szerver elutasította a kamu címet -> PONTOS szerver (nincs catch-all).")

        # 6. RSET a tranzakció nullázására
        send_cmd(sock, "RSET")
        send_cmd(sock, "MAIL FROM:<probe@peerplay.local>")

        # 7. VALÓS JELÖLT TESZTELÉSE
        cand_res = send_cmd(sock, f"RCPT TO:<{candidate_email}>")
        result["logs"].append(f"-> [JELÖLT TESZT] RCPT TO:<{candidate_email}>")
        result["logs"].append(f"<- {cand_res}")

        if cand_res.startswith("250"):
            result["candidate_accepted"] = True
            if result["is_catch_all"]:
                result["verdict"] = "CATCH_ALL_ACCEPTED"
                result["details"] = "A szerver elfogadta, de Catch-All miatt ez nem garantálja a személyes postafiók létezését."
            else:
                result["verdict"] = "DELIVERABLE_CONFIRMED"
                result["details"] = "A postafiók BIZONYÍTOTTAN LÉTEZIK és fogad leveleket (250 OK)."
        elif cand_res.startswith("550") or cand_res.startswith("551") or cand_res.startswith("553"):
            result["candidate_accepted"] = False
            result["verdict"] = "UNDELIVERABLE_BOUNCE"
            result["details"] = f"A szerver kifejezetten elutasította a címet (lepattanó hiba): {cand_res}"
        elif cand_res.startswith("450") or cand_res.startswith("451") or cand_res.startswith("452"):
            result["candidate_accepted"] = None
            result["verdict"] = "GREYLISTED_TEMPORARY"
            result["details"] = f"A szerver szürkelistázást (greylisting) alkalmaz, ideiglenesen visszautasította: {cand_res}"
        else:
            result["verdict"] = "UNEXPECTED_RESPONSE"
            result["details"] = f"Váratlan válaszkód: {cand_res}"

        # 8. Kapcsolat bontása (QUIT)
        send_cmd(sock, "QUIT")
        result["logs"].append("-> QUIT (kapcsolat szabályosan lezárva, nulla levél kiküldve)")

    except Exception as e:
        result["logs"].append(f"[!] Hiba a protokoll futása közben: {e}")
        result["verdict"] = "PROTOCOL_ERROR"
        result["details"] = str(e)
    finally:
        if sock:
            try:
                sock.close()
            except Exception:
                pass

    return result

if __name__ == "__main__":
    print("=" * 70)
    print("   SMTP 'RCPT TO' + Catch-All Védelem Éles Tesztelő")
    print("=" * 70)

    # Tesztelendő címek
    test_cases = [
        {"domain": "richter.hu", "candidate": "katalin.erdei@richter.hu"},
        {"domain": "praktiker.hu", "candidate": "andrea.nagy-jakab@praktiker.hu"},
        {"domain": "gmail.com", "candidate": "nemletezo_random_teszt_123456789@gmail.com"}
    ]

    for tc in test_cases:
        print(f"\n[+] Tesztelés: {tc['candidate']} a {tc['domain']} domainen...")
        res = test_smtp_address(tc["domain"], tc["candidate"])
        
        print(f"    ├─ MX Szerver:       {res['mx_host']}")
        print(f"    ├─ Port 25 Státusz:  {'NYITVA' if res['port_25_open'] else 'BLOKKOLVA / TIMEOUT'}")
        print(f"    ├─ Catch-All:        {res['is_catch_all']}")
        print(f"    ├─ Eredmény Kód:     {res['verdict']}")
        print(f"    ├─ Értékelés:        {res['details']}")
        print("    └─ SMTP Napló:")
        for log in res["logs"]:
            print(f"       {log}")

    print("\n" + "=" * 70)
    print("Teszt lezárva. Semmilyen levéltörzs (DATA) NEM került elküldésre!")
    print("=" * 70)
