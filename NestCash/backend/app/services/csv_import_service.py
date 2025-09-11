# app/services/csv_import_service.py
import csv
import io
import base64
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import logging

from app.models.csv_import_models import (
    CSVPreviewResponse, CSVPreviewRow, ColumnMapping, CSVColumnType,
    ImportConfiguration, TransactionImportData, ImportResult, ImportStats
)
from app.models.transaction import Transaction
from beanie import PydanticObjectId

logger = logging.getLogger(__name__)

class CSVImportService:
    """CSV import szolgáltatás"""
    
    # Revolut típusok leképezése az app típusaira
    REVOLUT_TYPE_MAPPING = {
        'CARD_PAYMENT': 'expense',
        'ATM': 'expense', 
        'TRANSFER': 'transfer',
        'TOPUP': 'income',
        'EXCHANGE': 'transfer',
        'FEE': 'expense',
        'REFUND': 'income'
    }
    
    # Oszlopnevek automatikus felismerése
    COLUMN_DETECTION_PATTERNS = {
        CSVColumnType.DATE: ['date', 'started date', 'completed date', 'datum', 'időpont'],
        CSVColumnType.AMOUNT: ['amount', 'osszeg', 'összeg', 'value'],
        CSVColumnType.DESCRIPTION: ['description', 'leiras', 'leírás', 'title', 'megnevezes'],
        CSVColumnType.TYPE: ['type', 'tipus', 'típus', 'transaction type'],
        CSVColumnType.CURRENCY: ['currency', 'deviza', 'penznem'],
        CSVColumnType.CATEGORY: ['category', 'kategoria', 'kategória']
    }

    @staticmethod
    def decode_csv_data(base64_data: str) -> str:
        """Base64 encoded CSV adat dekódolása"""
        try:
            # Base64 dekódolás
            decoded_bytes = base64.b64decode(base64_data)
            
            # Encoding felismerés - próbáljuk UTF-8-al, ha nem megy akkor latin-1
            try:
                return decoded_bytes.decode('utf-8')
            except UnicodeDecodeError:
                return decoded_bytes.decode('latin-1')
                
        except Exception as e:
            raise ValueError(f"Failed to decode CSV data: {e}")

    @staticmethod
    def parse_csv_content(csv_content: str, delimiter: str = ',') -> Tuple[List[str], List[Dict[str, Any]]]:
        """CSV tartalom parsing"""
        try:
            # Automatikus delimiter felismerés
            sniffer = csv.Sniffer()
            try:
                detected_delimiter = sniffer.sniff(csv_content[:1024]).delimiter
                delimiter = detected_delimiter
            except:
                pass  # Használjuk az alapértelmezett delimiter-t
            
            reader = csv.DictReader(io.StringIO(csv_content), delimiter=delimiter)
            
            headers = reader.fieldnames or []
            rows = list(reader)
            
            return headers, rows
            
        except Exception as e:
            raise ValueError(f"Failed to parse CSV: {e}")

    @staticmethod
    def detect_column_mappings(headers: List[str]) -> List[ColumnMapping]:
        """Oszlop leképezések automatikus felismerése"""
        mappings = []
        used_types = set()
        
        for header in headers:
            header_lower = header.lower().strip()
            detected_type = None
            
            # Keressük meg a legjobb match-et
            for col_type, patterns in CSVImportService.COLUMN_DETECTION_PATTERNS.items():
                if col_type in used_types:
                    continue
                    
                for pattern in patterns:
                    if pattern in header_lower:
                        detected_type = col_type
                        break
                
                if detected_type:
                    used_types.add(detected_type)
                    break
            
            if not detected_type:
                detected_type = CSVColumnType.IGNORE
            
            mappings.append(ColumnMapping(
                csv_column_name=header,
                app_field=detected_type,
                required=detected_type in [CSVColumnType.DATE, CSVColumnType.AMOUNT, CSVColumnType.DESCRIPTION]
            ))
        
        return mappings

    @staticmethod
    async def preview_csv(base64_data: str, max_preview_rows: int = 10) -> CSVPreviewResponse:
        """CSV előnézet generálása"""
        try:
            # CSV dekódolás és parsing
            csv_content = CSVImportService.decode_csv_data(base64_data)
            headers, rows = CSVImportService.parse_csv_content(csv_content)
            
            if not headers:
                raise ValueError("No headers found in CSV")
            
            if not rows:
                raise ValueError("No data rows found in CSV")
            
            # Oszlop leképezések automatikus felismerése
            detected_mappings = CSVImportService.detect_column_mappings(headers)
            
            # Előnézeti sorok létrehozása
            sample_rows = []
            for i, row in enumerate(rows[:max_preview_rows]):
                preview_row = CSVPreviewRow(
                    row_index=i,
                    data=row
                )
                
                # Próbáljuk meg parseolni az adatokat
                try:
                    parsed_data = CSVImportService._parse_row_data(row, detected_mappings)
                    preview_row.parsed_data = parsed_data
                except Exception as e:
                    preview_row.errors.append(str(e))
                
                sample_rows.append(preview_row)
            
            return CSVPreviewResponse(
                headers=headers,
                sample_rows=sample_rows,
                total_rows=len(rows),
                detected_mappings=detected_mappings
            )
            
        except Exception as e:
            logger.error(f"CSV preview error: {e}")
            raise ValueError(f"Failed to preview CSV: {e}")

    @staticmethod
    def _parse_row_data(row: Dict[str, Any], mappings: List[ColumnMapping]) -> Dict[str, Any]:
        """Sor adatok parseolása a leképezések alapján"""
        parsed_data = {}
        
        for mapping in mappings:
            if mapping.app_field == CSVColumnType.IGNORE:
                continue
                
            raw_value = row.get(mapping.csv_column_name, "")
            
            if mapping.app_field == CSVColumnType.DATE:
                parsed_data['date'] = CSVImportService._parse_date(raw_value)
            elif mapping.app_field == CSVColumnType.AMOUNT:
                parsed_data['amount'] = CSVImportService._parse_amount(raw_value)
            elif mapping.app_field == CSVColumnType.DESCRIPTION:
                parsed_data['description'] = str(raw_value).strip()
            elif mapping.app_field == CSVColumnType.TYPE:
                parsed_data['type'] = CSVImportService._parse_transaction_type(raw_value)
            elif mapping.app_field == CSVColumnType.CURRENCY:
                parsed_data['currency'] = str(raw_value).strip().upper()
            elif mapping.app_field == CSVColumnType.CATEGORY:
                parsed_data['category'] = str(raw_value).strip()
        
        return parsed_data

    @staticmethod
    def _parse_date(date_str: str) -> str:
        """Dátum parseolás különböző formátumokból"""
        if not date_str:
            raise ValueError("Empty date")
        
        # Próbáljuk meg különböző dátum formátumokkal
        date_formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
            "%d/%m/%Y %H:%M:%S", 
            "%d/%m/%Y",
            "%m/%d/%Y %H:%M:%S",
            "%m/%d/%Y",
            "%Y.%m.%d %H:%M:%S",
            "%Y.%m.%d"
        ]
        
        for fmt in date_formats:
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                return dt.strftime("%Y-%m-%d")  # Egységes formátumban visszaadjuk
            except ValueError:
                continue
        
        raise ValueError(f"Unable to parse date: {date_str}")

    @staticmethod
    def _parse_amount(amount_str: str) -> float:
        """Összeg parseolás"""
        if not amount_str:
            raise ValueError("Empty amount")
        
        # Tisztítjuk az összeget (eltávolítjuk a whitespace-t és extra karaktereket)
        clean_amount = str(amount_str).strip().replace(',', '').replace(' ', '')
        
        try:
            return float(clean_amount)
        except ValueError:
            raise ValueError(f"Unable to parse amount: {amount_str}")

    @staticmethod 
    def _parse_transaction_type(type_str: str) -> str:
        """Tranzakció típus parseolás"""
        if not type_str:
            return "expense"  # Alapértelmezett
        
        type_upper = str(type_str).strip().upper()
        
        # Revolut típusok leképezése
        if type_upper in CSVImportService.REVOLUT_TYPE_MAPPING:
            return CSVImportService.REVOLUT_TYPE_MAPPING[type_upper]
        
        # Egyéb típusok
        if type_upper in ['INCOME', 'BEVETEL', 'CREDIT']:
            return 'income'
        elif type_upper in ['EXPENSE', 'KIADAS', 'DEBIT']:
            return 'expense'
        elif type_upper in ['TRANSFER', 'ATUTALAS']:
            return 'transfer'
        
        return "expense"  # Alapértelmezett

    @staticmethod
    async def execute_import(
        user_id: str,
        base64_data: str, 
        configuration: ImportConfiguration
    ) -> ImportResult:
        """CSV import végrehajtása"""
        result = ImportResult()
        
        try:
            # CSV dekódolás és parsing
            csv_content = CSVImportService.decode_csv_data(base64_data)
            headers, rows = CSVImportService.parse_csv_content(csv_content)
            
            # Tranzakciók feldolgozása
            transactions_to_import = []
            
            for i, row in enumerate(rows):
                try:
                    # Sor parseolás
                    parsed_data = CSVImportService._parse_row_data(row, configuration.column_mappings)
                    
                    # Tranzakció adat összeállítása
                    transaction_data = TransactionImportData(
                        date=parsed_data.get('date', datetime.now().strftime("%Y-%m-%d")),
                        amount=parsed_data.get('amount', 0),
                        description=parsed_data.get('description', 'Imported transaction'),
                        type=parsed_data.get('type', 'expense'),
                        category=parsed_data.get('category') or configuration.default_category,
                        currency=parsed_data.get('currency', 'HUF'),
                        original_row=row
                    )
                    
                    # Duplikáció ellenőrzés
                    if configuration.skip_duplicates:
                        is_duplicate = await CSVImportService._check_duplicate(
                            user_id, transaction_data
                        )
                        transaction_data.is_duplicate = is_duplicate
                        
                        if is_duplicate:
                            result.duplicate_count += 1
                            continue
                    
                    transactions_to_import.append(transaction_data)
                    
                except Exception as e:
                    result.error_count += 1
                    result.errors.append({
                        'row_index': i,
                        'error': str(e),
                        'row_data': row
                    })
            
            # Tranzakciók mentése
            for transaction_data in transactions_to_import:
                try:
                    # Amount előjel kezelése a type alapján
                    amount_to_save = transaction_data.amount
                    if transaction_data.type == 'expense' and amount_to_save > 0:
                        amount_to_save *= -1
                    elif transaction_data.type == 'income' and amount_to_save < 0:
                        amount_to_save *= -1
                    
                    new_transaction = Transaction(
                        user_id=PydanticObjectId(user_id),
                        date=transaction_data.date,
                        amount=amount_to_save,
                        description=transaction_data.description,
                        main_account=configuration.main_account,
                        sub_account_name=configuration.sub_account_name,
                        kategoria=transaction_data.category,
                        type=transaction_data.type,
                        currency=transaction_data.currency
                    )
                    
                    await new_transaction.insert()
                    result.imported_transaction_ids.append(str(new_transaction.id))
                    result.success_count += 1
                    
                except Exception as e:
                    result.error_count += 1
                    result.errors.append({
                        'transaction': transaction_data.model_dump(),
                        'error': str(e)
                    })
            
            logger.info(f"Import completed: {result.success_count} success, {result.error_count} errors, {result.duplicate_count} duplicates")
            
        except Exception as e:
            logger.error(f"Import failed: {e}")
            result.errors.append({
                'general_error': str(e)
            })
            result.error_count += 1
        
        return result

    @staticmethod
    async def _check_duplicate(user_id: str, transaction_data: TransactionImportData) -> bool:
        """Duplikáció ellenőrzés"""
        try:
            # Keresünk hasonló tranzakciókat (dátum + összeg + leírás alapján)
            existing = await Transaction.find_one({
                "user_id": PydanticObjectId(user_id),
                "date": transaction_data.date,
                "amount": {"$in": [transaction_data.amount, -transaction_data.amount]},  # Mindkét előjellel
                "description": transaction_data.description
            })
            
            return existing is not None
            
        except Exception as e:
            logger.warning(f"Duplicate check failed: {e}")
            return False

    @staticmethod
    def calculate_import_stats(transactions: List[TransactionImportData]) -> ImportStats:
        """Import statisztikák számítása"""
        stats = ImportStats()
        
        for transaction in transactions:
            if transaction.is_duplicate:
                continue
                
            amount = abs(transaction.amount)
            
            if transaction.type == 'income':
                stats.total_income += amount
            else:
                stats.total_expenses += amount
            
            # Kategória szerinti bontás
            category = transaction.category or 'Egyéb'
            if category not in stats.by_category:
                stats.by_category[category] = 0
            stats.by_category[category] += amount
            
            # Deviza szerinti bontás  
            currency = transaction.currency
            if currency not in stats.by_currency:
                stats.by_currency[currency] = 0
            stats.by_currency[currency] += amount
        
        return stats