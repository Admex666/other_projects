"""
vault_playbook_builder.py  (Groq — Knowledge Compiler Edition)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Pipeline: MAP → SYNTHESIS → REDUCE

API kulcs: https://console.groq.com → API Keys → Create API Key
.env fájl: GROQ_API_KEY=gsk_...

Futtatás:
  python vault_playbook_builder.py --limit 30
  python vault_playbook_builder.py --limit 0          # mind a 227 üzleti fájl
  python vault_playbook_builder.py --reduce-only      # csak Reduce (meglévő chunkokból)
  python vault_playbook_builder.py --skip-synthesis   # MAP → REDUCE (nincs köztes fázis)
"""

import os
import re
import sys
import time
import argparse
import json
import pandas as pd
from groq import Groq
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── CONFIG ─────────────────────────────────────────────────────────────────
GROQ_CLIENTS       = []
CURRENT_CLIENT_IDX = 0

VAULT_PATH       = r"E:\obsidian_safe\obsidian_safe"
CLUSTERS_CSV     = "vault_clusters.csv"
BIZ_CLUSTERS     = [0, 3, 5, 12]
CHUNK_SIZE       = 4
OUTPUT_DIR       = Path("output")
CHUNKS_DIR       = OUTPUT_DIR / "chunks"
CHAPTERS_DIR     = OUTPUT_DIR / "chapters"
MODEL            = "llama-3.3-70b-versatile"
MAX_NOTE_CHARS   = 3000
SLEEP_BETWEEN    = 20.0
MAX_RETRIES      = 5
TEMP_MAP         = 0.6
TEMP_SYNTHESIS   = 0.6
TEMP_REDUCE      = 0.7


