"""Kvízszervezői profilok, tájképek (Quiz Landscape) és ujjlenyomatok (Quiz Fingerprints)."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from quizforge.core.constants import Domain, QuestionMechanism


@dataclass
class QuizProfile:
    """Egy konkrét kvízest vagy kvízjáték tematikus és mechanizmus-ujjlenyomata."""
    profile_id: str
    name: str
    category: str  # "pub_quiz" vagy "board_game"
    description: str
    domain_weights: Dict[str, float] = field(default_factory=dict)
    mechanism_weights: Dict[str, float] = field(default_factory=dict)
    rules_notes: str = ""

    def get_domain_weight(self, domain: str) -> float:
        """Adott témakör súlya az ujjlenyomatban (0.0 ha nincs megadva)."""
        return self.domain_weights.get(domain, 0.05)

    def get_mechanism_weight(self, mechanism: str) -> float:
        """Adott mechanizmus súlya az ujjlenyomatban."""
        return self.mechanism_weights.get(mechanism, 0.05)


class QuizLandscapeEngine:
    """A magyar kvízestek és kvízjátékok katalógusa és tájképelemzője."""

    def __init__(self):
        self._profiles: Dict[str, QuizProfile] = {}
        self._load_curated_profiles()

    def _load_curated_profiles(self):
        """Valós magyar kvízestek és társasjátékok ujjlenyomatainak betöltése."""
        # 1. Csömör Kvízest
        self._profiles["csomor"] = QuizProfile(
            profile_id="csomor",
            name="Csömöri Kvízest",
            category="pub_quiz",
            description="Általános kocsmakvíz: Filmek, zenék, földrajz, sport, történelem és popkultúra.",
            domain_weights={
                Domain.POP_CULTURE.value: 0.25,
                Domain.GEOGRAPHY.value: 0.20,
                Domain.HISTORY.value: 0.20,
                Domain.SPORTS.value: 0.15,
                Domain.ART_MUSIC.value: 0.10,
                Domain.GENERAL_KNOWLEDGE.value: 0.10,
            },
            mechanism_weights={
                QuestionMechanism.ABCD.value: 0.70,
                QuestionMechanism.TRUE_FALSE.value: 0.15,
                QuestionMechanism.CONNECTION.value: 0.15,
            },
            rules_notes="Klasszikus pontszerző kvízest baráti csapatoknak."
        )

        # 2. QuizKrumpli
        self._profiles["quizkrumpli"] = QuizProfile(
            profile_id="quizkrumpli",
            name="QuizKrumpli",
            category="pub_quiz",
            description="55 kérdés, 8 blokkban: film, zene, bulvár, irodalom, tudomány, rekordok, gasztró, biológia.",
            domain_weights={
                Domain.POP_CULTURE.value: 0.20,
                Domain.LITERATURE.value: 0.15,
                Domain.SCIENCE_TECH.value: 0.15,
                Domain.GASTRONOMY.value: 0.15,
                Domain.GENERAL_KNOWLEDGE.value: 0.15,
                Domain.GEOGRAPHY.value: 0.10,
                Domain.ART_MUSIC.value: 0.10,
            },
            mechanism_weights={
                QuestionMechanism.ABCD.value: 0.35,
                QuestionMechanism.TRUE_FALSE.value: 0.15,
                QuestionMechanism.CONNECTION.value: 0.15,
                QuestionMechanism.MATCHING.value: 0.15,
                QuestionMechanism.ORDERING.value: 0.10,
                QuestionMechanism.FIRST_LETTER.value: 0.10,
            },
            rules_notes="Változatos feladattípusok és blokkok, egyedi feladványok."
        )

        # 3. Quizland
        self._profiles["quizland"] = QuizProfile(
            profile_id="quizland",
            name="Quizland",
            category="pub_quiz",
            description="Blokkok: Bemelegítő, Képben vagy?, Sorrend, Mi az igazság?, Tematikus, Kapcsolat, Pontlépcső.",
            domain_weights={
                Domain.GENERAL_KNOWLEDGE.value: 0.25,
                Domain.HISTORY.value: 0.15,
                Domain.GEOGRAPHY.value: 0.15,
                Domain.SCIENCE_TECH.value: 0.15,
                Domain.POP_CULTURE.value: 0.15,
                Domain.ART_MUSIC.value: 0.15,
            },
            mechanism_weights={
                QuestionMechanism.ABCD.value: 0.30,
                QuestionMechanism.ORDERING.value: 0.20,
                QuestionMechanism.TRUE_FALSE.value: 0.20,
                QuestionMechanism.CONNECTION.value: 0.20,
                QuestionMechanism.PICTURE_PUZZLE.value: 0.10,
            },
            rules_notes="Kötött blokkszerkezet kapcsolat és sorrend feladványokkal."
        )

        # 4. Kertvárosi Kvízjáték
        self._profiles["kertvarosi"] = QuizProfile(
            profile_id="kertvarosi",
            name="Kertvárosi Kvízjáték",
            category="pub_quiz",
            description="Általános műveltség és meglepő rekordok, numerikus saccolások (pl. 'Hány kockacukornyi cukrot tartalmaz a Mars csoki?').",
            domain_weights={
                Domain.GENERAL_KNOWLEDGE.value: 0.35,
                Domain.GASTRONOMY.value: 0.25,
                Domain.SCIENCE_TECH.value: 0.15,
                Domain.GEOGRAPHY.value: 0.15,
                Domain.HISTORY.value: 0.10,
            },
            mechanism_weights={
                QuestionMechanism.ESTIMATION.value: 0.45,
                QuestionMechanism.ABCD.value: 0.40,
                QuestionMechanism.TRUE_FALSE.value: 0.15,
            },
            rules_notes="Hangsúly a saccolásokon, hétköznapi arányokon és meglepő rekordokon."
        )

        # 5. Inquizitor
        self._profiles["inquizitor"] = QuizProfile(
            profile_id="inquizitor",
            name="Inquizitor Társasjáték",
            category="board_game",
            description="Kártyatípusok: Sztori (tartalom alapján cím), Saccolás (szám ±30% toleranciával), Szófordítás (régies szavak), Betűkiegészítés.",
            domain_weights={
                Domain.LITERATURE.value: 0.30,
                Domain.POP_CULTURE.value: 0.25,
                Domain.SCIENCE_TECH.value: 0.20,
                Domain.GENERAL_KNOWLEDGE.value: 0.15,
                Domain.HISTORY.value: 0.10,
            },
            mechanism_weights={
                QuestionMechanism.DEDUCTION.value: 0.30,
                QuestionMechanism.ESTIMATION.value: 0.30,
                QuestionMechanism.MATCHING.value: 0.20,
                QuestionMechanism.MISSING_LETTERS.value: 0.20,
            },
            rules_notes="Saccolásnál a hibahatár legfeljebb 30%. Szófordításnál elfeledett magyar szavak."
        )

        # 6. Honfoglaló / Triviador
        self._profiles["honfoglalo"] = QuizProfile(
            profile_id="honfoglalo",
            name="Honfoglaló (Triviador)",
            category="board_game",
            description="10 témakör: Biológia+Kémia, Sport, Szórakozás, Életmód, Művészet, Mindennapok, Földrajz, Történelem, Irodalom, Matek+Fizika.",
            domain_weights={
                Domain.SCIENCE_TECH.value: 0.20,
                Domain.HISTORY.value: 0.15,
                Domain.GEOGRAPHY.value: 0.15,
                Domain.LITERATURE.value: 0.10,
                Domain.SPORTS.value: 0.10,
                Domain.POP_CULTURE.value: 0.10,
                Domain.ART_MUSIC.value: 0.10,
                Domain.GENERAL_KNOWLEDGE.value: 0.10,
            },
            mechanism_weights={
                QuestionMechanism.ABCD.value: 0.60,
                QuestionMechanism.ESTIMATION.value: 0.40,
            },
            rules_notes="Klasszikus 4-választós villámkérdések és legközelebbi tippelős bázisfoglaló kérdések."
        )

    def list_profiles(self) -> List[QuizProfile]:
        """Összes elérhető kvízprofil listázása."""
        return list(self._profiles.values())

    def get_profile(self, profile_id: str) -> Optional[QuizProfile]:
        """Kvízprofil lekérése azonosító alapján."""
        return self._profiles.get(profile_id)
