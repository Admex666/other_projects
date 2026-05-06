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
import pandas as pd
from groq import Groq
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── CONFIG ─────────────────────────────────────────────────────────────────
VAULT_PATH       = r"E:\obsidian_safe\obsidian_safe"
CLUSTERS_CSV     = "vault_clusters.csv"
BIZ_CLUSTERS     = [0, 3, 5, 12]
CHUNK_SIZE       = 12
OUTPUT_DIR       = Path("output")
CHUNKS_DIR       = OUTPUT_DIR / "chunks"
MODEL            = "llama-3.3-70b-versatile"
MAX_NOTE_CHARS   = 8000
SLEEP_BETWEEN    = 3.5
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


# ── API CALL WITH RETRY ─────────────────────────────────────────────────────
def call_groq(client: Groq, system: str, user: str, temperature: float = 0.6,
              max_tokens: int = 8192) -> str:
    for attempt in range(1, MAX_RETRIES + 1):
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
            return response.choices[0].message.content
        except Exception as e:
            err = str(e)
            if '429' in err or 'rate_limit' in err.lower():
                m = re.search(r'please try again in ([0-9.]+)s', err, re.IGNORECASE)
                wait = float(m.group(1)) + 2 if m else 30 * attempt
                if attempt < MAX_RETRIES:
                    print(f"\n  [429] Rate limit — várakozás {wait:.0f}s... ({attempt}/{MAX_RETRIES})",
                          flush=True)
                    time.sleep(wait)
                else:
                    print(f"\n❌ {MAX_RETRIES} próbálkozás után sem sikerült.")
                    raise
            else:
                raise
    return ""


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


def map_chunk(client: Groq, chunk_idx: int, notes: list[dict]) -> str:
    CHUNKS_DIR.mkdir(parents=True, exist_ok=True)
    out_file = CHUNKS_DIR / f"chunk_{chunk_idx:03d}.md"

    if out_file.exists():
        print(f"  [SKIP] chunk_{chunk_idx:03d}.md már létezik, kihagyva.")
        return out_file.read_text(encoding='utf-8')

    notes_block = ""
    for i, note in enumerate(notes, 1):
        content = read_note(note['path'])
        fname = Path(note['filename']).stem[:80]
        notes_block += f"\n{'─'*60}\n### NOTE {i}: {fname}\n{'─'*60}\n{content}\n"

    user = MAP_USER_TEMPLATE.format(n=len(notes), notes_block=notes_block)

    print(f"  → Chunk {chunk_idx:03d} ({len(notes)} fájl)...", end=" ", flush=True)
    dossier = call_groq(client, MAP_SYSTEM, user, temperature=TEMP_MAP, max_tokens=8192)
    out_file.write_text(dossier, encoding='utf-8')
    words = len(dossier.split())
    print(f"✓ ({words} szó → {out_file.name})")
    return dossier


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


def run_synthesis(client: Groq, dossiers: list[str]) -> str:
    print("\n[PHASE 2 — SYNTHESIS] Mélystruktúra-elemzés...", flush=True)
    syn_path = OUTPUT_DIR / "synthesis_layer.md"

    if syn_path.exists():
        print("  [SKIP] synthesis_layer.md már létezik, kihagyva.")
        return syn_path.read_text(encoding='utf-8')

    block = ""
    for i, d in enumerate(dossiers, 1):
        block += f"\n{'═'*60}\n### DOSSIER {i}\n{'═'*60}\n{d}\n"

    # Ha a teljes blokk túl hosszú, rövidítsük a dossier-ket
    if len(block) > 90000:
        block = ""
        for i, d in enumerate(dossiers, 1):
            short = d[:3000] + "\n...[rövidítve]" if len(d) > 3000 else d
            block += f"\n{'═'*60}\n### DOSSIER {i}\n{'═'*60}\n{short}\n"

    user = SYNTHESIS_USER_TEMPLATE.format(n=len(dossiers), dossiers_block=block)
    result = call_groq(client, SYNTHESIS_SYSTEM, user, temperature=TEMP_SYNTHESIS, max_tokens=6000)
    syn_path.write_text(result, encoding='utf-8')
    print(f"  ✓ Synthesis layer kész ({len(result.split())} szó → {syn_path.name})")
    return result


