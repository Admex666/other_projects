from __future__ import annotations
from beanie import Document
from pydantic import BaseModel, Field, computed_field
from typing import Dict, Optional

class SubAccountDetails(BaseModel):
    balance: float
    currency: str = Field("HUF", description="Az alszámla devizaneme (pl. HUF, EUR, USD)")

class AccountDetails(BaseModel):
    alszamlak: Dict[str, SubAccountDetails] = Field(default_factory=dict) # Az alszamlak most SubAccountDetails-t tárolnak

    @computed_field
    @property
    def foosszeg(self) -> float:
        # Itt kellene valamilyen logikát implementálni, ha a főösszeget több devizából kell számolni
        # Például: visszaadhat egy Dict[str, float]-ot, ahol a kulcs a deviza, az érték pedig az összeg.
        # Egyszerűség kedvéért most csak az HUF összegeket adom össze, vagy ha nincs deviza megadva
        total_huf = 0.0
        for sub_account in self.alszamlak.values():
            if sub_account.currency == "HUF": # Ideiglenes megoldás, csak HUF-ra
                total_huf += sub_account.balance
            elif sub_account.currency == "EUR":
                total_huf += sub_account.balance * 400
            elif sub_account.currency == "USD":
                total_huf += sub_account.balance * 345 
            # Később itt lehetne devizaátváltást végezni, ha szükséges
        return total_huf

class UserAccounts(BaseModel):
    likvid: AccountDetails
    befektetes: AccountDetails
    megtakaritas: AccountDetails

class AllUserAccountsDocument(Document):
    accounts_by_user: Dict[str, UserAccounts] = Field(default_factory=dict, alias="accounts")

    class Settings:
        name = "accounts"