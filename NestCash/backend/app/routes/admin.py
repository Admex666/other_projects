from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import logging

from app.core.db import get_db
from app.models.user import UserDocument # Szükséges a UserDocument lekérdezéséhez

logger = logging.getLogger(__name__)

# Ez egy adminisztrációs route lehet, nem feltétlenül az accounts router része
admin_router = APIRouter(prefix="/admin", tags=["admin"])

@admin_router.post("/migrate-accounts")
async def migrate_account_keys(db: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Ez a végpont elvégzi a migrációt:
    Átnevezi a felhasználói számlák kulcsait az 'accounts' kollekció egyetlen dokumentumában
    a régi numerikus user_id-król az új UserDocument._id azonosítókra.
    """
    try:
        # 1. Lekérdezzük az accounts kollekció EGYETLEN dokumentumát
        accounts_doc = await db["accounts"].find_one()

        if not accounts_doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No master accounts document found.")

        current_accounts_data = accounts_doc.copy() # Másolat, amin dolgozunk
        updated_accounts_data = {}
        migration_performed = False

        # 2. Létrehozzuk a régi user_id és az új _id közötti megfeleltetést
        # EZ A KRITIKUS RÉSZ! Jelenleg nincs automatikus módja ennek a lekérésnek.
        # Ennek a szótárnak kellene összekapcsolnia a régi string ID-ket
        # az új ObjectId string ID-kkel.
        
        # PÉLDA: Hogyan kaphatja meg ezt a mapping-et (Válassza ki az Önhöz illő opciót):
        user_id_to_new_id_map = {}
        
        # --- OPCIÓ A: Ha a régi user_id megegyezik a username-mel ---
        # (Ez valószínűleg nem így van, ha "6" volt a user_id)
        # users = await UserDocument.find({}).to_list()
        # for user in users:
        #     if user.username.isdigit(): # feltételezve, hogy a régi user_id numerikus
        #         user_id_to_new_id_map[user.username] = str(user.id)
        
        # --- OPCIÓ B: Ha van valamilyen "legacy_id" mező a UserDocument-ben ---
        # (Nincs ilyen a jelenlegi UserDocument.py-ban, de hozzáadható lenne)
        # users = await UserDocument.find({}).to_list()
        # for user in users:
        #     if user.legacy_id:
        #         user_id_to_new_id_map[user.legacy_id] = str(user.id)

        # --- OPCIÓ C: MANUÁLIS MEGFELELTETÉS (valószínűleg a legrealisztikusabb) ---
        # Ezt a szótárt manuálisan kell feltöltenie a valós adatai alapján!
        # Pl. lekérdezheti az összes felhasználót és az összes régi kulcsot,
        # majd manuálisan párosítja őket.
        
        # Mivel nincs automatikus módja a programozott leképezésnek az aktuális UserDocument alapján,
        # feltételeznünk kell, hogy van egy 'legacy_id' mező a UserDocument-ben,
        # vagy a felhasználó valamilyen más módon adja meg ezt a leképezést.
        # A legbiztonságosabb, ha a felhasználó adja meg ezt a mapping-et.
        
        # Az alábbi sor egy placeholder. Ezt ki kell cserélnie a VALÓDI megfeleltetéssel!
        # Ahhoz, hogy a migráció sikeres legyen, ennek a szótárnak TARTALMAZNIA KELL
        # az ÖSSZES régi numerikus user_id-t kulcsként, és a hozzájuk tartozó
        # ÚJ UserDocument._id stringet értékként!
        
        # PÉLDA, ha az összes felhasználóhoz leképeztük (tegyük fel, hogy valahogy előállította ezt):
        all_users = await UserDocument.find({}).to_list()
        for user in all_users:
            # Ez egy PLACEHOLDER! Önnek kell tudnia, hogyan találja meg a régi ID-t a felhasználóhoz.
            # Ha a régi ID-k nem egyeznek meg a username-ekkel, és nincs külön legacy mező,
            # akkor EZT A RÉSZT ÖNNEK KELL KIDOLGOZNIA VAGY MANUÁLISAN MEGADNIA.
            # Például, ha van egy CSV-je a régi felhasználói ID-kről és az új _id-król.
            if hasattr(user, 'legacy_id') and user.legacy_id: # Feltételezi, hogy hozzáadott egy legacy_id mezőt
                user_id_to_new_id_map[str(user.legacy_id)] = str(user.id)
            # Ha a username volt a régi id:
            elif user.username.isdigit(): # Például, ha a "6" az username
                user_id_to_new_id_map[user.username] = str(user.id)
            # Ha nem tudjuk programmatikusan leképezni, akkor a mapping-et kívülről kell megadni
            # (pl. egy konfigurációs fájlból, vagy egy kérés paramétereként).
            # Mivel a `UserDocument` jelenleg nem tartalmazza a régi `user_id` mezőt,
            # a legvalószínűbb, hogy ezt manuálisan kell megadnia.
            
        logger.info(f"Generated user ID map: {user_id_to_new_id_map}")


        for old_id_key, account_data in list(current_accounts_data.items()): # list-re konvertálunk, mert módosítjuk a dict-et iterálás közben
            if old_id_key == "_id": # Kihagyjuk az _id mezőt
                updated_accounts_data["_id"] = account_data
                continue

            # Ellenőrizzük, hogy a kulcs régi "user_id" formátumú-e (pl. numerikus string)
            # Ezt a feltételt az Ön régi user_id formátumához kell igazítani!
            # Feltételezve, hogy a régi ID-k csupán számok stringként:
            if old_id_key.isdigit(): # Ez egy erős feltételezés, ellenőrizze!
                new_id_key = user_id_to_new_id_map.get(old_id_key)
                if new_id_key:
                    updated_accounts_data[new_id_key] = account_data
                    migration_performed = True
                    logger.info(f"Migrated account key from '{old_id_key}' to '{new_id_key}'")
                else:
                    logger.warning(f"Could not find new ID for old user ID '{old_id_key}'. Account data might be lost if not handled.")
                    # Döntés: Ha nem található megfeleltetés, mit tegyünk?
                    # - Meghagyjuk a régi kulccsal? (Lehet, hogy problémás, ha a frontend _id-t vár)
                    # - Kidobjuk? (Adatvesztés!)
                    # - Megtartjuk a régi kulccsal, de naplózzuk?
                    updated_accounts_data[old_id_key] = account_data # Ideiglenesen megtartjuk a régi kulccsal
            else:
                # Már új _id kulcs, vagy más típusú kulcs
                updated_accounts_data[old_id_key] = account_data

        if migration_performed:
            # Töröljük a régi kulcsokat az eredeti dokumentumból (ha nem volt átmásolva)
            # Ahogy most a kód van, az `updated_accounts_data` egy új dict,
            # így csak a régi `_id`-t és az új kulcsokat kell visszatenni.
            
            # FIGYELEM: Ez a logikája azt feltételezi, hogy az _id mező nem egy user_id.
            # Az MVP logikája alapján az _id valószínűleg egy generált ObjectId,
            # és az összes user_id a gyökérszintű kulcs.

            # Helyesebb megközelítés: Törölje a régi documentumot, és szúrja be az újat, VAGY
            # Módosítsa a meglévő documentumot az update_one-nal.

            # Ezt az update-et finomhangolni kell, hogy CSAK a változásokat írja vissza,
            # vagy a teljes dokumentumot lecserélje.
            
            # A legegyszerűbb, de potenciálisan kockázatos: lecseréli a teljes dokumentum tartalmát
            # (az _id kivételével, azt megőrizve)
            update_fields = {k: v for k, v in updated_accounts_data.items() if k != "_id"}
            
            # Töröljük a régi, nem _id kulcsokat, amik már nincsenek az update_fields-ben (ha átneveződtek)
            unset_fields = {}
            for old_key in accounts_doc.keys():
                if old_key != "_id" and old_key not in update_fields:
                    # Ha egy régi kulcs át lett nevezve, vagy el lett távolítva, akkor unseteljük
                    if old_key.isdigit() and user_id_to_new_id_map.get(old_id_key) is not None:
                        unset_fields[old_key] = "" # Unset operátorhoz kell
                        logger.info(f"Unsetting old key: {old_key}")


            update_operations = {}
            if update_fields:
                update_operations["$set"] = update_fields
            if unset_fields:
                update_operations["$unset"] = unset_fields

            if update_operations:
                await db["accounts"].update_one(
                    {"_id": accounts_doc["_id"]}, # Megtartjuk a dokumentum eredeti _id-jét
                    update_operations
                )
                logger.info(f"Accounts document migrated successfully. Original _id: {accounts_doc['_id']}")
                return {"message": "Account keys migrated successfully.", "migrated_count": len(user_id_to_new_id_map)}
            else:
                return {"message": "No migration needed or performed.", "migrated_count": 0}
        else:
            return {"message": "No migration needed or performed.", "migrated_count": 0}

    except HTTPException:
        raise # Tovább dobjuk a FastAPI HTTP hibákat
    except Exception as e:
        logger.error(f"Error during account migration: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to migrate account data: {e}")