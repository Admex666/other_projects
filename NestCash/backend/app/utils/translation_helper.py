# app/utils/translation_helper.py

TRANSLATIONS = {
    'hu': {
        'recommendation_1': 'Költéseid magasabbak a hasonló felhasználókénál',
        'recommendation_2': 'Érdemes átnézni a legnagyobb kiadási kategóriákat',
        'recommendation_3': 'Költéseid alacsonyabbak az átlagnál - jó munka!',
        'recommendation_4': 'Fontos a megtakarítások növelése',
        'recommendation_5': 'Költési szokásaid átlagosak',
        'insight_1': 'Kategória változtatásokkal {savings:.0f} Ft éves megtakarítás lehetséges',
        'cost_optimization_title': 'Költségoptimalizálás',
        'savings_suggestions_title': 'Megtakarítási javaslatok',
        'emergency_fund_advice_title': 'Vészhelyzeti alap',
        'debt_management_title': 'Adósságkezelés'
    },
    'en': {
        'recommendation_1': 'Your spending is higher than similar users',
        'recommendation_2': 'It is worth reviewing the largest expense categories',
        'recommendation_3': 'Your spending is below average - good job!',
        'recommendation_4': 'It is important to increase savings',
        'recommendation_5': 'Your spending habits are average',
        'insight_1': 'With category changes, an annual saving of {savings:.0f} HUF is possible',
        'cost_optimization_title': 'Cost Optimization',
        'savings_suggestions_title': 'Savings Suggestions',
        'emergency_fund_advice_title': 'Emergency Fund',
        'debt_management_title': 'Debt Management'
    }
}

def translate(key: str, lang: str = 'hu', **kwargs) -> str:
    """A megadott kulcs fordítását adja vissza a megadott nyelven, változókkal helyettesítve."""
    translation_dict = TRANSLATIONS.get(lang, TRANSLATIONS['hu'])
    text = translation_dict.get(key, key)
    return text.format(**kwargs)