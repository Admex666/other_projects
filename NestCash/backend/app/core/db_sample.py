from pymongo import MongoClient
import json
from bson import ObjectId
from dotenv import load_dotenv
import os

load_dotenv()

# --- segéd JSON encoder az ObjectId és dátumok miatt ---
class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        # ha kell datetime:
        try:
            import datetime
            if isinstance(o, (datetime.datetime, datetime.date)):
                return o.isoformat()
        except:
            pass
        return super().default(o)

def dump_db_overview(uri: str, db_name: str, coll_name: str, sample_size: int = 5):
    client = MongoClient(uri)
    db = client[db_name]
    overview = {}

    coll = db[coll_name]

    # count
    count = coll.estimated_document_count()

    # minták
    docs = list(coll.find().limit(sample_size))

    # kulcsok összesítése (top-level)
    keys = set()
    for d in docs:
        keys.update(d.keys())

    overview[coll_name] = {
        "count_estimate": count,
        "sample_keys": sorted(keys),
        "sample_docs": docs,
    }

    # pretty print string (amit ide be tudsz másolni)
    txt = json.dumps(overview, indent=2, ensure_ascii=False, cls=EnhancedJSONEncoder)
    print(txt)
    return txt

# --- Használat ---
if __name__ == "__main__":
    URI = os.getenv("MONGODB_URI")
    dump_db_overview(URI, "nestcash", 'accounts', sample_size=5)
