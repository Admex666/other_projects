import email
from email.header import decode_header
import email.utils
import hashlib
import imaplib
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple
from bs4 import BeautifulSoup

from src.fetchers.base import BaseEmailFetcher
from src.models import RawEmail


def decode_mime_words(header_value: Optional[str]) -> str:
    """Dekódolja a MIME fejléc szövegeket (pl. subject, from)."""
    if not header_value:
        return ""
    decoded_fragments = []
    for fragment, encoding in decode_header(header_value):
        if isinstance(fragment, bytes):
            try:
                decoded_fragments.append(fragment.decode(encoding or "utf-8", errors="replace"))
            except LookupError:
                decoded_fragments.append(fragment.decode("utf-8", errors="replace"))
        else:
            decoded_fragments.append(str(fragment))
    return "".join(decoded_fragments)


def extract_body_text(msg: email.message.Message) -> str:
    """Kinyeri a tiszta szöveges tartalmat az email üzenetből (text/plain vagy text/html)."""
    text_parts: List[str] = []
    html_parts: List[str] = []

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition", ""))
            if "attachment" in content_disposition:
                continue

            try:
                payload = part.get_payload(decode=True)
                if not payload:
                    continue
                charset = part.get_content_charset() or "utf-8"
                text = payload.decode(charset, errors="replace")
                if content_type == "text/plain":
                    text_parts.append(text)
                elif content_type == "text/html":
                    html_parts.append(text)
            except Exception:
                continue
    else:
        content_type = msg.get_content_type()
        try:
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or "utf-8"
                text = payload.decode(charset, errors="replace")
                if content_type == "text/plain":
                    text_parts.append(text)
                elif content_type == "text/html":
                    html_parts.append(text)
        except Exception:
            pass

    raw_text = ""
    if text_parts:
        raw_text = "\n".join(text_parts)
    elif html_parts:
        soup = BeautifulSoup("\n".join(html_parts), "html.parser")
        # Remove scripts and styles
        for s in soup(["script", "style"]):
            s.decompose()
        raw_text = soup.get_text(separator="\n")

    # Clean whitespace and lines
    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
    cleaned = "\n".join(lines)
    # Truncate at 5000 chars to avoid giant token consumption
    return cleaned[:5000]


class ImapEmailFetcher(BaseEmailFetcher):
    """IMAP protokoll alapú email begyűjtő."""

    def _connect(self) -> imaplib.IMAP4:
        server = self.account.imap_server
        if not server:
            raise ValueError(f"Nincs IMAP szerver beállítva a(z) '{self.account.name}' fiókhoz.")

        if self.account.use_ssl:
            client = imaplib.IMAP4_SSL(server, self.account.imap_port)
        else:
            client = imaplib.IMAP4(server, self.account.imap_port)

        client.login(self.account.username, self.account.password)
        return client

    def test_connection(self) -> bool:
        """Ellenőrzi, hogy a fiók sikeresen fel tud-e jelentkezni az IMAP szerverre."""
        try:
            client = self._connect()
            client.logout()
            return True
        except Exception as e:
            print(f"[ERROR] IMAP kapcsolódási hiba ({self.account.name}): {e}")
            return False

    def fetch_recent_emails(self, hours: Optional[int] = None) -> List[RawEmail]:
        """Lekéri az elmúlt megadott órában érkezett leveleket."""
        fetch_hours = hours or self.account.fetch_hours or 24
        since_date = datetime.now(timezone.utc) - timedelta(hours=fetch_hours)
        date_str = since_date.strftime("%d-%b-%Y")

        emails: List[RawEmail] = []
        try:
            client = self._connect()
            client.select(self.account.folder, readonly=True)

            # IMAP SINCE keresés
            status, response = client.search(None, f'(SINCE "{date_str}")')
            if status != "OK" or not response[0]:
                client.logout()
                return []

            msg_ids = response[0].split()
            for msg_id in msg_ids:
                try:
                    fetch_status, msg_data = client.fetch(msg_id, "(RFC822)")
                    if fetch_status != "OK" or not msg_data:
                        continue

                    raw_bytes = msg_data[0][1]
                    msg = email.message_from_bytes(raw_bytes)

                    # Message-ID
                    raw_msg_id = msg.get("Message-ID")
                    sender = decode_mime_words(msg.get("From", ""))
                    subject = decode_mime_words(msg.get("Subject", "(Nincs tárgy)"))
                    date_header = msg.get("Date")

                    parsed_date = datetime.now(timezone.utc)
                    if date_header:
                        try:
                            parsed_date = email.utils.parsedate_to_datetime(date_header)
                        except Exception:
                            pass

                    # Filter out messages strictly older than the requested time window
                    if parsed_date < since_date:
                        continue

                    if not raw_msg_id:
                        # Fallback hash
                        hash_src = f"{self.account.id}_{sender}_{subject}_{parsed_date.isoformat()}"
                        raw_msg_id = hashlib.sha256(hash_src.encode("utf-8")).hexdigest()
                    else:
                        raw_msg_id = raw_msg_id.strip()

                    body_text = extract_body_text(msg)

                    emails.append(
                        RawEmail(
                            message_id=raw_msg_id,
                            account_id=self.account.id,
                            account_name=self.account.name,
                            default_category=self.account.category,
                            sender=sender,
                            recipient=decode_mime_words(msg.get("To", "")),
                            subject=subject,
                            date=parsed_date,
                            body_text=body_text,
                        )
                    )
                except Exception as ex:
                    print(f"[WARN] Hiba egy levél feldolgozásakor ({self.account.name}, id={msg_id}): {ex}")

            client.logout()
        except Exception as e:
            print(f"[ERROR] Hiba az IMAP lekérés során ({self.account.name}): {e}")

        return emails
