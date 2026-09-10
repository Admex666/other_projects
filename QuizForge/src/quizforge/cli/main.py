"""QuizForge parancssori felület (CLI)."""

import argparse
import json
import sys
from pathlib import Path

# Gyökér és src hozzáadása a path-hoz
src_path = Path(__file__).resolve().parent.parent.parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from quizforge.core.config import settings
from quizforge.core.constants import Domain, QuestionMechanism
from quizforge.core.models import Entity, Relation
from quizforge.ingestion.mek import MEKIngestor
from quizforge.ingestion.quiz_sources import HungarianPubQuizSampleCorpus, OpenTriviaIngestor
from quizforge.ingestion.validator import SourceValidationPipeline
from quizforge.ingestion.wikidata import WikidataIngestor
from quizforge.ingestion.wikipedia import WikipediaIngestor
from quizforge.knowledge.graph import KnowledgeGraph
from quizforge.knowledge.relevance import RelevanceEngine
from quizforge.llm.groq_client import GroqClient
from quizforge.quiz_engine.generator import QuizGenerator
from quizforge.storage.db import DatabaseManager
from quizforge.storage.repositories import QuizQuestionRepository


def cmd_validate_sources(args):
    """Adatforrások validálása."""
    limit = getattr(args, "limit", 5) or 5
    pipeline = SourceValidationPipeline()
    pipeline.run_validation(sample_limit=limit)


def cmd_init_db(args):
    """DuckDB adatbázis és táblák inicializálása."""
    db = DatabaseManager()
    stats = db.get_stats()
    print("DuckDB sikeresen inicializálva:")
    for table, count in stats.items():
        print(f"  - {table}: {count} sor")
    db.close()


def cmd_sync_sources(args):
    """Adatok gyűjtése a forrásokból, mentés DuckDB Knowledge Graphba és export Parquet-ba."""
    db = DatabaseManager()
    kg = KnowledgeGraph(db)
    q_repo = QuizQuestionRepository(db)

    print("=" * 60)
    print("QuizForge - Tudásgráf szinkronizáció és Parquet export")
    print("=" * 60)

    # 1. Wikidata
    print("--> Wikidata SPARQL szinkronizáció...")
    w_ing = WikidataIngestor()
    nobel_data = w_ing.fetch_sample(limit=10)
    counties_data = w_ing.fetch_hungarian_counties(limit=20)
    e1, r1 = w_ing.extract_triplets(nobel_data + counties_data)
    e_seed, r_seed = w_ing.get_seed_curated_knowledge()
    kg.ingest_triplets(e1 + e_seed, r1 + r_seed)
    w_ing.close()
    print(f"    Wikidata & Curated: {len(e1) + len(e_seed)} entitás, {len(r1) + len(r_seed)} reláció hozzáadva.")

    # 2. Wikipédia
    print("--> Magyar Wikipédia szinkronizáció...")
    wiki_ing = WikipediaIngestor()
    wiki_data = wiki_ing.fetch_sample(limit=10)
    e2, r2 = wiki_ing.extract_triplets(wiki_data)
    kg.ingest_triplets(e2, r2)
    wiki_ing.close()
    print(f"    Wikipédia: {len(e2)} entitás, {len(r2)} reláció hozzáadva.")

    # 3. MEK
    print("--> OSZK MEK szinkronizáció...")
    mek_ing = MEKIngestor()
    mek_data = mek_ing.fetch_sample(limit=10)
    e3, r3 = mek_ing.extract_triplets(mek_data)
    kg.ingest_triplets(e3, r3)
    mek_ing.close()
    print(f"    MEK: {len(e3)} entitás, {len(r3)} reláció hozzáadva.")

    # 4. Kvízkérdések és kapcsolatok
    print("--> Magyar Kvíz Seed Korpusz betöltése...")
    seed_questions = HungarianPubQuizSampleCorpus.get_seed_questions()
    for q in seed_questions:
        q_repo.add_question(q)
    print(f"    Korpusz: {len(seed_questions)} kérdés eltárolva.")

    # 5. Magyar kvízrelevancia újraszámolása
    rel_engine = RelevanceEngine(db)
    updated = rel_engine.recalculate_relevance_scores()
    print(f"--> Magyar kvízrelevancia frissítve {updated} entitásra.")

    # 6. Parquet export
    print("--> Parquet táblák generálása (data/parquet/)...")
    db.export_to_parquet()
    print("    Parquet export kész!")

    stats = db.get_stats()
    print("\nAdatbázis aktuális állapota:")
    for table, count in stats.items():
        print(f"  - {table}: {count} sor")
    print("=" * 60)
    db.close()


