from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from backend.models import DimService, FactRevenue
# from backend.database import DATABASE_URL

# Adjust DB URL for script execution if needed (relative path)
# Assuming run from root
engine = create_engine("sqlite:///./clinicos.db")
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

print("Checking DimService...")
services = db.query(DimService).all()
print(f"Found {len(services)} services.")

print("Checking FactRevenue...")
revenue_count = db.query(FactRevenue).count()
print(f"Found {len(services)} revenue records.")

print("Running API Query...")
try:
    results = db.query(
        DimService.name,
        DimService.category,
        func.sum(FactRevenue.gross_revenue).label("revenue"),
        func.sum(FactRevenue.gross_margin).label("margin")
    ).join(DimService, FactRevenue.service_id == DimService.service_id)\
     .group_by(DimService.name, DimService.category).all()

    print(f"Query returned {len(results)} rows.")
    for r in results:
        print(r)
except Exception as e:
    print(f"Query Failed: {e}")
