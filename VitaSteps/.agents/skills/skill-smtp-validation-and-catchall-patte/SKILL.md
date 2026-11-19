---
name: skill-smtp-validation-and-catchall-patte
description: >-
  Use this skill when handling 🛡️ smtp rcpt to validáció és catch-all detektálási minták or related operational workflows in domain 'peerplay'. Synthesized from canonical operational learning: smtp_validation_and_catchall_patterns.md.
---

# 🛡️ SMTP RCPT TO Validáció és Catch-All Detektálási Minták

## Overview & Purpose
This skill encapsulates verified operational procedures and verified solutions synthesized from `smtp_validation_and_catchall_patterns.md`.
Agents should activate this skill instead of re-inventing ad-hoc scripts or debugging known procedures.

## Operational Protocol & Steps
# 🛡️ SMTP RCPT TO Validáció és Catch-All Detektálási Minták

**Domain:** B2B Lead Validáció, Email Kézbesíthetőség & Hálózati Felderítés  
**Kapcsolódó Tudáselemek:** `b2b_validation_playbook.md`, `current_system_state_and_b2b_validation.md`  
**Dátum:** 2026-11-17  
**Státusz:** Faktuálisan Tesztelve & Validálva

---

## 1. Az SMTP Handshake (RCPT TO) Validációs Elve

Az email címek létezésének legmagasabb szintű technikai ellenőrzése közvetlenül a fogadó Mail Exchanger (MX) szerveren történik az **RFC 5321 szabványú SMTP kézfogás** szimulációjával, **levéltörzs (DATA) és valódi üzenetküldés nélkül**.

### A Protokoll Lépései:
```text
[Kliens]  ---> HELO peerplay.local
[Szerver] <--- 250 Hello!

[Kliens]  ---> MAIL FROM:<probe@peerplay.local>
[Szerver] <--- 250 2.1.0 Sender OK

[Kliens]  ---> [1. CATCH-ALL PROBE] RCPT TO:<nonexistent_random_xyz@domain.hu>
[Szerver] <--- 550 User Unknown  (✅ Pontos szerver)  VAGY  250 OK (⚠️ Catch-All!)

[Kliens]  ---> RSET
[Kliens]  ---> MAIL FROM:<probe@peerplay.local>

[Kliens]  ---> [2. JELÖLT TESZT] RCPT TO:<keresztnev.vezeteknev@domain.hu>
[Szerver] <--- 250 Recipient OK  (✅ Létező postafiók)  VAGY  550 Recipient Rejected (❌ Lepattanó)

[Kliens]  ---> QUIT  (Kapcsolat bontása, NULLA levél kézbesítve)
```

---

## 2. A Catch-All Szerverek Kockázata és Leleplezése

### Mi az a Catch-All?
Sok vállalati szerver és felhős átjáró (különösen a Microsoft 365 Exchange Online Protection - EOP) a külső kapunál (Edge transport) **minden formailag helyes címre 250 OK választ ad**, és csak a belső routing vagy karantén során szűri a nem létező fiókokat.
- **Kockázat Catch-All védelem nélkül:** Egy egyszerű SMTP tesztelő a kamu és az igazi címre is `250 OK`-t kapna, ami **hamis biztonságérzetet** okoz.

### A Catch-All Detektálási Szabály:
Minden valós cím tesztelése előtt kötelezően elküldünk egy **véletlenszerűen generált, garantáltan nem létező kamu címet** (pl. `nonexistent_probe_eaa5cfcd@domain.hu`):
1. **Ha a kamu címre `250 OK` érkezik:**  
   $\rightarrow$ A szerver **CATCH-ALL**. A státusz: `CATCH_ALL_ACCEPTED`. Nem vehető készpénznek a konkrét postaláda fizikai megléte, ilyenkor a DNS/SPF infrastruktúra-alapú statisztikai mintaheurisztika a döntő.
2. **Ha a kamu címre `550 / 551 / 553 / 554` érkezik:**  
   $\rightarrow$ A szerver **PONTOS (nem catch-all)**. Ha a valós jelöltre ezután `250 OK` jön, a cím **100%-os bizonyossággal kézbesíthető**.

---

## 3. Hálózati Korlátok és Kétlépcsős Architektúra

Az éles tesztek során két hálózati korlátot igazoltunk:

### A) Spamhaus PBL (Policy Block List) & Lakossági Port 25
- **Tapasztalat:** Lakossági vagy kis irodai internetszolgáltatók (Telekom, Vodafone stb.) IP-címeiről a Microsoft és Google szerverek egy része `550 5.7.1 Service unavailable, Client host blocked using Spamhaus` hibával elutasítja a közvetlen SMTP kapcsolatot.
- **Megoldás:**
  - **Lokális futtatáskor (0 Ft):** DNS MX + SPF mintaheurisztikát alkalmazunk. A cégek 85%-ánál (M365) a `keresztnev.vezeteknev` minta bizonyítottan pontos, és nem igényli a port 25 nyitottságát.
  - **Közvetlen SMTP Ping futtatásakor:** Egy tiszta, fix IP-címmel és beállított rDNS-sel (PTR) rendelkező dedikált felhős gépről (VPS) futtatjuk az SMTP ellenőrzőt.

---

## 4. Magyar Névkezelési Szabályok (Speciális Női és Összetett Nevek)

A korábbi `Szijjné Kállai Ildikó` teszteset alapján a névelemző motornak kötelezően kezelnie kell a magyar névrendszer speciális struktúráit:

1. **`-né` végződésű tag:** Férjezett családnév része (pl. `Szijjné`).
2. **Kettős családnév leánykori névvel:** Ha a név 3 szóból áll (pl. `[Vezetéknév1] [Vezetéknév2] [Keresztnév]`), az utolsó szótag a tényleges keresztnév:
   * Név: `Szijjné Kállai Ildikó`
   * Helyes bontás: Családnév: `Szijjné Kállai`, Keresztnév: `Ildikó`
   * Generált elsődleges minták: `ildiko.szijjne-kallai@domain.hu`, másodlagos: `ildiko.kallai@domain.hu`.
3. **Titulusok:** `Dr.`, `ifj.`, `id.`, `prof.` automatikus leválasztása a keresztnév/vezetéknév párosítás előtt.

---

## 5. Perzisztens Eszközök a Repóban

* **Élő SMTP Tesztelő Script:** [scripts/test_smtp_rcpt.py](file:///E:/Data/other_projects/PeerPlay/scripts/test_smtp_rcpt.py)
* **Lead Motor & DNS Heurisztika:** [scripts/b2b_lead_engine.py](file:///E:/Data/other_projects/PeerPlay/scripts/b2b_lead_engine.py)
* **Adatbázis:** [data/b2b_lead_pipeline.db](file:///E:/Data/other_projects/PeerPlay/data/b2b_lead_pipeline.db)
* **Központi Dashboard:** [public/b2b_leads_dashboard.html](file:///E:/Data/other_projects/PeerPlay/public/b2b_leads_dashboard.html)

## Executable Scripts
- [run_skill-smtp-validation-and-catchall-patte.sh](./scripts/run_skill-smtp-validation-and-catchall-patte.sh)

## Canonical Source of Truth
- Primary Reference: [smtp_validation_and_catchall_patterns.md](./references/smtp_validation_and_catchall_patterns.md)
- Original Location: `E:\Data\other_projects\PeerPlay\knowledge\learnings\smtp_validation_and_catchall_patterns.md`
