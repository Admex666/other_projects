"""Alapvető konstansok és enumerációk a QuizForge rendszerhez."""

from enum import Enum


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
