from __future__ import annotations
from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field
from typing import Optional, Dict

class AccountDetails(BaseModel):
    foosszeg: float
    crypto: Optional[float] = None
    lakas: Optional[float] = None

class UserAccounts(BaseModel):
    likvid: AccountDetails
    befektetes: AccountDetails
    megtakaritas: AccountDetails

# Ez a modell reprezentálja az EGYETLEN dokumentumot az 'accounts' kollekcióban
class AllUserAccountsDocument(Document):
    # Az _id mező tetszőleges lehet, nem a user_id. Pl. ha van egyetlen dokumentum az "accounts" kollekcióban.
    # Ha nincs értelmes _id, hagyhatja PydanticObjectId-nak, a Beanie generál egyet.
    # De ha van egy fix _id (pl. "main_accounts_doc"), akkor azt megadhatja:
    # id: str = Field(alias="_id", default="main_accounts_doc")
    # Vagy hagyhatjuk, hogy a Beanie kezelje az _id-t, ha ez egy egyetlen dokumentum.
    # Mivel a db_sample.py-ban az _id is egy random string, nem user_id,
    # egyszerűen kihagyjuk az _id alias-t, és hagyjuk, hogy a Beanie kezelje.
    
    # A fő számla adatok, ahol a kulcs a felhasználó ID-je (stringként)
    accounts_by_user: Dict[str, UserAccounts] = Field(..., alias="accounts") # Az "accounts" kulcsot használjuk, mint a db_sample.py-ban

    class Settings:
        name = "accounts" # Ez a kollekció neve a MongoDB-ben
        # Ha egyetlen dokumentum van, és mindig azt akarjuk lekérdezni:
        # keep_doc_order = True # Nem igazán releváns itt