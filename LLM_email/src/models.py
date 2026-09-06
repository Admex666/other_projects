from datetime import datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, Field


EmailCategory = Literal["személyes", "munka", "egyetem", "projekt", "egyéb"]
UrgencyLevel = Literal["kritikus", "magas", "közepes", "alacsony"]
ImportanceLevel = Literal["kiemelt", "normál", "alacsony"]


class AccountConfig(BaseModel):
    id: str
    name: str
    category: EmailCategory = "egyéb"
    provider: str = "imap" # "imap" vagy "graph"
    imap_server: Optional[str] = None
    imap_port: int = 993
    use_ssl: bool = True
    username: str
    password: Optional[str] = None
    folder: str = "INBOX"
    fetch_hours: int = 24
    enabled: bool = True
    # Microsoft Graph specifikus beállítások
    client_id: Optional[str] = None
    tenant_id: Optional[str] = "organizations"


class RawEmail(BaseModel):
    message_id: str
    account_id: str
    account_name: str
    default_category: EmailCategory = "egyéb"
    sender: str
    recipient: str = ""
    subject: str
    date: datetime
    body_text: str


class EmailAnalysis(BaseModel):
    category: EmailCategory = "egyéb"
    urgency: UrgencyLevel = "közepes"
    importance: ImportanceLevel = "normál"
    summary: str = Field(description="Rövid, lényegretörő magyar nyelvű összefoglaló 1-2 mondatban.")
    action_items: List[str] = Field(default_factory=list, description="A levélből kinyert konkrét teendők.")
    deadlines: List[str] = Field(default_factory=list, description="A levélben említett konkrét határidők vagy időpontok.")


class ProcessedEmail(BaseModel):
    raw: RawEmail
    analysis: EmailAnalysis


class DailyDigest(BaseModel):
    generated_at: datetime = Field(default_factory=datetime.now)
    total_scanned: int = 0
    total_new: int = 0
    urgent_count: int = 0
    processed_emails: List[ProcessedEmail] = Field(default_factory=list)
    digest_text: str = ""