# ── HELPERS ────────────────────────────────────────────────────────────────
def clean_text(text: str) -> str:
    text = re.sub(r'^---.*?---', '', text, flags=re.DOTALL)
    text = re.sub(r'!\[.*?\]\(.*?\)', '', text)
    text = re.sub(r'\[\[(?:.*?\|)?(.*?)\]\]', r'\1', text)
    text = re.sub(r'http\S+', '', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def read_note(path: str) -> str:
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            raw = f.read()
        clean = clean_text(raw)
        return clean[:MAX_NOTE_CHARS] + "\n...[truncated]" if len(clean) > MAX_NOTE_CHARS else clean
    except Exception as e:
        return f"[ERROR: {e}]"


def get_business_files(limit: int = 0) -> list[dict]:
    df = pd.read_csv(CLUSTERS_CSV)
    biz = df[df['cluster'].isin(BIZ_CLUSTERS)].reset_index(drop=True)
    if limit > 0:
        biz = biz.head(limit)
    return biz[['filename', 'path']].to_dict('records')


def chunk_list(lst: list, size: int) -> list[list]:
    return [lst[i:i+size] for i in range(0, len(lst), size)]


def build_dossier_block(dossiers: list[str], max_total_chars: int = 12000) -> str:
    if not dossiers:
        return ""
    # Elosztjuk a rendelkezésre álló karakterkeretet a dossziék között
    chars_per_dossier = max(400, max_total_chars // len(dossiers))
    block = ""
    for i, d in enumerate(dossiers, 1):
        short = d[:chars_per_dossier] + "\n...[rövidítve]" if len(d) > chars_per_dossier else d
        block += f"\n{'─'*60}\n#### DOSSIER {i}\n{'─'*60}\n{short}\n"
    return block


# ── API CALL WITH RETRY ─────────────────────────────────────────────────────
def call_groq(system: str, user: str, temperature: float = 0.6,
              max_tokens: int = 8192) -> str:
    global CURRENT_CLIENT_IDX
    consecutive_429s = 0
    total_keys = len(GROQ_CLIENTS)

    for attempt in range(1, MAX_RETRIES * total_keys + 1):
        client = GROQ_CLIENTS[CURRENT_CLIENT_IDX]
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user",   "content": user},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            consecutive_429s = 0
            return response.choices[0].message.content
        except Exception as e:
            err = str(e)
            if '429' in err or 'rate_limit' in err.lower():
                consecutive_429s += 1
                next_idx = (CURRENT_CLIENT_IDX + 1) % total_keys
                
                if consecutive_429s >= total_keys:
                    m = re.search(r'please try again in ([0-9.]+)s', err, re.IGNORECASE)
                    wait = float(m.group(1)) + 2 if m else 30 * (attempt // total_keys + 1)
                    print(f"\n  [429] Rate limit a(z) {CURRENT_CLIENT_IDX + 1}. kulcson. (Minden kulcs betelt!) Várakozás {wait:.0f}s... ({attempt}/{MAX_RETRIES * total_keys})", flush=True)
                    time.sleep(wait)
                    consecutive_429s = 0
                else:
                    print(f"\n  [429] Rate limit a(z) {CURRENT_CLIENT_IDX + 1}. kulcson. Váltás a(z) {next_idx + 1}. kulcsra...", flush=True)
                
                CURRENT_CLIENT_IDX = next_idx
            else:
                raise
                
    raise Exception("❌ Minden API újrapróbálkozás kimerült.")


# ── PHASE 1: MAP ───────────────────────────────────────────────────────────
# Not a summarizer. A knowledge extraction engine.
MAP_SYSTEM = """\
Te egy tudás-szintetizáló elemző rendszer vagy — NEM executive summary generátor.

A feladatod: üzleti és marketing tartalmakból mély tudáskinyerést végezni.
A kimenet NEM rövid összefoglaló. A kimenet egy részletes "Knowledge Extraction Dossier".

AMIT KI KELL NYERNI:

1. MENTÁLIS MODELLEK ÉS STRATÉGIAI MINTÁK
   - Milyen implicit döntési logikák húzódnak meg a szöveg mögött?
   - Milyen gondolkodási keretrendszert használ az anyag?
   - Melyek az ismétlődő elvek, amelyek visszaköszönnek?

2. OK-OKOZATI KAPCSOLATOK
   - Mi vezet mihez? (Ha X, akkor Y logika)
   - Milyen mechanizmusokon keresztül hatnak egymásra a fogalmak?
   - Milyen lépcsők, feltételek, trigger-pontok vannak?

3. RENDSZERSZINTŰ ÖSSZEFÜGGÉSEK
   - Hogyan kapcsolódnak egymáshoz az ötletek?
   - Milyen hierarchiák, függőségek, kölcsönhatások vannak?
   - Melyek az erősítő (flywheel) és gyengítő hatások?

4. DÖNTÉSI SZABÁLYOK ÉS TRIGGER-FELTÉTELEK
   - Mikor alkalmaz valamit az anyag? (trigger condition)
   - Milyen körülmények között működik egy stratégia és mikor nem?
   - Milyen trade-offokat azonosít?

5. ANTI-PATTERNEK ÉS HIBÁK
   - Mit NEM szabad csinálni és miért?
   - Milyen tipikus hibákat emel ki az anyag?
   - Milyen figyelmeztetések vannak?

6. KONKRÉT IMPLEMENTÁCIÓS LOGIKA
   - Pontos számok, mérőszámok, küszöbértékek
   - Konkrét eszközök, lépések, workflow-k
   - Reprodukálható folyamatok

KIMENET FORMÁTUMA:
- ## szekciók a fenti 6 kategóriához
- Részletes bullet listák, al-bullet-ekkel ahol szükséges
- Őrizd meg az összes specifikus nevet, számot, formulát
- Magyar nyelven, de az angol terminus technicusokat hagyd meg

CÉLZOTT TERJEDELEM: 1500–3000 szó per chunk.

KRITIKUS SZABÁLY:
A cél NEM rövid összefoglaló készítése.
NE tömörítsd az információt — bontsd ki, rendszerezd, kapcsold össze.
Viselkedj tudás-szintetizáló elemzőként, nem újságíróként.\
"""

MAP_USER_TEMPLATE = """\
Az alábbi {n} üzleti/marketing note-ot kaptad egy Obsidian vaultból.
Készíts róluk egy részletes Knowledge Extraction Dossier-t a megadott struktúra szerint.

{notes_block}

Most készítsd el a Knowledge Extraction Dossier-t (1500–3000 szó):\
"""


def map_chunk(chunk_idx: int, notes: list[dict]) -> tuple[str, bool]:
    CHUNKS_DIR.mkdir(parents=True, exist_ok=True)
    out_file = CHUNKS_DIR / f"chunk_{chunk_idx:03d}.md"

    if out_file.exists():
        print(f"  [SKIP] chunk_{chunk_idx:03d}.md már létezik, kihagyva.")
        return out_file.read_text(encoding='utf-8'), False

    notes_block = ""
    for i, note in enumerate(notes, 1):
        content = read_note(note['path'])
        fname = Path(note['filename']).stem[:80]
        notes_block += f"\n{'─'*60}\n### NOTE {i}: {fname}\n{'─'*60}\n{content}\n"

    user = MAP_USER_TEMPLATE.format(n=len(notes), notes_block=notes_block)

    print(f"  → Chunk {chunk_idx:03d} ({len(notes)} fájl)...", end=" ", flush=True)
    dossier = call_groq(MAP_SYSTEM, user, temperature=TEMP_MAP, max_tokens=3000)
    out_file.write_text(dossier, encoding='utf-8')
    words = len(dossier.split())
    print(f"✓ ({words} szó → {out_file.name})")
    return dossier, True


# ── PHASE 2: SYNTHESIS (intermediate thinking layer) ──────────────────────
SYNTHESIS_SYSTEM = """\
Te egy stratégiai tudás-architekt vagy.

Több chunk-nyi nyers üzleti tudás-kinyerési dossier-t kaptál.
A feladatod: felismerni a mélyebb mintázatokat és struktúrát — mielőtt a végső rendszer megépül.

AMIT KI KELL DERÍTENI:

1. VISSZATÉRŐ ELVEK (Recurring Principles)
   - Melyek azok az elvek, amelyek több különböző forrásban is megjelennek?
   - Milyen "törvények" rajzolódnak ki ismétlődően?

2. KAUZÁLIS HIERARCHIA (Causal Hierarchy)
   - Melyek az alap-okok és melyek a következmények?
   - Mi van felső szinten (stratégia) és mi az alsó szinten (taktika/eszköz)?
   - Milyen sorrend, prioritás adódik ki az anyagból?

3. ELLENTMONDÁSOK ÉS FESZÜLTSÉGEK
   - Hol mond ellen egymásnak két forrás?
   - Milyen trade-offok vannak a különböző elvek között?
   - Melyik ellentmondás valójában kontextus-függő (mindkettő igaz, de más helyzetben)?

4. EMERGENS MODELLEK (Emergent Models)
   - Milyen magasabb szintű üzleti modell rajzolódik ki az egész anyagból?
   - Milyen "operációs logika" köti össze a részeket?
   - Mi az, ami az egyes chunkokban nem volt kimondva, de az összességből következik?

5. STRATÉGIAI TAXONÓMIA
   - Hogyan csoportosíthatók a fogalmak egy egységes rendszerbe?
   - Melyek a fő "tengelyek" (pl. Akvizíció → Konverzió → Megtartás)?
   - Milyen életciklus-logika adódik ki?

6. KRITIKUS KAPCSOLATOK
   - Mely fogalmak erősítik egymást (flywheel)?
   - Mely fogalmak helyettesítik egymást (alternatives)?
   - Milyen függőségek (prerequisite chains) vannak?

KIMENET: Strukturált elemzés, nem összefoglaló.
Célzott terjedelem: 1000–2000 szó.
Ez lesz a "thinking layer" a végső playbook előtt.\
"""

SYNTHESIS_USER_TEMPLATE = """\
Az alábbi {n} Knowledge Extraction Dossier-t kaptad.
Végezz mélystruktúra-elemzést — azonosítsd az emergens mintázatokat, \
hierarchiákat és kapcsolatrendszereket.

{dossiers_block}

Készítsd el a Stratégiai Szintézis-Elemzést:\
"""


def run_synthesis(dossiers: list[str]) -> tuple[str, bool]:
    print("\n[PHASE 2 — SYNTHESIS] Mélystruktúra-elemzés...", flush=True)
    syn_path = OUTPUT_DIR / "synthesis_layer.md"

    if syn_path.exists():
        print("  [SKIP] synthesis_layer.md már létezik, kihagyva.")
        return syn_path.read_text(encoding='utf-8'), False

    # Építjük fel a dosszié blokkot, maximum 12,000 karakterben
    block = build_dossier_block(dossiers, max_total_chars=12000)

    user = SYNTHESIS_USER_TEMPLATE.format(n=len(dossiers), dossiers_block=block)
    result = call_groq(SYNTHESIS_SYSTEM, user, temperature=TEMP_SYNTHESIS, max_tokens=3500)
    syn_path.write_text(result, encoding='utf-8')
    print(f"  ✓ Synthesis layer kész ({len(result.split())} szó → {syn_path.name})")
    return result, True


# ── PHASE 3: OUTLINE ───────────────────────────────────────────────────────
OUTLINE_SYSTEM = """\
Te egy stratégiai rendszerező vagy. A feladatod, hogy egy mély, átfogó üzleti és marketing playbook "Tartalomjegyzékét" (Outline) hozd létre a bemenetként kapott Szintézis és Dossier-k alapján.

A kimenetednek KIZÁRÓLAG egy érvényes JSON tömbnek kell lennie, amely tartalmazza a fejezetek címeit és egy rövid leírást.
Formátum:
[
  {
    "chapter_number": 1,
    "title": "A fejezet címe",
    "description": "Miről fog szólni a fejezet (1-2 mondat)"
  }
]

Tervezz 5-8 tartalmas, egymásra épülő fejezetet. Ne írj markdown kódblokkot, csak magát a nyers JSON tömböt add vissza!
"""

def generate_outline(dossiers: list[str], synthesis: str) -> tuple[list[dict], bool]:
    print("\n[PHASE 3 — OUTLINE] Playbook Vázlat (Tartalomjegyzék) generálása...", flush=True)
    out_path = OUTPUT_DIR / "outline.json"
    
    if out_path.exists():
        print("  [SKIP] outline.json már létezik, betöltés...")
        try:
            return json.loads(out_path.read_text(encoding='utf-8')), False
        except Exception as e:
            print("  [ERROR] outline.json betöltése sikertelen, újra generáljuk...", e)

    user = f"A SZINTÉZIS:\n{synthesis}\n\nKészítsd el a JSON tartalomjegyzéket a playbookhoz:"
    outline_json = call_groq(OUTLINE_SYSTEM, user, temperature=0.5, max_tokens=2048)
    
    try:
        clean_json = outline_json.strip()
        if clean_json.startswith('```json'):
            clean_json = clean_json[7:]
        if clean_json.endswith('```'):
            clean_json = clean_json[:-3]
        clean_json = clean_json.strip()
        
        outline = json.loads(clean_json)
        out_path.write_text(json.dumps(outline, indent=2, ensure_ascii=False), encoding='utf-8')
        print(f"  ✓ Outline generálva: {len(outline)} fejezet.")
        return outline, True
    except Exception as e:
        print(f"❌ Hiba a JSON parse-olásakor:\n{outline_json}")
        raise e

# ── PHASE 4: CHAPTER EXPANSION ─────────────────────────────────────────────
CHAPTER_SYSTEM = """\
Te egy üzleti operációs rendszer tervezője vagy — NEM könyv-összefoglaló generátor.
A feladatod a Playbook EGYETLEN FEJEZETÉNEK extrém részletes, mély kifejtése a rendelkezésre álló dokumentumok alapján.

A DOCTRINE MEGALKOTÁSÁNAK ELVEI:
1. OPERÁCIÓS LOGIKA: Döntési szabályok, trigger-condition logika, workflow-k.
2. KAUZÁLIS MAGYARÁZATOK: Miből következik, mit befolyásol, mik a trade-offok.
3. EMERGENS MODELLEK: Magasabb szintű mintázatok.

MOST KIZÁRÓLAG EGY FEJEZETET KELL MEGÍRNOD! Ne írj bevezetőt a könyvhöz, ne írj összefoglalót a könyvről. Koncentrálj arra az egy fejezetre, amit a felhasználó kér.
Terjedelem: Legalább 1000-1500 szó az adott fejezetről. Fejtsd ki a lehető legmélyebben!
"""

def expand_chapter(chapter: dict, dossiers: list[str], synthesis: str, outline: list[dict]) -> tuple[str, bool]:
    CHAPTERS_DIR.mkdir(parents=True, exist_ok=True)
    ch_num = chapter.get('chapter_number', 0)
    out_file = CHAPTERS_DIR / f"chapter_{ch_num:02d}.md"
    
    if out_file.exists():
        print(f"  [SKIP] chapter_{ch_num:02d}.md már létezik, betöltés...")
        return out_file.read_text(encoding='utf-8'), False

    print(f"  → Fejezet {ch_num} generálása: {chapter.get('title', 'N/A')}...", end=" ", flush=True)

    # Építjük fel a dosszié blokkot dinamikus csonkítással, hogy beleférjünk a limitbe
    dossiers_block = build_dossier_block(dossiers, max_total_chars=10000)

    outline_str = "\n".join([f"{c.get('chapter_number', '?')}. {c.get('title', '?')}: {c.get('description', '?')}" for c in outline])

    user = (
        f"A KÖNYV TELJES VÁZLATA:\n{outline_str}\n\n"
        f"SZINTÉZIS:\n{synthesis}\n\n"
        f"DOSSIER TÖREDÉKEK:\n{dossiers_block}\n\n"
        f"A TE FELADATOD MOST KIZÁRÓLAG ENNEK A FEJEZETNEK A MEGÍRÁSA:\n"
        f"Fejezet: {ch_num}. {chapter.get('title', 'N/A')}\n"
        f"Leírás: {chapter.get('description', 'N/A')}\n\n"
        f"Kérlek, fejtsd ki ezt a fejezetet a lehető legrészletesebben (1000+ szó), alcímekkel, bullet pointokkal és konkrétumokkal!"
    )

    result = call_groq(CHAPTER_SYSTEM, user, temperature=TEMP_REDUCE, max_tokens=3500)
    out_file.write_text(result, encoding='utf-8')
    words = len(result.split())
    print(f"✓ ({words} szó)")
    return result, True


# ── MAIN ───────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Vault Knowledge Compiler — MAP → SYNTHESIS → REDUCE"
    )
    parser.add_argument("--limit",          type=int, default=30,
                        help="Max fájlok száma (0 = mind)")
    parser.add_argument("--chunk-size",     type=int, default=CHUNK_SIZE)
    parser.add_argument("--reduce-only",    action="store_true",
                        help="Csak Reduce: meglévő chunk + synthesis fájlokból")
    parser.add_argument("--skip-synthesis", action="store_true",
                        help="MAP → REDUCE (nincs synthesis fázis)")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(exist_ok=True)
    CHUNKS_DIR.mkdir(exist_ok=True)
    CHAPTERS_DIR.mkdir(exist_ok=True)

    api_keys_str = os.getenv("GROQ_API_KEYS") or os.getenv("GROQ_API_KEY")
    if not api_keys_str:
        print("❌ HIBA: Nem található GROQ_API_KEYS vagy GROQ_API_KEY a .env fájlban!")
        print("   Regisztrálj: https://console.groq.com → API Keys → Create API Key")
        sys.exit(1)

    keys = [k.strip() for k in api_keys_str.split(',') if k.strip()]
    global GROQ_CLIENTS
    GROQ_CLIENTS = [Groq(api_key=k) for k in keys]
    print(f"✅ Groq — {MODEL} ({len(GROQ_CLIENTS)} db API kulccsal inicializálva)\n")

    dossiers = []

    # ── PHASE 1: MAP ──────────────────────────────────────────────────────
    if args.reduce_only:
        print("[REDUCE-ONLY] Meglévő chunk fájlok betöltése...")
        chunk_files = sorted(CHUNKS_DIR.glob("chunk_*.md"))
        if not chunk_files:
            print("❌ Nincsenek chunk fájlok az output/chunks/ mappában!")
            sys.exit(1)
        dossiers = [f.read_text(encoding='utf-8') for f in chunk_files]
        print(f"  → {len(dossiers)} dossier betöltve.")
    else:
        files = get_business_files(args.limit)
        chunks = chunk_list(files, args.chunk_size)
        label = f"első {args.limit}" if args.limit > 0 else "összes"
        print(f"[PHASE 1 — MAP] {len(files)} fájl ({label}) → {len(chunks)} chunk (á {args.chunk_size})\n")

        for idx, chunk in enumerate(chunks):
            dossier, hit_api = map_chunk(idx, chunk)
            dossiers.append(dossier)
            if hit_api and idx < len(chunks) - 1:
                time.sleep(SLEEP_BETWEEN)

    total_map_words = sum(len(d.split()) for d in dossiers)
    print(f"\n[PHASE 1 KÉSZ] {len(dossiers)} dossier — összesen ~{total_map_words:,} szó")

    # ── PHASE 2: SYNTHESIS ────────────────────────────────────────────────
    if args.skip_synthesis:
        synthesis = "(Synthesis fázis kihagyva)"
        print("\n[PHASE 2 — SYNTHESIS] Kihagyva (--skip-synthesis)")
    else:
        synthesis, hit_api = run_synthesis(dossiers)
        if hit_api:
            time.sleep(SLEEP_BETWEEN)

    # ── PHASE 3: OUTLINE ──────────────────────────────────────────────────
    outline, hit_api = generate_outline(dossiers, synthesis)
    if hit_api:
        time.sleep(SLEEP_BETWEEN)

    # ── PHASE 4: CHAPTER EXPANSION ────────────────────────────────────────
    print("\n[PHASE 4 — CHAPTER EXPANSION] Részletes fejezetek generálása...", flush=True)
    chapters_content = []
    for chapter in outline:
        content, hit_api = expand_chapter(chapter, dossiers, synthesis, outline)
        chapters_content.append(content)
        if hit_api:
            time.sleep(SLEEP_BETWEEN)

    # ── ÖSSZESZERELÉS ─────────────────────────────────────────────────────
    suffix = f"_first{args.limit}" if (args.limit > 0 and not args.reduce_only) else "_full"
    out_path = OUTPUT_DIR / f"Business_Operational_Doctrine{suffix}.md"
    
    final_doctrine = "# Business & Marketing Operational Doctrine\n\n"
    final_doctrine += "\n\n".join(chapters_content)
    
    out_path.write_text(final_doctrine, encoding='utf-8')

    word_count = len(final_doctrine.split())
    print(f"\n{'═'*60}")
    print(f"✅ KÉSZ → {out_path}")
    print(f"   Szómennyiség: ~{word_count:,} szó")
    print(f"   (Map: ~{total_map_words:,} szó → Doctrine: ~{word_count:,} szó)")
    print(f"{'═'*60}")


if __name__ == "__main__":
    main()
