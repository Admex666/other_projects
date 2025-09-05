# seeds/lessons.py

from typing import Dict, List, Optional
from dataclasses import dataclass

@dataclass
class LessonPage:
    title: str
    content: str
    order: int

@dataclass
class QuizQuestion:
    question: str
    type: str  # "multiple_choice", "single_choice", "true_false"
    options: List[str]
    correct_answers: List[int]
    explanation: Optional[str] = None

@dataclass
class LessonContent:
    title: str
    description: Optional[str]
    pages: List[LessonPage]
    quiz_questions: List[QuizQuestion]

# Lecke tartalmak többnyelvű tárolása
LESSONS_CONTENT: Dict[str, Dict[str, LessonContent]] = {
    "basic_budgeting": {
        "hu": LessonContent(
            title="Alapvető költségvetés készítés",
            description="Tanuld meg, hogyan készíts hatékony személyi költségvetést.",
            pages=[
                LessonPage(
                    title="Mi az a költségvetés?",
                    content="""A költségvetés egy olyan terv, amely segít nyomon követni a bevételeidet és kiadásaidat egy meghatározott időszakra vonatkozóan.

# Miért fontos a költségvetés?

• **Pénzügyi kontroll**: Látod, hová megy a pénzed
• **Célok elérése**: Megtakarításokat tudsz tervezni
• **Stressz csökkentés**: Kevesebb pénzügyi aggodalom
• **Jobb döntések**: Tudatosabb vásárlási szokások

A költségvetés nem korlátozás, hanem szabadság - szabadság arra, hogy tudatosan dönts a pénzedről.""",
                    order=1
                ),
                LessonPage(
                    title="A 50/30/20 szabály",
                    content="""Az egyik legegyszerűbb költségvetési módszer a 50/30/20 szabály:

# Hogyan oszd fel a bevételeid?

**50% - Szükségletek**
• Lakbér/törlesztő
• Élelmiszer
• Közművek
• Minimális ruházat
• Közlekedés

**30% - Vágyak**
• Szórakozás
• Étterem
• Hobbik
• Nem alapvető vásárlások

**20% - Megtakarítás és adósság**
• Vészhelyzeti alap
• Nyugdíj megtakarítás
• Befektetések
• Extra adósságtörlesztés

Ez egy kiindulópont - saját helyzetedhez igazítsd!""",
                    order=2
                ),
                LessonPage(
                    title="Költségvetés lépései",
                    content="""# 5 lépésben a saját költségvetésedhez

**1. lépés: Számold ki a havi nettó bevételed**
Tartalmazza a fizetést, mellékjövedelmeket, támogatásokat.

**2. lépés: Írd fel minden havi kiadásod**
• Fix költségek (lakás, biztosítás, telefon)
• Változó költségek (élelmiszer, üzemanyag)
• Szórakozás és hobbik

**3. lépés: Kategorizálj**
Oszd szét a kiadásokat szükségletek és vágyak között.

**4. lépés: Számolj**
Bevétel - Kiadások = ?
Ha pozitív: jó, ha negatív: változtatni kell!

**5. lépés: Állíts be automatizmusokat**
Állíts be automatikus átutalásokat a megtakarításokra.""",
                    order=3
                )
            ],
            quiz_questions=[
                QuizQuestion(
                    question="Mi a 50/30/20 szabály szerint a megtakarításra és adósságtörlesztésre elkülönítendő arány?",
                    type="single_choice",
                    options=["10%", "20%", "30%", "50%"],
                    correct_answers=[1],
                    explanation="A 50/30/20 szabály szerint a bevétel 20%-át kell megtakarításra és adósságtörlesztésre fordítani."
                ),
                QuizQuestion(
                    question="Melyek tartoznak a szükségletek kategóriájába? (Több válasz is helyes)",
                    type="multiple_choice",
                    options=["Lakbér", "Étterem", "Élelmiszer", "Közművek", "Szórakozás"],
                    correct_answers=[0, 2, 3],
                    explanation="A szükségletek közé tartozik a lakbér, élelmiszer és közművek. Az étterem és szórakozás a vágyak kategóriába sorolható."
                ),
                QuizQuestion(
                    question="A költségvetés készítése korlátozza a szabadságodat.",
                    type="true_false",
                    options=["Igaz", "Hamis"],
                    correct_answers=[1],
                    explanation="Hamis. A költségvetés valójában több szabadságot ad, mert tudatosan dönthetsz a pénzedről és elérheted a céljaidat."
                )
            ]
        ),
        "en": LessonContent(
            title="Basic Budgeting",
            description="Learn how to create an effective personal budget.",
            pages=[
                LessonPage(
                    title="What is a budget?",
                    content="""A budget is a plan that helps you track your income and expenses over a specific period.

# Why is budgeting important?

• **Financial control**: You see where your money goes
• **Achieving goals**: You can plan savings
• **Stress reduction**: Less financial worry
• **Better decisions**: More conscious spending habits

A budget is not a limitation, but freedom - freedom to make conscious decisions about your money.""",
                    order=1
                ),
                LessonPage(
                    title="The 50/30/20 rule",
                    content="""One of the simplest budgeting methods is the 50/30/20 rule:

# How to divide your income?

**50% - Needs**
• Rent/mortgage
• Food
• Utilities
• Basic clothing
• Transportation

**30% - Wants**
• Entertainment
• Restaurants
• Hobbies
• Non-essential purchases

**20% - Savings and debt**
• Emergency fund
• Retirement savings
• Investments
• Extra debt payments

This is a starting point - adjust it to your own situation!""",
                    order=2
                ),
                LessonPage(
                    title="Budget steps",
                    content="""# 5 steps to your own budget

**Step 1: Calculate your monthly net income**
Include salary, side income, benefits.

**Step 2: List all your monthly expenses**
• Fixed costs (housing, insurance, phone)
• Variable costs (food, fuel)
• Entertainment and hobbies

**Step 3: Categorize**
Divide expenses between needs and wants.

**Step 4: Calculate**
Income - Expenses = ?
If positive: good, if negative: need to change!

**Step 5: Set up automation**
Set up automatic transfers for savings.""",
                    order=3
                )
            ],
            quiz_questions=[
                QuizQuestion(
                    question="According to the 50/30/20 rule, what percentage should be allocated for savings and debt repayment?",
                    type="single_choice",
                    options=["10%", "20%", "30%", "50%"],
                    correct_answers=[1],
                    explanation="According to the 50/30/20 rule, 20% of income should be allocated for savings and debt repayment."
                ),
                QuizQuestion(
                    question="Which belong to the needs category? (Multiple answers correct)",
                    type="multiple_choice",
                    options=["Rent", "Restaurants", "Food", "Utilities", "Entertainment"],
                    correct_answers=[0, 2, 3],
                    explanation="Needs include rent, food, and utilities. Restaurants and entertainment fall into the wants category."
                ),
                QuizQuestion(
                    question="Creating a budget limits your freedom.",
                    type="true_false",
                    options=["True", "False"],
                    correct_answers=[1],
                    explanation="False. A budget actually gives you more freedom because you can make conscious decisions about your money and achieve your goals."
                )
            ]
        )
    },
    
    "emergency_fund": {
        "hu": LessonContent(
            title="Vészhelyzeti alap építése",
            description="Építs fel egy biztonságos pénzügyi hátteret váratlan helyzetekre.",
            pages=[
                LessonPage(
                    title="Mi az a vészhelyzeti alap?",
                    content="""A vészhelyzeti alap egy olyan megtakarítás, amelyet váratlan pénzügyi helyzetekre tartasz fenn.

# Mikor van rá szükség?

• Munkahely elvesztése
• Váratlan orvosi költségek
• Lakás vagy autó sürgős javítása
• Családi vészhelyzetek

A vészhelyzeti alap nem befektetés - célja a biztonság, nem a hozam.""",
                    order=1
                ),
                LessonPage(
                    title="Mennyi pénz szükséges?",
                    content="""# Általános szabályok

**Kezdő szint: 1000 Ft**
Ha még nincs semmilyen megtakarításod, kezdj ezzel az összeggel.

**Minimális szint: 1 havi kiadás**
Számold ki a havi alapvető kiadásaidat és annyit tegyél félre.

**Ideális szint: 3-6 havi kiadás**
Ez már komoly biztonságot nyújt a legtöbb helyzetben.

**Maximális szint: 12 havi kiadás**
Ha bizonytalan a munkád vagy vállalkozó vagy.

Az összeg a te helyzetedtől függ!""",
                    order=2
                )
            ],
            quiz_questions=[
                QuizQuestion(
                    question="Mi a vészhelyzeti alap elsődleges célja?",
                    type="single_choice",
                    options=["Magas hozam elérése", "Váratlan kiadások fedezése", "Luxus vásárlások", "Nyugdíj megtakarítás"],
                    correct_answers=[1],
                    explanation="A vészhelyzeti alap célja a váratlan pénzügyi helyzetek kezelése, nem a hozam maximalizálása."
                )
            ]
        ),
        "en": LessonContent(
            title="Building an Emergency Fund",
            description="Build a secure financial background for unexpected situations.",
            pages=[
                LessonPage(
                    title="What is an emergency fund?",
                    content="""An emergency fund is savings that you keep for unexpected financial situations.

# When do you need it?

• Job loss
• Unexpected medical costs
• Urgent home or car repairs
• Family emergencies

The emergency fund is not an investment - its purpose is security, not returns.""",
                    order=1
                ),
                LessonPage(
                    title="How much money is needed?",
                    content="""# General rules

**Beginner level: $50**
If you don't have any savings yet, start with this amount.

**Minimum level: 1 month of expenses**
Calculate your monthly basic expenses and save that much.

**Ideal level: 3-6 months of expenses**
This provides serious security for most situations.

**Maximum level: 12 months of expenses**
If your job is uncertain or you're an entrepreneur.

The amount depends on your situation!""",
                    order=2
                )
            ],
            quiz_questions=[
                QuizQuestion(
                    question="What is the primary purpose of an emergency fund?",
                    type="single_choice",
                    options=["Achieving high returns", "Covering unexpected expenses", "Luxury purchases", "Retirement savings"],
                    correct_answers=[1],
                    explanation="The purpose of an emergency fund is to handle unexpected financial situations, not to maximize returns."
                )
            ]
        )
    }
}

# Kategóriák és leckék hozzárendelése
LESSON_CATEGORIES: Dict[str, Dict[str, str]] = {
    "basic_finance": {
        "hu": "Alapvető pénzügyek",
        "en": "Basic Finance"
    },
    "savings": {
        "hu": "Megtakarítások",
        "en": "Savings"
    }
}

# Leckék kategóriákhoz rendelése
LESSON_CATEGORY_MAPPING = {
    "basic_budgeting": "basic_finance",
    "emergency_fund": "savings"
}