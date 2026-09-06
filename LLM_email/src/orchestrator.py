from datetime import datetime
from typing import List, Optional

from src.analyzer.groq_analyzer import GroqEmailAnalyzer
from src.config import AppSettings, load_accounts
from src.fetchers.base import BaseEmailFetcher
from src.fetchers.imap_fetcher import ImapEmailFetcher
from src.fetchers.graph_fetcher import GraphEmailFetcher
from src.models import AccountConfig, DailyDigest, ProcessedEmail, RawEmail
from src.notifier.pushbullet import PushbulletNotifier
from src.storage.db import EmailDatabase


class EmailOrchestrator:
    """Napi munkafolyamat koordinátor: lekérés, szűrés, AI elemzés, mentés és értesítés."""

    def __init__(self, settings: AppSettings):
        self.settings = settings
        self.db = EmailDatabase(settings.db_path)
        self.analyzer = GroqEmailAnalyzer(
            api_key=settings.groq_api_key,
            model=settings.groq_model,
        )
        self.notifier = PushbulletNotifier(access_token=settings.pushbullet_access_token)

    def _get_fetcher_for_account(self, account: AccountConfig) -> BaseEmailFetcher:
        if account.provider == "imap":
            return ImapEmailFetcher(account)
        elif account.provider in ["graph", "microsoft"]:
            return GraphEmailFetcher(account)
        raise ValueError(f"Nem támogatott provider: {account.provider}")

    def run_daily_workflow(
        self,
        accounts: Optional[List[AccountConfig]] = None,
        dry_run: bool = False,
        force_notify_even_empty: bool = False,
    ) -> DailyDigest:
        """Lefuttatja a teljes napi email figyelési és elemzési folyamatot."""
        active_accounts = accounts if accounts is not None else load_accounts(self.settings.accounts_file)

        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Napi folyamat indítása...")
        print(f"Aktív fiókok száma: {len(active_accounts)}")

        all_raw_emails: List[RawEmail] = []
        total_scanned = 0

        for acc in active_accounts:
            if not acc.enabled:
                continue

            print(f"--> Emailek lekérése a(z) '{acc.name}' fiókból...")
            try:
                fetcher = self._get_fetcher_for_account(acc)
                recent = fetcher.fetch_recent_emails(hours=acc.fetch_hours)
                total_scanned += len(recent)
                print(f"    Talált levél az elmúlt {acc.fetch_hours} órából: {len(recent)}")

                # Kiszűrjük a már feldolgozottakat
                msg_ids = [m.message_id for m in recent]
                unprocessed_ids = self.db.filter_unprocessed_ids(msg_ids)
                unprocessed = [m for m in recent if m.message_id in unprocessed_ids]
                print(f"    Új, még feldolgozatlan levél: {len(unprocessed)}")
                all_raw_emails.extend(unprocessed)
            except Exception as e:
                print(f"[ERROR] Hiba a(z) '{acc.name}' fiók feldolgozásakor: {e}")

        # AI Elemzés
        processed_emails: List[ProcessedEmail] = []
        if all_raw_emails:
            print(f"\nAI elemzés indítása {len(all_raw_emails)} új levélre a Groq segítségével...")
            for i, raw in enumerate(all_raw_emails, 1):
                print(f"  [{i}/{len(all_raw_emails)}] Elemzés: {raw.subject[:40]}...")
                analysis = self.analyzer.analyze_email(raw)
                processed_emails.append(ProcessedEmail(raw=raw, analysis=analysis))

            if self.analyzer.session_tokens_used > 0:
                limits = self.analyzer.last_rate_limits
                print(f"\n📊 Groq API felhasználás ebben a futásban:")
                print(f"   • Felhasznált tokenek: {self.analyzer.session_tokens_used:,} token ({self.analyzer.session_requests_used} kérés)")
                if limits:
                    print(f"   • Hátralévő kérés keret: {limits.get('remaining_requests')}/{limits.get('limit_requests')} (reset: {limits.get('reset_requests')})")
                    print(f"   • Hátralévő token/perc: {limits.get('remaining_tokens')}/{limits.get('limit_tokens')} (reset: {limits.get('reset_tokens')})")

        # Napi összesítő generálása
        digest_text = self.analyzer.generate_daily_digest(processed_emails)
        urgent_count = sum(1 for p in processed_emails if p.analysis.urgency in ["kritikus", "magas"])

        digest = DailyDigest(
            generated_at=datetime.now(),
            total_scanned=total_scanned,
            total_new=len(processed_emails),
            urgent_count=urgent_count,
            processed_emails=processed_emails,
            digest_text=digest_text,
        )

        print("\n--- ÖSSZESÍTŐ JELENTÉS ---")
        print(digest_text)
        print("--------------------------\n")

        # Pushbullet küldés
        if processed_emails or force_notify_even_empty:
            title = f"📬 Napi Email Összesítő ({len(processed_emails)} új levél)"
            if urgent_count > 0:
                title = f"🚨 {urgent_count} Sürgős! " + title

            if not dry_run:
                self.notifier.send_push(title=title, body=digest_text)
            else:
                print("[DRY-RUN] Pushbullet értesítés küldése kihagyva.")
        else:
            print("[INFO] Nem érkezett új levél, Pushbullet értesítés nem szükséges.")

        # Mentés adatbázisba
        if not dry_run and processed_emails:
            self.db.save_processed_emails(processed_emails)
            print(f"[INFO] {len(processed_emails)} levél állapota elmentve az adatbázisba.")
        elif dry_run:
            print("[DRY-RUN] Adatbázis mentés kihagyva.")

        return digest