# ── PHASE 3: REDUCE ────────────────────────────────────────────────────────
REDUCE_SYSTEM = """\
Te egy üzleti operációs rendszer tervezője vagy — NEM könyv-összefoglaló generátor.

A feladatod: egy koherens, végrehajtható üzleti Operational Doctrine-t alkotni
a rendelkezésre álló tudás-dossier-ekből és a szintézis-elemzésből.

EZ NEM ÖSSZEFOGLALÁS. EZ RENDSZERÉPÍTÉS.

A DOCTRINE MEGALKOTÁSÁNAK ELVEI:

1. OPERÁCIÓS LOGIKA — nem motiváció
   Minden fejezet tartalmazzon:
   - Döntési szabályokat (Ha X, akkor Y — ha Z, akkor W)
   - Trigger-condition logikát (Mikor lép életbe? Mi az aktiváló feltétel?)
   - Prioritási elveket (Mi az előfeltétele minek?)
   - Végrehajtható workflow-kat (Lépések sorrendben)
   - Anti-patterneket (Mit NE csinálj és miért csábító mégis)

2. KAUZÁLIS MAGYARÁZATOK — nem listák
   Minden fő koncepciónál:
   - Miből következik ez az elv?
   - Mit befolyásol, ha alkalmazzuk?
   - Milyen életciklusban kritikus (korai fázis vs. skálázás)?
   - Milyen trade-offokat hoz létre?
   - Mi az input és mi az output?

3. EMERGENS MODELLEK — nem kategóriák
   Az ismétlődő elveket vond össze magasabb szintű mintázatokba,
   de ŐRIZD MEG az egyedi implementációs különbségeket.
   Minden emergens modellnél magyarázd, miért erősebb a részeinél.

4. RELATIONSHIP GRAPH VERBÁLISAN
   Minden fejezet végén: "Kapcsolatok más fejezetekkel" szekció.
   Mi erősíti? Mi az előfeltétele? Mi következik belőle?

STRUKTÚRA:
- Vezetői összefoglaló: az operációs rendszer lényege 3 mondatban
- 5-8 fejezet (nem tematikus listák — operációs modulok)
- Minden fejezet: Elv → Mechanizmus → Trigger → Workflow → Anti-pattern → Kapcsolatok
- Záró: "Operational Playbook" — 4 hetes végrehajtási terv, heti szintű lépésekkel
- "10 Invariáns Törvény" — az a 10 elv, ami minden körülmény között igaz

CÉLZOTT TERJEDELEM: 3500–5000 szó.
NE generálj motivációs szöveget. Generálj operational logic-ot.\
"""

REDUCE_USER_TEMPLATE = """\
BEMENET:
- {n_dossiers} Knowledge Extraction Dossier chunk-ból
- 1 Stratégiai Szintézis-Elemzésből (thinking layer)

A SZINTÉZIS-ELEMZÉS (thinking layer):
{'═'*60}
{synthesis}
{'═'*60}

A KNOWLEDGE DOSSIER-EK:
{dossiers_block}

Most alkotd meg a Business & Marketing Operational Doctrine-t (3500–5000 szó):\
"""


def reduce_to_doctrine(client: Groq, dossiers: list[str], synthesis: str) -> str:
    print("\n[PHASE 3 — REDUCE] Operational Doctrine generálása...", flush=True)

    dossiers_block = ""
    for i, d in enumerate(dossiers, 1):
        dossiers_block += f"\n{'─'*60}\n#### DOSSIER {i}\n{'─'*60}\n{d}\n"

    total_len = len(synthesis) + len(dossiers_block)

    # Ha túl hosszú, rövidítsük a dossier-ket (a synthesis-t MINDIG megőrizzük)
    if total_len > 90000:
        print(f"  ⚠️  Bemeneti tartalom hosszú ({total_len} kar.) — dossier-ek rövidítése...")
        dossiers_block = ""
        for i, d in enumerate(dossiers, 1):
            short = d[:3500] + "\n...[rövidítve]" if len(d) > 3500 else d
            dossiers_block += f"\n{'─'*60}\n#### DOSSIER {i}\n{'─'*60}\n{short}\n"

    user = (
        f"BEMENET:\n- {len(dossiers)} Knowledge Extraction Dossier chunk-ból\n"
        f"- 1 Stratégiai Szintézis-Elemzésből (thinking layer)\n\n"
        f"A SZINTÉZIS-ELEMZÉS (thinking layer):\n{'═'*60}\n{synthesis}\n{'═'*60}\n\n"
        f"A KNOWLEDGE DOSSIER-EK:\n{dossiers_block}\n\n"
        f"Most alkotd meg a Business & Marketing Operational Doctrine-t (3500–5000 szó):"
    )

    return call_groq(client, REDUCE_SYSTEM, user, temperature=TEMP_REDUCE, max_tokens=8192)


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

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("❌ HIBA: Nem található GROQ_API_KEY a .env fájlban!")
        print("   Regisztrálj: https://console.groq.com → API Keys → Create API Key")
        sys.exit(1)

    client = Groq(api_key=api_key)
    print(f"✅ Groq — {MODEL}\n")

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
            dossier = map_chunk(client, idx, chunk)
            dossiers.append(dossier)
            if idx < len(chunks) - 1:
                time.sleep(SLEEP_BETWEEN)

    total_map_words = sum(len(d.split()) for d in dossiers)
    print(f"\n[PHASE 1 KÉSZ] {len(dossiers)} dossier — összesen ~{total_map_words:,} szó")

    # ── PHASE 2: SYNTHESIS ────────────────────────────────────────────────
    if args.skip_synthesis:
        synthesis = "(Synthesis fázis kihagyva)"
        print("\n[PHASE 2 — SYNTHESIS] Kihagyva (--skip-synthesis)")
    else:
        synthesis = run_synthesis(client, dossiers)
        time.sleep(SLEEP_BETWEEN)

    # ── PHASE 3: REDUCE ───────────────────────────────────────────────────
    doctrine = reduce_to_doctrine(client, dossiers, synthesis)

    suffix = f"_first{args.limit}" if (args.limit > 0 and not args.reduce_only) else "_full"
    out_path = OUTPUT_DIR / f"Business_Operational_Doctrine{suffix}.md"
    out_path.write_text(doctrine, encoding='utf-8')

    word_count = len(doctrine.split())
    print(f"\n{'═'*60}")
    print(f"✅ KÉSZ → {out_path}")
    print(f"   Szómennyiség: ~{word_count:,} szó")
    print(f"   (Map: ~{total_map_words:,} szó → Doctrine: ~{word_count:,} szó)")
    print(f"{'═'*60}")


if __name__ == "__main__":
    main()
