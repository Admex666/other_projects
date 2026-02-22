import pandas as pd
from sqlalchemy.orm import Session
from app.models import domain
from app.models import schemas
import io
import json

class ImportService:
    @staticmethod
    def import_from_csv(db: Session, file_content: bytes, model_type: str):
        df = pd.read_csv(io.BytesIO(file_content))
        return ImportService._process_dataframe(db, df, model_type)

    @staticmethod
    def import_from_json(db: Session, file_content: bytes, model_type: str):
        data = json.loads(file_content)
        df = pd.DataFrame(data)
        return ImportService._process_dataframe(db, df, model_type)

    @staticmethod
    def _process_dataframe(db: Session, df: pd.DataFrame, model_type: str):
        # Mapping model types to their SQLAlchemy classes
        model_map = {
            "clinic": domain.Clinic,
            "patient": domain.Patient,
            "doctor": domain.Doctor,
            "service": domain.Service,
            "appointment": domain.Appointment,
            "revenue": domain.RevenueEvent
        }
        
        if model_type not in model_map:
            raise ValueError(f"Unknown model type: {model_type}")
            
        model_class = model_map[model_type]
        records = df.to_dict(orient="records")
        
        imported_count = 0
        for record in records:
            # Basic validation could be added here using Pydantic schemas if needed
            db_item = model_class(**record)
            db.add(db_item)
            imported_count += 1
            
        db.commit()
        return imported_count
