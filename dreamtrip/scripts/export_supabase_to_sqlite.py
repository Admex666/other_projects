"""
Optivoya — Supabase to SQLite Full Database Exporter
Lekéri a Supabase felhőben lévő összes adatbázis táblát (beta_users, telemetry_events, user_sessions stb.),
és lementi őket egy helyi SQLite (.db) adatbázisfájlba.

Használat:
    python scripts/export_supabase_to_sqlite.py
    python scripts/export_supabase_to_sqlite.py --output data/my_backup.db
"""
import sys
import os
import json
import sqlite3
import argparse
from typing import List, Dict, Any

# Root hozzáadása a python path-hoz
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.supabase import get_supabase, is_supabase_configured, get_supabase_config

# Alapértelmezett táblák listája (ha az automatikus felderítés korlátozott)
DEFAULT_TABLES = [
    "beta_users",
    "user_sessions",
    "telemetry_events"
]

def discover_tables(sb) -> List[str]:
    """Megpróbálja felderíteni a nyilvános táblákat, vagy visszaadja az ismert táblákat."""
    discovered = list(DEFAULT_TABLES)
    
    # Próbálkozás a postgrest schema endpoint-tal
    try:
        import requests
        url, key = get_supabase_config()
        headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}"
        }
        resp = requests.get(f"{url}/rest/v1/", headers=headers, timeout=5)
        if resp.status_code == 200:
            openapi_spec = resp.json()
            definitions = openapi_spec.get("definitions", {})
            for table_name in definitions.keys():
                if table_name not in discovered and not table_name.startswith("_"):
                    discovered.append(table_name)
    except Exception:
        pass
        
    return discovered

def fetch_all_rows(sb, table_name: str, batch_size: int = 1000) -> List[Dict[str, Any]]:
    """Lapozva lekéri a tábla összes rekordját a Supabase API-n keresztül."""
    all_rows = []
    offset = 0
    
    while True:
        try:
            res = sb.table(table_name).select("*").range(offset, offset + batch_size - 1).execute()
            rows = res.data or []
            if not rows:
                break
            all_rows.extend(rows)
            if len(rows) < batch_size:
                break
            offset += batch_size
        except Exception as e:
            # Ha a tábla nem létezik vagy nincs rá olvasási jog
            if "relation" in str(e).lower() or "not found" in str(e).lower() or "404" in str(e):
                print(f"  [!] '{table_name}' tábla nem található a Supabase-ben, kihagyva.")
            else:
                print(f"  [!] Hiba a(z) '{table_name}' tábla lekérésekor: {e}")
            return []
            
    return all_rows

def infer_sqlite_type(value: Any) -> str:
    """Típus következtetés SQLite oszlophoz."""
    if value is None:
        return "TEXT"
    if isinstance(value, bool):
        return "INTEGER"
    if isinstance(value, int):
        return "INTEGER"
    if isinstance(value, float):
        return "REAL"
    return "TEXT"

def dump_supabase_to_sqlite(output_path: str = None, tables: List[str] = None):
    print("=" * 65)
    print("   SUPABASE -> SQLITE TELJES ADATBÁZIS EXPORTÁLÓ")
    print("=" * 65)

    if not is_supabase_configured():
        print("\n[HIBA] A Supabase nincs konfigurálva a .env fájlban!")
        print("Kérlek ellenőrizd a SUPABASE_URL és SUPABASE_KEY értékeket.")
        return False

    url, _ = get_supabase_config()
    print(f"\n[INFO] Kapcsolódás a Supabase felhőhöz: {url}")
    sb = get_supabase()
    if not sb:
        print("[HIBA] Nem sikerült inicializálni a Supabase klienst.")
        return False

    if not output_path:
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        os.makedirs(data_dir, exist_ok=True)
        output_path = os.path.join(data_dir, "supabase_dump.db")

    # Ha már létezik a fájl, töröljük az újratöltés előtt
    if os.path.exists(output_path):
        try:
            os.remove(output_path)
            print(f"[INFO] Korábbi mentés fájl törölve: {output_path}")
        except Exception as e:
            print(f"[FIGYELEM] Nem sikerült törölni a korábbi fájlt ({e}), felülírás lesz.")

    conn = sqlite3.connect(output_path)
    cursor = conn.cursor()

    target_tables = tables or discover_tables(sb)
    print(f"[INFO] Vizsgált táblák: {', '.join(target_tables)}")
    print(f"[INFO] Cél SQLite fájl: {output_path}\n")

    total_tables_exported = 0
    total_rows_exported = 0

    for table_name in target_tables:
        print(f"--> '{table_name}' tábla letöltése...", end=" ", flush=True)
        rows = fetch_all_rows(sb, table_name)
        
        if not rows:
            print("(0 sor)")
            continue

        print(f"Sikeres ({len(rows)} sor). SQLite tábla létrehozása...", end=" ", flush=True)

        # Oszlopok és típusok felderítése az összes sorból
        columns = {}
        for row in rows:
            for k, v in row.items():
                if k not in columns:
                    columns[k] = infer_sqlite_type(v)
                elif columns[k] == "TEXT" and v is not None:
                    # Marad TEXT
                    pass
                elif columns[k] == "INTEGER" and isinstance(v, float):
                    columns[k] = "REAL"

        # CREATE TABLE összeállítása
        cols_def = []
        for col_name, col_type in columns.items():
            # Ha 'id' vagy 'event_id' vagy 'session_id' a táblában, jelölhetjük, de általános TEXT/INT típus a legbiztonságosabb
            cols_def.append(f'"{col_name}" {col_type}')
            
        create_sql = f'CREATE TABLE IF NOT EXISTS "{table_name}" ({", ".join(cols_def)});'
        cursor.execute(create_sql)

        # INSERT összeállítása
        col_names = list(columns.keys())
        placeholders = ", ".join(["?"] * len(col_names))
        quoted_cols = ", ".join([f'"{c}"' for c in col_names])
        insert_sql = f'INSERT INTO "{table_name}" ({quoted_cols}) VALUES ({placeholders})'

        batch_values = []
        for row in rows:
            row_vals = []
            for col in col_names:
                val = row.get(col)
                if isinstance(val, (dict, list)):
                    # JSON mezők sorosítása szöveggé SQLite-hoz
                    val = json.dumps(val, ensure_ascii=False)
                elif isinstance(val, bool):
                    val = 1 if val else 0
                row_vals.append(val)
            batch_values.append(row_vals)

        cursor.executemany(insert_sql, batch_values)
        conn.commit()
        print(f"KÉSZ.")
        
        total_tables_exported += 1
        total_rows_exported += len(rows)

    conn.close()

    file_size_kb = os.path.getsize(output_path) / 1024 if os.path.exists(output_path) else 0

    print("\n" + "=" * 65)
    print("   EXPORT SIKERESEN BEFEJEZŐDÖTT!")
    print(f"   Táblák száma:      {total_tables_exported}")
    print(f"   Összes rekord:     {total_rows_exported} db")
    print(f"   Létrehozott fájl:  {output_path} ({file_size_kb:.1f} KB)")
    print("=" * 65)
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Supabase teljes adatbázis exportálása helyi SQLite .db fájlba")
    parser.add_argument("--output", "-o", type=str, default=None, help="Cél .db fájl elérési útja (alapértelmezett: data/supabase_dump.db)")
    parser.add_argument("--tables", "-t", nargs="+", default=None, help="Csak adott táblák exportálása (pl. --tables beta_users telemetry_events)")
    args = parser.parse_args()

    dump_supabase_to_sqlite(output_path=args.output, tables=args.tables)