def cmd_calc_relevance(args):
    """Magyar kvízrelevanciák kalkulációja és top entitások listázása."""
    db = DatabaseManager()
    rel_engine = RelevanceEngine(db)
    updated = rel_engine.recalculate_relevance_scores()
    top_entities = rel_engine.get_top_entities(limit=getattr(args, "limit", 10))

    print(f"\nRelevancia újraszámolva: {updated} entitás érintve.")
    print("\nTop Magyar Kvízrelevanciájú Entitások:")
    print(f"{'Név':<30} | {'Téma':<15} | {'Korpusz gyak.':<12} | {'Kapcsolatok':<12} | {'Quiz Score':<10}")
    print("-" * 88)
    for ent in top_entities:
        print(f"{ent['label']:<30} | {ent['domain']:<15} | {ent['corpus_freq']:<12} | {ent['degree']:<12} | {ent['quiz_score']:<10}")
    db.close()


def cmd_test_groq(args):
    """Groq API kapcsolat tesztelése kérdésgenerálással a Knowledge Graphból."""
    groq = GroqClient()
    print("=" * 60)
    print("QuizForge - Groq LLM Kliens Teszt")
    print("=" * 60)
    print(f"Groq elérhető: {groq.is_available}")
    print(f"Modell: {groq.model}")

    if not groq.is_available:
        print("FIGYELEM: GROQ_API_KEY nincs beállítva a .env fájlban vagy a környezetben!")
        return

    # Mintakérdés generálása egy létező tény alapján
    db = DatabaseManager()
    kg = KnowledgeGraph(db)
    
    # Keresünk egy valós relációt az adatbázisban
    row = db.conn.execute("""
        SELECT r.relation_id, r.relation_type,
               e_src.entity_id, e_src.label_hu, e_src.domain, e_src.subdomain,
               e_tgt.entity_id, e_tgt.label_hu, e_tgt.domain, e_tgt.subdomain
        FROM relations r
        JOIN entities e_src ON r.source_entity_id = e_src.entity_id
        JOIN entities e_tgt ON r.target_entity_id = e_tgt.entity_id
        LIMIT 1
    """).fetchone()

    if row:
        src = Entity(entity_id=row[2], label_hu=row[3], domain=Domain(row[4]), subdomain=row[5])
        tgt = Entity(entity_id=row[6], label_hu=row[7], domain=Domain(row[8]), subdomain=row[9])
        rel = Relation(relation_id=row[0], source_entity_id=row[2], target_entity_id=row[6], relation_type=row[1])

        distractors = kg.get_distractors(tgt.entity_id, domain=tgt.domain, subdomain=tgt.subdomain, count=3)
        print(f"\n1. Kiválasztott KG Triplet: [{src.label_hu}] --[{rel.relation_type}]--> [{tgt.label_hu}]")
        print(f"   Intelligens disztraktorok a KG-ből: {distractors}")

        print("\n2. Groq LLM megfogalmazás futtatása (Structured JSON)...")
        result = groq.formulate_question_from_triplet(
            source_entity=src,
            relation=rel,
            target_entity=tgt,
            mechanism=QuestionMechanism.ABCD,
            distractors=distractors
        )
        print("\nGenerált kérdés eredménye:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("Nincs még adat az adatbázisban, futtasd előbb: python src/quizforge/cli/main.py sync-sources")

    db.close()


def cmd_groq_quota(args):
    """A rendelkezésre álló GROQ API tokenek és kérések lekérdezése."""
    groq = GroqClient()
    print("=" * 60)
    print("QuizForge - Valós idejű GROQ API Token és Kvóta Lekérdezés")
    print("=" * 60)
    if not groq.is_available:
        print("FIGYELEM: GROQ_API_KEY nincs beállítva a .env fájlban vagy környezeti változóként!")
        return

    quota = groq.get_quota_status(force_refresh=True)
    if quota.get("error"):
        print(f"Hiba a lekérdezés során: {quota['error']}")
        return

    print(f"Modell: {groq.model}")
    print(f"Utolsó frissítés: {quota.get('last_updated', 'Most')}")
    print("-" * 60)
    print(f"  - Fennmaradó tokenek:  {quota.get('remaining_tokens', 'N/A')} / {quota.get('limit_tokens', 'N/A')}")
    print(f"  - Token reset idő:     {quota.get('reset_tokens', 'N/A')}")
    print(f"  - Fennmaradó kérések:  {quota.get('remaining_requests', 'N/A')} / {quota.get('limit_requests', 'N/A')}")
    print(f"  - Kérés reset idő:     {quota.get('reset_requests', 'N/A')}")
    print("=" * 60)


def cmd_generate_quiz(args):
    """Kvízkérdések automatikus generálása a Knowledge Graphból."""
    count = getattr(args, "count", 3) or 3
    domain_arg = getattr(args, "domain", None)
    target_domain = Domain(domain_arg) if domain_arg in [d.value for d in Domain] else None

    db = DatabaseManager()
    gen = QuizGenerator(db)
    groq = gen.groq

    print("=" * 60)
    print(f"QuizForge - Kvízkérdések generálása ({count} db, téma: {domain_arg or 'bármely'})")
    if groq.is_available:
        print(groq.format_quota_summary(force_refresh=True))
    print("=" * 60)

    generated = gen.generate_batch(count=count, domain=target_domain)
    for idx, q in enumerate(generated, 1):
        print(f"\n[{idx}. Kérdés] (Mechanizmus: {q.mechanism.value} | Téma: {q.domain.value})")
        print(f"Kérdés: {q.text}")
        if q.options:
            print(f"Válaszlehetőségek: {', '.join(q.options)}")
        print(f"Helyes válasz: {q.correct_answer}")
        print(f"Érintett entitások: {', '.join(q.entities)}")

    print("\n" + "=" * 60)
    print(f"Összesen {len(generated)} új kérdés generálva és elmentve a DuckDB-be!")
    if groq.is_available:
        print(groq.format_quota_summary(force_refresh=False))
    print("=" * 60)
    db.close()


def cmd_dashboard(args):
    """Streamlit webes felület indítása a böngészőben."""
    import subprocess
    app_file = str(settings.PROJECT_ROOT / "src" / "quizforge" / "ui" / "app.py")
    print(f"QuizForge Streamlit Web UI indítása ({app_file})...")
    subprocess.run([sys.executable, "-m", "streamlit", "run", app_file])


def cmd_ui(args):
    """Harlequin terminálos vizuális felület indítása a DuckDB adatbázishoz."""
    import subprocess
    db_file = str(settings.DUCKDB_PATH)
    print(f"Harlequin indítása a következő adatbázissal: {db_file}...")
    subprocess.run([sys.executable, "-m", "harlequin", db_file])


def main():
    parser = argparse.ArgumentParser(description="QuizForge - Adatvezérelt kvízfelkészítő platform")
    subparsers = parser.add_subparsers(dest="command", help="Választható parancsok")

    # validate-sources
    val_parser = subparsers.add_parser("validate-sources", help="Adatforrások elérhetőségének és minőségének tesztelése")
    val_parser.add_argument("--limit", type=int, default=5, help="Próbaminta mérete forrásonként (alapértelmezett: 5)")

    # init-db
    subparsers.add_parser("init-db", help="DuckDB adatbázis és táblák inicializálása")

    # sync-sources
    subparsers.add_parser("sync-sources", help="Források letöltése, KG építés és Parquet export")

    # calc-relevance
    rel_parser = subparsers.add_parser("calc-relevance", help="Magyar kvízrelevancia újraszámítása és top entitások listázása")
    rel_parser.add_argument("--limit", type=int, default=10, help="Megjelenítendő entitások száma")

    # test-groq
    subparsers.add_parser("test-groq", help="Groq LLM integráció tesztelése KG triplet kérdésgenerálással")

    # generate-quiz
    gen_parser = subparsers.add_parser("generate-quiz", help="Új kérdések generálása a tudásgráfból a Groq segítségével")
    gen_parser.add_argument("--count", type=int, default=3, help="Generálandó kérdések száma (alapértelmezett: 3)")
    gen_parser.add_argument("--domain", type=str, default=None, help="Témakör szűrés (pl. science_tech, literature, geography)")

    # groq-quota
    subparsers.add_parser("groq-quota", help="Valós idejű GROQ API token- és kéréskvóta lekérdezése")

    # dashboard (Streamlit)
    subparsers.add_parser("dashboard", help="Streamlit webes vizuális felület megnyitása a böngészőben")

    # ui (Harlequin)
    subparsers.add_parser("ui", help="Harlequin terminálos adatbázis felület megnyitása")

    args = parser.parse_args()

    commands = {
        "validate-sources": cmd_validate_sources,
        "init-db": cmd_init_db,
        "sync-sources": cmd_sync_sources,
        "calc-relevance": cmd_calc_relevance,
        "test-groq": cmd_test_groq,
        "groq-quota": cmd_groq_quota,
        "generate-quiz": cmd_generate_quiz,
        "dashboard": cmd_dashboard,
        "ui": cmd_ui,
    }

    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
