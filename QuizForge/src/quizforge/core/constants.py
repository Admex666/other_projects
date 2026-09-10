"""Alapvető konstansok és enumerációk a QuizForge rendszerhez."""

from enum import Enum
from typing import Any


class QuestionMechanism(str, Enum):
    """Támogatott kérdésmechanizmusok a funkcionalitási specifikáció alapján."""
    ABCD = "abcd"                          # 4 válaszlehetőség
    TRUE_FALSE = "true_false"              # Igaz / Hamis
    ESTIMATION = "estimation"              # Numerikus becslés (évszám, távolság, darabszám)
    ORDERING = "ordering"                  # Időrendi vagy nagyságrendi sorba rendezés
    MATCHING = "matching"                  # Elemek párosítása (pl. író - mű, város - folyó)
    CONNECTION = "connection"              # Mi a közös bennük? / Kakukktojás
    FIRST_LETTER = "first_letter"          # Kezdőbetű megadva
    MISSING_LETTERS = "missing_letters"    # Hiányzó betűk kitalálása
    IMAGE_RECOGNITION = "image"            # Képről felismerés
    AUDIO_RECOGNITION = "audio"            # Hang / zenerészlet
    DEDUCTION = "deduction"                # Történetből / leírásból való következtetés
    PICTURE_PUZZLE = "picture_puzzle"      # Képrejtvény / rébusz


class Domain(str, Enum):
    """Fő tudásterületek kvízekben."""
    HISTORY = "history"                    # Történelem
    GEOGRAPHY = "geography"                # Földrajz
    LITERATURE = "literature"              # Irodalom és nyelvészet
    SCIENCE_TECH = "science_tech"          # Természettudomány és technológia
    POP_CULTURE = "pop_culture"            # Film, sorozat, popzene, képregény
    SPORTS = "sports"                      # Sport és olimpia
    ART_MUSIC = "art_music"                # Képzőművészet, klasszikus zene, színház
    GASTRONOMY = "gastronomy"              # Ételek, italok, konyhaművészet
    GENERAL_KNOWLEDGE = "general"          # Általános műveltség / vegyes


class SourceType(str, Enum):
    """Adatforrások típusai."""
    WIKIDATA = "wikidata"
    WIKIPEDIA = "wikipedia"
    MEK = "mek"
    OPEN_TRIVIA = "open_trivia"
    QUIZ_PORTAL = "quiz_portal"
    MANUAL = "manual"


# Felhasználóbarát, egységes magyar megjelenítési címkék
DOMAIN_LABELS = {
    Domain.HISTORY.value: "Történelem",
    Domain.GEOGRAPHY.value: "Földrajz",
    Domain.LITERATURE.value: "Irodalom és Nyelvészet",
    Domain.SCIENCE_TECH.value: "Tudomány és Technológia",
    Domain.POP_CULTURE.value: "Popkultúra",
    Domain.SPORTS.value: "Sport",
    Domain.ART_MUSIC.value: "Művészet és Zene",
    Domain.GASTRONOMY.value: "Gasztronómia",
    Domain.GENERAL_KNOWLEDGE.value: "Általános Műveltség",
    "general": "Általános Műveltség",
}

MECHANISM_LABELS = {
    QuestionMechanism.ABCD.value: "Feleletválasztós (ABCD)",
    QuestionMechanism.TRUE_FALSE.value: "Igaz-Hamis",
    QuestionMechanism.ESTIMATION.value: "Becslés / Saccolás",
    QuestionMechanism.ORDERING.value: "Sorrendbe állítás",
    QuestionMechanism.MATCHING.value: "Párosítás",
    QuestionMechanism.CONNECTION.value: "Kapcsolat / Mi a közös?",
    QuestionMechanism.FIRST_LETTER.value: "Kezdőbetűs",
    QuestionMechanism.MISSING_LETTERS.value: "Betűkiegészítés",
    QuestionMechanism.IMAGE_RECOGNITION.value: "Képfelismerés",
    QuestionMechanism.AUDIO_RECOGNITION.value: "Zenefelismerés",
    QuestionMechanism.DEDUCTION.value: "Dedukció / Sztori",
    QuestionMechanism.PICTURE_PUZZLE.value: "Képrejtvény",
}

CATEGORY_LABELS = {
    "pub_quiz": "Kocsmakvíz",
    "board_game": "Társasjáték",
}


def get_domain_label(domain_val: Any) -> str:
    """Visszaadja a domain szép magyar megnevezését."""
    if hasattr(domain_val, "value"):
        domain_val = domain_val.value
    key = str(domain_val).strip().lower()
    return DOMAIN_LABELS.get(key, key.replace("_", " ").title())


def get_mechanism_label(mech_val: Any) -> str:
    """Visszaadja a kérdésmechanizmus szép magyar megnevezését."""
    if hasattr(mech_val, "value"):
        mech_val = mech_val.value
    key = str(mech_val).strip().lower()
    return MECHANISM_LABELS.get(key, key.replace("_", " ").title())


def get_category_label(cat_val: Any) -> str:
    """Visszaadja a kvízkategória szép magyar megnevezését."""
    key = str(cat_val).strip().lower()
    return CATEGORY_LABELS.get(key, key.replace("_", " ").title())

