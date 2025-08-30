# app/utils/translation_helper.py

TRANSLATIONS = {
    'hu': {
        'savings_low_rate': 'Próbálj meg legalább 10%-ot megtakarítani a bevételeidből',
        'savings_auto_setup': 'Állíts be automatikus megtakarítást minden hónap elején',
        'savings_increase_to_20': 'Remek! Próbáld növelni a megtakarítási rátád 20%-ra',
        'savings_excellent': 'Kiváló megtakarítási szokásaid vannak!',
        'emergency_fund_low': 'Építs fel legalább 3 havi kiadásnak megfelelő vészhelyzeti alapot',
        'emergency_fund_advice': 'Havonta tegyél félre egy kisebb összeget erre a célra',
        'debt_high': 'Adósságaid magasak a bevételeidhez képest',
        'debt_prioritize': 'Prioritást adj az adósságok törlesztésének',
        'debt_consolidation': 'Fontolj meg adósság-konszolidációt',
        'debt_reduce': 'Törekedj az adósságok fokozatos csökkentésére',
        'debt_good': 'Jól kezeled az adósságaidat!',
        'spending_unpredictable': 'Költési szokásaid kiszámíthatatlanok - próbálj rendszeresebb költségvetést vezetni',
        'spending_add_categories': 'Add hozzá az alapvető kategóriákat (élelmiszer, lakhatás, közlekedés)',
        'spending_variable_categories': 'Ezekben a kategóriákban változékony a költésed: {categories}',
        'spending_structured': 'Jól strukturált költési szokásaid vannak!',
        'anomaly_many': 'Sok szokatlan tranzakciót észleltünk - érdemes átnézni a költési szokásaidat',
        'anomaly_high_risk': '{count} magas kockázatú szokatlan kiadást találtunk',
        'anomaly_check': 'Ellenőrizd ezeket a tranzakciókat - lehetnek hibás vagy váratlan költések',
        'anomaly_time': 'Szokatlan időpontokban történt vásárlásokat észleltünk',
        'anomaly_stable': 'Költési szokásaid stabilak és kiszámíthatóak!',
        'forecast_increasing': 'Költéseid növekvő tendenciát mutatnak - érdemes figyelni!',
        'seasonal_christmas': 'Karácsonyi időszakban készülj fel magasabb kiadásokra - tervezz előre!',
        'seasonal_january': 'Januárban gyakran magasabbak a kiadások az új év fogadalmai miatt',
        'seasonal_peak_month': 'A legmagasabb kiadásaid {month}-ban vannak - érdemes erre a hónapra külön költségvetést készíteni',
        'seasonal_stable': 'Költési szokásaid egyenletesek az év során - ez jó költségvetési fegyelem jele!',
        'insight_savings': 'Az elemzés alapján {savings} Ft-ot takaríthatsz meg havonta',
    },
    'en': {
        'savings_low_rate': 'Try to save at least 10% of your income',
        'savings_auto_setup': 'Set up automatic savings at the beginning of each month',
        'savings_increase_to_20': 'Great! Try to increase your savings rate to 20%',
        'savings_excellent': 'You have excellent saving habits!',
        'emergency_fund_low': 'Build an emergency fund covering at least 3 months of expenses',
        'emergency_fund_advice': 'Set aside a small amount each month for this purpose',
        'debt_high': 'Your debts are high compared to your income',
        'debt_prioritize': 'Prioritize debt repayment',
        'debt_consolidation': 'Consider debt consolidation',
        'debt_reduce': 'Work on gradually reducing your debts',
        'debt_good': 'You manage your debts well!',
        'spending_unpredictable': 'Your spending habits are unpredictable - try to maintain a more regular budget',
        'spending_add_categories': 'Add basic categories (food, housing, transportation)',
        'spending_variable_categories': 'Your spending varies in these categories: {categories}',
        'spending_structured': 'You have well-structured spending habits!',
        'anomaly_many': 'We detected many unusual transactions - consider reviewing your spending habits',
        'anomaly_high_risk': 'Found {count} high-risk unusual expenses',
        'anomaly_check': 'Check these transactions - they might be errors or unexpected costs',
        'anomaly_time': 'We detected purchases at unusual times',
        'anomaly_stable': 'Your spending habits are stable and predictable!',
        'forecast_increasing': 'Your expenses show an increasing trend - worth monitoring!',
        'seasonal_christmas': 'Prepare for higher expenses during Christmas season - plan ahead!',
        'seasonal_january': 'January often has higher expenses due to New Year resolutions',
        'seasonal_peak_month': 'Your highest expenses are in {month} - consider a separate budget for this month',
        'seasonal_stable': 'Your spending habits are consistent throughout the year - a sign of good budget discipline!',
        'insight_savings': 'Based on the analysis, you could save {savings} HUF per month',
    }
}

def translate(key: str, lang: str = 'hu', **kwargs) -> str:
    """A megadott kulcs fordítását adja vissza a megadott nyelven, változókkal helyettesítve."""
    translation_dict = TRANSLATIONS.get(lang, TRANSLATIONS['hu'])
    text = translation_dict.get(key, key)
    return text.format(**kwargs)