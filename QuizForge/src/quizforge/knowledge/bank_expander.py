"""Kérdésbank bővítő modul: Offline, determinisztikus és kurált kérdésbázis építése Groq API token kíméléssel."""

import json
import random
from typing import Any, Dict, List, Tuple
from quizforge.core.constants import Domain, QuestionMechanism, SourceType
from quizforge.core.models import RawQuizQuestion
from quizforge.storage.db import DatabaseManager
from quizforge.storage.repositories import QuizQuestionRepository


# --- 1. INQUIZITOR SPECIÁLIS KÁRTYÁK ---

INQUIZITOR_STORIES = [
    {
        "id": "inq:story:tüskevar",
        "text": "Melyik híres magyar ifjúsági regény cselekménye az alábbi?\n'Egy pesti kamasz fiú a nyári szünetben a Kis-Balatonhoz kerül rokonához, ahol a bölcs öreg pákász, Matula bácsi tanítja meg a nádi élet, a természet és a felelősség törvényeire.'",
        "correct": "Tüskevár",
        "options": ["Tüskevár", "Téli berek", "A Pál utcai fiúk", "Kincskereső kisködmön"],
        "domain": Domain.LITERATURE,
        "subdomain": "sztori",
    },
    {
        "id": "inq:story:egri_csillagok",
        "text": "Melyik klasszikus magyar regény cselekménye az alábbi?\n'A török hódoltság korában játszódó történet, amely Bornemissza Gergely és Cecey Éva sorsát követi nyomon az 1552-es hősies végvári ostromig Dobó István vezetésével.'",
        "correct": "Egri csillagok",
        "options": ["Egri csillagok", "A kőszívű ember fiai", "A láthatatlan ember", "Rab Ráby"],
        "domain": Domain.LITERATURE,
        "subdomain": "sztori",
    },
    {
        "id": "inq:story:pal_utcai_fiuk",
        "text": "Melyik világirodalmi hírű magyar regény leírása?\n'Két budapesti fiúcsapat, a grund védői Boka vezetésével és az Áts Feri vezette vörösingesek harcolnak egy darabka grundért, miközben a legkisebb fiú hősiessége életét követeli.'",
        "correct": "A Pál utcai fiúk",
        "options": ["A Pál utcai fiúk", "Légy jó mindhalálig", "Kincskereső kisködmön", "Tüskevár"],
        "domain": Domain.LITERATURE,
        "subdomain": "sztori",
    },
    {
        "id": "inq:story:robinson",
        "text": "Melyik regény cselekményét rejti a leírás?\n'Egy hajótörést szenvedett angol tengerész huszonnyolc évet tölt egy lakatlan szigeten a Karib-tenger térségében, ahol egy Péntek nevű bennszülött lesz a társa.'",
        "correct": "Robinson Crusoe",
        "options": ["Robinson Crusoe", "Gulliver utazásai", "Kétévi vakáció", "A kincses sziget"],
        "domain": Domain.LITERATURE,
        "subdomain": "sztori",
    },
    {
        "id": "inq:story:gatsby",
        "text": "Melyik 20. századi regényről van szó?\n'Egy titokzatos milliomos extravagáns partikat rendez Long Islanden a jazzkorszakban abban a reményben, hogy újra elcsábíthatja fiatalkori szerelmét, Daisyt.'",
        "correct": "A nagy Gatsby",
        "options": ["A nagy Gatsby", "Búcsú a fegyverektől", "Rozsban a fogó", "Édentől keletre"],
        "domain": Domain.LITERATURE,
        "subdomain": "sztori",
    },
    {
        "id": "inq:story:harom_testor_afrikaban",
        "text": "Melyik Rejtő Jenő regényről van szó?\n'A Francia Idegenlégió három jómadara, Csülök, Senki Alfonz és Tuskó Hopkins elindul felkutatni egy titkos szudáni gyarmati összeesküvést.'",
        "correct": "A három testőr Afrikában",
        "options": ["A három testőr Afrikában", "A láthatatlan légió", "Piszkos Fred, a kapitány", "A szőke ciklon"],
        "domain": Domain.LITERATURE,
        "subdomain": "sztori",
    }
]

INQUIZITOR_WORDS = [
    {
        "id": "inq:word:umog",
        "text": "Mit jelent a régi magyar 'ümög' kifejezés?",
        "correct": "Ing",
        "options": ["Ing", "Csizma", "Kalap", "Köpönyeg"],
        "domain": Domain.LITERATURE,
        "subdomain": "szófordítás",
    },
    {
        "id": "inq:word:cenk",
        "text": "Mit jelent a népies 'cenk' szó?",
        "correct": "Kiskutya",
        "options": ["Kiskutya", "Vadmalac", "Csikó", "Bárány"],
        "domain": Domain.LITERATURE,
        "subdomain": "szófordítás",
    },
    {
        "id": "inq:word:saroglya",
        "text": "Mi volt a 'saroglya' a hagyományos falusi életben?",
        "correct": "Szekérülés / poggyásztartó",
        "options": ["Szekérülés / poggyásztartó", "Kapanyél", "Cséplőgép", "Aratókoszorú"],
        "domain": Domain.LITERATURE,
        "subdomain": "szófordítás",
    },
    {
        "id": "inq:word:pityke",
        "text": "Mi a 'pityke' a hagyományos magyar viseletben?",
        "correct": "Díszes fémgomb",
        "options": ["Díszes fémgomb", "Övcsat", "Kalaptoll", "Sarkantyú"],
        "domain": Domain.LITERATURE,
        "subdomain": "szófordítás",
    },
    {
        "id": "inq:word:kenceficel",
        "text": "Mit csinál az a személy, aki 'kenceficél'?",
        "correct": "Piperézkedik / feleslegesen kenegeti magát",
        "options": ["Piperézkedik / feleslegesen kenegeti magát", "Szánt a mezőn", "Kenyeret dagaszt", "Kereket zsíroz"],
        "domain": Domain.LITERATURE,
        "subdomain": "szófordítás",
    },
    {
        "id": "inq:word:lajbi",
        "text": "Mi az a 'lajbi'?",
        "correct": "Ujjatlan mellény",
        "options": ["Ujjatlan mellény", "Bőrcsizma", "Bőrnadrág", "Zsebkendő"],
        "domain": Domain.LITERATURE,
        "subdomain": "szófordítás",
    },
    {
        "id": "inq:word:kalamaris",
        "text": "Mi volt régen a 'kalamáris'?",
        "correct": "Tintatartó",
        "options": ["Tintatartó", "Vonalzó", "Irótábla", "Krétatartó doboz"],
        "domain": Domain.LITERATURE,
        "subdomain": "szófordítás",
    },
    {
        "id": "inq:word:bakafantos",
        "text": "Milyen tulajdonságú emberre mondták régen, hogy 'bakafántos'?",
        "correct": "Kötekedő / makacs",
        "options": ["Kötekedő / makacs", "Jószívű és adakozó", "Vidám és tréfás", "Gyámoltalan"],
        "domain": Domain.LITERATURE,
        "subdomain": "szófordítás",
    },
    {
        "id": "inq:word:garaboncias",
        "text": "Ki a 'garabonciás' a magyar néphit szerint?",
        "correct": "Vándorló, varázserejű diák",
        "options": ["Vándorló, varázserejű diák", "Kovácsmester", "Erdőkerülő vadász", "Kóbor hegedűs"],
        "domain": Domain.LITERATURE,
        "subdomain": "szófordítás",
    }
]

INQUIZITOR_LETTERS = [
    {
        "id": "inq:let:vadnyugat",
        "text": "Egészítsd ki a klasszikus filmcímet a hiányzó betűk pótlásával:\n'_ o l t   e g y _ z e r   e g y   _ a d n y u g a t'",
        "correct": "Volt egyszer egy vadnyugat",
        "options": ["Volt egyszer egy vadnyugat", "Holt lelkek a vadnyugaton", "Volt egyszer egy herceg", "Volt egyszer egy Amerika"],
        "domain": Domain.POP_CULTURE,
        "subdomain": "betűkiegészítés",
    },
    {
        "id": "inq:let:penz_kutya",
        "text": "Melyik híres magyar közmondást rejti a betűrejtvény?\n'_ é n z   b e s z é l ,   k u t y a   _ g a t'",
        "correct": "Pénz beszél, kutya ugat",
        "options": ["Pénz beszél, kutya ugat", "Kéz kezet mos, kutya fut", "Pénz nem boldogít", "Ki korán kel, aranyat lel"],
        "domain": Domain.LITERATURE,
        "subdomain": "betűkiegészítés",
    },
    {
        "id": "inq:let:fekete_varos",
        "text": "Egészítsd ki Mikszáth Kálmán híres regényének címét:\n'A   _ e k e t e   _ á r o s'",
        "correct": "A fekete város",
        "options": ["A fekete város", "A fekete gyémánt", "A velencei kalmár", "A néma levente"],
        "domain": Domain.LITERATURE,
        "subdomain": "betűkiegészítés",
    }
]


# --- 2. KERTVÁROSI KVÍZ & SACCOLÁSOK (ESTIMATION) ---

ESTIMATION_QUESTIONS = [
    {
        "id": "est:mars_cukor",
        "text": "Hány darab kockacukornyi (kb. 3-3.2g) cukrot tartalmaz egyetlen darab átlagos 51 grammos Mars csokoládé?",
        "correct": "8",
        "domain": Domain.GASTRONOMY,
        "subdomain": "cukortartalom",
        "metadata": {"unit": "kockacukor", "tolerance_percentage": 25.0}
    },
    {
        "id": "est:cola_cukor",
        "text": "Hány darab kockacukornyi cukor található egy klasszikus 330 ml-es dobozos Coca-Colában?",
        "correct": "7",
        "domain": Domain.GASTRONOMY,
        "subdomain": "cukortartalom",
        "metadata": {"unit": "kockacukor", "tolerance_percentage": 25.0}
    },
    {
        "id": "est:kekbalna_sziv",
        "text": "Körülbelül hány kilogrammot nyom egy kifejlett kék bálna szíve?",
        "correct": "180",
        "domain": Domain.SCIENCE_TECH,
        "subdomain": "rekordok",
        "metadata": {"unit": "kg", "tolerance_percentage": 30.0}
    },
    {
        "id": "est:eiffel_lepcsok",
        "text": "Hány lépcsőfok vezet fel az Eiffel-torony legfelső látogatható szintjéig a talajtól?",
        "correct": "1665",
        "domain": Domain.GEOGRAPHY,
        "subdomain": "rekordok",
        "metadata": {"unit": "lépcsőfok", "tolerance_percentage": 20.0}
    },
    {
        "id": "est:everest_magassag",
        "text": "Hány méter magas a Föld legmagasabb hegycsúcsa, a Csomolungma (Mount Everest)?",
        "correct": "8848",
        "domain": Domain.GEOGRAPHY,
        "subdomain": "földrajz",
        "metadata": {"unit": "méter", "tolerance_percentage": 5.0}
    },
    {
        "id": "est:napfeny_ido",
        "text": "Hány másodperc alatt ér a Nap fénye a Földre a vákuumban?",
        "correct": "500",
        "domain": Domain.SCIENCE_TECH,
        "subdomain": "fizika",
        "metadata": {"unit": "másodperc", "tolerance_percentage": 15.0}
    },
    {
        "id": "est:orszaghas_magassag",
        "text": "Hány méter magas a budapesti Országház és a Szent István-bazilika kupolája?",
        "correct": "96",
        "domain": Domain.HISTORY,
        "subdomain": "építészet",
        "metadata": {"unit": "méter", "tolerance_percentage": 5.0}
    },
    {
        "id": "est:balaton_melyseg",
        "text": "Hány méter mély a Balaton legmélyebb pontja a Tihanyi-kútnál?",
        "correct": "11",
        "domain": Domain.GEOGRAPHY,
        "subdomain": "magyar_földrajz",
        "metadata": {"unit": "méter", "tolerance_percentage": 20.0}
    },
    {
        "id": "est:kekes_magassag",
        "text": "Hány méter magas Magyarország legmagasabb hegycsúcsa, a Kékestető?",
        "correct": "1014",
        "domain": Domain.GEOGRAPHY,
        "subdomain": "magyar_földrajz",
        "metadata": {"unit": "méter", "tolerance_percentage": 5.0}
    },
    {
        "id": "est:emberi_fogak",
        "text": "Hány foga van egy kifejlett felnőtt embernek a bölcsességfogakkal együtt?",
        "correct": "32",
        "domain": Domain.SCIENCE_TECH,
        "subdomain": "biológia",
        "metadata": {"unit": "fog", "tolerance_percentage": 10.0}
    },
    {
        "id": "est:hold_tavolsag",
        "text": "Körülbelül hány ezer kilométer a Föld és a Hold közötti átlagos távolság?",
        "correct": "384",
        "domain": Domain.SCIENCE_TECH,
        "subdomain": "csillagászat",
        "metadata": {"unit": "ezer km", "tolerance_percentage": 15.0}
    },
    {
        "id": "est:foci_jatekido",
        "text": "Hány percből áll a nagypályás labdarúgó mérkőzések rendes játékideje (a két félidő összesen)?",
        "correct": "90",
        "domain": Domain.SPORTS,
        "subdomain": "labdarúgás",
        "metadata": {"unit": "perc", "tolerance_percentage": 0.0}
    }
]


# --- 3. CSÖMÖR, QUIZKRUMPLI, QUIZLAND & HONFOGLALÓ MULTI-CHOICE ---

PUB_ABCD_QUESTIONS = [
    # Film & Popkultúra
    {
        "id": "abcd:film:inception",
        "text": "Ki rendezte a 2010-ben bemutatott 'Eredet' (Inception) című kultikus sci-fi thrillert?",
        "correct": "Christopher Nolan",
        "options": ["Christopher Nolan", "Quentin Tarantino", "Steven Spielberg", "James Cameron"],
        "domain": Domain.POP_CULTURE,
        "subdomain": "film",
    },
    {
        "id": "abcd:music:beatles_abbey",
        "text": "Melyik brit együttes adta ki 1969-ben az ikonikus zebraátkelős borítójú 'Abbey Road' nagylemezt?",
        "correct": "The Beatles",
        "options": ["The Beatles", "The Rolling Stones", "Queen", "Pink Floyd"],
        "domain": Domain.POP_CULTURE,
        "subdomain": "zene",
    },
    {
        "id": "abcd:film:star_wars_year",
        "text": "Melyik évben mutatták be a mozikban az első Star Wars (Egy új remény) filmet?",
        "correct": "1977",
        "options": ["1977", "1975", "1980", "1983"],
        "domain": Domain.POP_CULTURE,
        "subdomain": "film",
    },
    {
        "id": "abcd:film:iron_man",
        "text": "Melyik színész alakította Tony Starkot (Vasembert) a Marvel Moziverzumban?",
        "correct": "Robert Downey Jr.",
        "options": ["Robert Downey Jr.", "Chris Evans", "Chris Hemsworth", "Mark Ruffalo"],
        "domain": Domain.POP_CULTURE,
        "subdomain": "film",
    },
    {
        "id": "abcd:film:saul_fia",
        "text": "Melyik magyar rendező alkotása kapta a legjobb idegen nyelvű filmnek járó Oscar-díjat a 'Saul fia' című filmért?",
        "correct": "Nemes Jeles László",
        "options": ["Nemes Jeles László", "Szabó István", "Enyedi Ildikó", "Tarr Béla"],
        "domain": Domain.ART_MUSIC,
        "subdomain": "magyar_film",
    },
    {
        "id": "abcd:film:titanic_oscars",
        "text": "Hány Oscar-díjat nyert el James Cameron filmje, a Titanic 1998-ban?",
        "correct": "11",
        "options": ["11", "9", "7", "13"],
        "domain": Domain.POP_CULTURE,
        "subdomain": "film",
    },

    # Sport
    {
        "id": "abcd:sport:vb_2022",
        "text": "Melyik ország labdarúgó-válogatottja nyerte meg a 2022-es katari világbajnokságot?",
        "correct": "Argentína",
        "options": ["Argentína", "Franciaország", "Horvátország", "Brazília"],
        "domain": Domain.SPORTS,
        "subdomain": "labdarúgás",
    },
    {
        "id": "abcd:sport:darnyi_arany",
        "text": "Melyik magyar úszólegenda nyert négy aranyérmet vegyesúszásban az olimpiákon szöuli és barcelonai duplázással?",
        "correct": "Darnyi Tamás",
        "options": ["Darnyi Tamás", "Cseh László", "Gyurta Dániel", "Wladár Sándor"],
        "domain": Domain.SPORTS,
        "subdomain": "úszás",
    },
    {
        "id": "abcd:sport:nadal_gs",
        "text": "Hány egyéni Grand Slam-tornát nyert meg a spanyol teniszcsillag, Rafael Nadal pályafutása során?",
        "correct": "22",
        "options": ["22", "20", "24", "18"],
        "domain": Domain.SPORTS,
        "subdomain": "tenisz",
    },
    {
        "id": "abcd:sport:ftc_vvk",
        "text": "Melyik magyar csapat nyerte meg az 1965-ös Vásárvárosok Kupáját a torinói döntőben?",
        "correct": "Ferencváros (FTC)",
        "options": ["Ferencváros (FTC)", "Újpest", "Budapest Honvéd", "MTK"],
        "domain": Domain.SPORTS,
        "subdomain": "labdarúgás",
    },

    # Gasztronómia (Kertvárosi & QuizKrumpli)
    {
        "id": "abcd:gasz:safran",
        "text": "Melyik növény megszárított és kézzel szedett bibéjéből származik a világ legdrágább fűszere, a sáfrány?",
        "correct": "Jóféle sáfrány (Crocus sativus)",
        "options": ["Jóféle sáfrány (Crocus sativus)", "Vaníliaorchidea", "Kardamomfa", "Szerecsendió-virág"],
        "domain": Domain.GASTRONOMY,
        "subdomain": "fűszerek",
    },
    {
        "id": "abcd:gasz:flodni",
        "text": "Melyik hagyományos zsidó-magyar sütemény jellegzetessége a mák, dió, alma és szilvalekvár négyes rétegződése?",
        "correct": "Flódni",
        "options": ["Flódni", "Zserbó", "Rigó Jancsi", "Dobostorta"],
        "domain": Domain.GASTRONOMY,
        "subdomain": "sütemények",
    },
    {
        "id": "abcd:gasz:tiramisu",
        "text": "Milyen különleges olasz krémsajt alkotja a klasszikus tiramisù krémjének az alapját?",
        "correct": "Mascarpone",
        "options": ["Mascarpone", "Ricotta", "Gorgonzola", "Pecorino"],
        "domain": Domain.GASTRONOMY,
        "subdomain": "édességek",
    },

    # Történelem & Földrajz (Honfoglaló, Csömör, Quizland)
    {
        "id": "abcd:hist:mohacs",
        "text": "Melyik évben zajlott a tragikus kimenetelű mohácsi csata?",
        "correct": "1526",
        "options": ["1526", "1456", "1541", "1686"],
        "domain": Domain.HISTORY,
        "subdomain": "magyar_történelem",
    },
    {
        "id": "abcd:hist:berlin_fal",
        "text": "Melyik évben bontották le a berlini falat, ami a hidegháborús megosztottság végét jelezte?",
        "correct": "1989",
        "options": ["1989", "1991", "1985", "1987"],
        "domain": Domain.HISTORY,
        "subdomain": "egyetemes_történelem",
    },
    {
        "id": "abcd:geo:ausztralia_fovaros",
        "text": "Melyik város Ausztrália hivatalos szövetségi fővárosa?",
        "correct": "Canberra",
        "options": ["Canberra", "Sydney", "Melbourne", "Brisbane"],
        "domain": Domain.GEOGRAPHY,
        "subdomain": "fővárosok",
    },
    {
        "id": "abcd:geo:bajkal",
        "text": "Melyik a Föld legmélyebb édesvizű tava, amely a világ folyékony édesvízkészletének kb. 20%-át tárolja?",
        "correct": "Bajkál-tó",
        "options": ["Bajkál-tó", "Tanganyika-tó", "Felső-tó", "Viktória-tó"],
        "domain": Domain.GEOGRAPHY,
        "subdomain": "tavak",
    },
    {
        "id": "abcd:geo:tolna_szekhely",
        "text": "Melyik város Tolna vármegye székhelye?",
        "correct": "Szekszárd",
        "options": ["Szekszárd", "Paks", "Bonyhád", "Tamási"],
        "domain": Domain.GEOGRAPHY,
        "subdomain": "vármegyék",
    },

    # Természettudomány (Honfoglaló Biológia & Kémia, Fizika)
    {
        "id": "abcd:sci:arany_vegyjel",
        "text": "Melyik kémiai elem vegyjele az 'Au' a periódusos rendszerben?",
        "correct": "Arany",
        "options": ["Arany", "Ezüst", "Réz", "Alumínium"],
        "domain": Domain.SCIENCE_TECH,
        "subdomain": "kémia",
    },
    {
        "id": "abcd:sci:kromoszoma",
        "text": "Hány kromoszómát tartalmaz egy egészséges felnőtt ember testi sejtje?",
        "correct": "46",
        "options": ["46", "23", "48", "44"],
        "domain": Domain.SCIENCE_TECH,
        "subdomain": "biológia",
    },
    {
        "id": "abcd:sci:penicillin",
        "text": "Ki fedezte fel az első modern antibiotikumot, a penicillint 1928-ban?",
        "correct": "Alexander Fleming",
        "options": ["Alexander Fleming", "Louis Pasteur", "Robert Koch", "Joseph Lister"],
        "domain": Domain.SCIENCE_TECH,
        "subdomain": "orvostudomány",
    },
    {
        "id": "abcd:sci:inzulin",
        "text": "Melyik emberi belső szerv termeli a vércukorszintet szabályozó inzulint?",
        "correct": "Hasnyálmirigy",
        "options": ["Hasnyálmirigy", "Máj", "Lép", "Mellékvese"],
        "domain": Domain.SCIENCE_TECH,
        "subdomain": "biológia",
    }
]


# --- 4. IGAZ-HAMIS, KAPCSOLAT & SORREND FELADVÁNYOK ---

TRUE_FALSE_QUESTIONS = [
    {
        "id": "tf:kekbalna_meret",
        "text": "A kék bálna a valaha élt legnagyobb ismert állat a Földön, testtömege még a legnagyobb dinoszauruszokét is meghaladja.",
        "correct": "Igaz",
        "options": ["Igaz", "Hamis"],
        "domain": Domain.SCIENCE_TECH,
        "subdomain": "biológia",
    },
    {
        "id": "tf:everest_kozeppont",
        "text": "A Mount Everest a Föld középpontjától mért legtávolabbi pont a bolygó felszínén.",
        "correct": "Hamis",
        "options": ["Igaz", "Hamis"],
        "domain": Domain.GEOGRAPHY,
        "subdomain": "földrajz",
        "metadata": {"explanation": "Az egyenlítői kidudorodás miatt a Chimborazo vulkán csúcsa van a legtávolabb a Föld középpontjától."}
    },
    {
        "id": "tf:mez_romlas",
        "text": "A méz az egyetlen olyan természetes élelmiszer, amely évezredekig sem romlik meg száraz, zárt tárolás mellett.",
        "correct": "Igaz",
        "options": ["Igaz", "Hamis"],
        "domain": Domain.GASTRONOMY,
        "subdomain": "gasztro",
    },
    {
        "id": "tf:sydney_fovaros",
        "text": "Ausztrália fővárosa és kormányzati székhelye Sydney városa.",
        "correct": "Hamis",
        "options": ["Igaz", "Hamis"],
        "domain": Domain.GEOGRAPHY,
        "subdomain": "földrajz",
        "metadata": {"explanation": "Ausztrália fővárosa Canberra."}
    }
]

CONNECTION_QUESTIONS = [
    {
        "id": "conn:nobel_magyarok",
        "text": "Mi a közös a következő személyekben:\nSzent-Györgyi Albert, Kertész Imre, Karikó Katalin, Krausz Ferenc?",
        "correct": "Mindannyian magyar vagy magyar származású Nobel-díjasok",
        "domain": Domain.SCIENCE_TECH,
        "subdomain": "tudománytörténet",
    },
    {
        "id": "conn:duna_fovarosok",
        "text": "Mi a közös a következő európai nagyvárosokban:\nBécs, Pozsony, Budapest, Belgrád?",
        "correct": "Mindannyian a Duna partján fekvő fővárosok",
        "domain": Domain.GEOGRAPHY,
        "subdomain": "folyók",
    },
    {
        "id": "conn:bolygo_kakuktojas",
        "text": "Mi a kakukktojás a következő négy bolygó közül, és miért:\nMerkúr, Vénusz, Jupiter, Mars?",
        "correct": "A Jupiter a kakukktojás, mert az gázóriás, a többi pedig kőzetbolygó",
        "domain": Domain.SCIENCE_TECH,
        "subdomain": "csillagászat",
    }
]

ORDERING_QUESTIONS = [
    {
        "id": "ord:magyar_csatak",
        "text": "Állítsd időrendi sorrendbe a következő történelmi eseményeket a legkorábbitól a legkésőbbi felé haladva!\n(A: Mohácsi csata, B: Magyar honfoglalás, C: 1848-as forradalom, D: Nándorfehérvári diadal)",
        "correct": "B -> D -> A -> C",
        "options": ["B -> D -> A -> C", "B -> A -> D -> C", "D -> B -> A -> C", "A -> B -> D -> C"],
        "domain": Domain.HISTORY,
        "subdomain": "kronológia",
        "metadata": {"sequence": ["B", "D", "A", "C"], "dates": {"B": 895, "D": 1456, "A": 1526, "C": 1848}}
    },
    {
        "id": "ord:irok_szuletes",
        "text": "Állítsd születési sorrendbe a következő magyar írókat a legidősebbtől a legfiatalabb felé haladva!\n(A: Petőfi Sándor, B: Arany János, C: Ady Endre, D: József Attila)",
        "correct": "B -> A -> C -> D",
        "options": ["B -> A -> C -> D", "A -> B -> C -> D", "B -> C -> A -> D", "A -> C -> B -> D"],
        "domain": Domain.LITERATURE,
        "subdomain": "irodalomtörténet",
        "metadata": {"sequence": ["B", "A", "C", "D"], "dates": {"B": 1817, "A": 1823, "C": 1877, "D": 1905}}
    }
]


MATCHING_QUESTIONS = [
    {
        "id": "match:irok_muvek",
        "text": "Párosítsd a magyar írókat leghíresebb klasszikus művükkel!",
        "correct": "Petőfi Sándor: János vitéz, Arany János: Toldi, Mikszáth Kálmán: Szent Péter esernyője, Móricz Zsigmond: Légy jó mindhalálig",
        "options": ["Petőfi Sándor", "Arany János", "Mikszáth Kálmán", "Móricz Zsigmond"],
        "domain": Domain.LITERATURE,
        "subdomain": "klasszikusok",
        "metadata": {
            "pairs": {
                "Petőfi Sándor": "János vitéz",
                "Arany János": "Toldi",
                "Mikszáth Kálmán": "Szent Péter esernyője",
                "Móricz Zsigmond": "Légy jó mindhalálig"
            }
        }
    },
    {
        "id": "match:feltalalok_targy",
        "text": "Párosítsd a világhírű magyar feltalálókat korszakalkotó találmányukkal!",
        "correct": "Bíró László: golyóstoll, Rubik Ernő: bűvös kocka, Jedlik Ányos: dinamó elv, Puskás Tivadar: telefonközpont",
        "options": ["Bíró László", "Rubik Ernő", "Jedlik Ányos", "Puskás Tivadar"],
        "domain": Domain.SCIENCE_TECH,
        "subdomain": "találmányok",
        "metadata": {
            "pairs": {
                "Bíró László": "golyóstoll",
                "Rubik Ernő": "bűvös kocka",
                "Jedlik Ányos": "dinamó elv",
                "Puskás Tivadar": "telefonközpont"
            }
        }
    },
    {
        "id": "match:megyek_szekhelyek",
        "text": "Párosítsd a magyar vármegyéket a vármegyeszékhelyükkel!",
        "correct": "Tolna: Szekszárd, Baranya: Pécs, Csongrád-Csanád: Szeged, Békés: Békéscsaba",
        "options": ["Tolna", "Baranya", "Csongrád-Csanád", "Békés"],
        "domain": Domain.GEOGRAPHY,
        "subdomain": "vármegyék",
        "metadata": {
            "pairs": {
                "Tolna": "Szekszárd",
                "Baranya": "Pécs",
                "Csongrád-Csanád": "Szeged",
                "Békés": "Békéscsaba"
            }
        }
    },
    {
        "id": "match:rendezok_filmek",
        "text": "Párosítsd a világhírű filmrendezőket ikonikus sikerfilmjükkel!",
        "correct": "Christopher Nolan: Eredet, Quentin Tarantino: Ponyvaregény, Steven Spielberg: Jurassic Park, James Cameron: Titanic",
        "options": ["Christopher Nolan", "Quentin Tarantino", "Steven Spielberg", "James Cameron"],
        "domain": Domain.POP_CULTURE,
        "subdomain": "film",
        "metadata": {
            "pairs": {
                "Christopher Nolan": "Eredet",
                "Quentin Tarantino": "Ponyvaregény",
                "Steven Spielberg": "Jurassic Park",
                "James Cameron": "Titanic"
            }
        }
    }
]


class KnowledgeBankExpander:
    """A kérdésbank bővítését és Parquet szinkronizációját végző komponens."""

    def __init__(self, db: DatabaseManager):
        self.db = db
        self.q_repo = QuizQuestionRepository(db)

    def populate_all_curated_questions(self) -> int:
        """Az összes kurált, kocsmakvíz-specifikus kérdés, valamint a tudásgráf entitások betöltése DuckDB-be és Parquet-ba."""
        count = 0

        # 0. Alapvető magyar entitások és relációk biztosítása a gráfban
        try:
            from quizforge.ingestion.wikidata import WikidataIngestor
            from quizforge.knowledge.graph import KnowledgeGraph
            from quizforge.knowledge.relevance import RelevanceEngine
            w_ing = WikidataIngestor()
            e_seed, r_seed = w_ing.get_seed_curated_knowledge()
            kg = KnowledgeGraph(self.db)
            kg.ingest_triplets(e_seed, r_seed)
            w_ing.close()
            RelevanceEngine(self.db).recalculate_relevance_scores()
        except Exception as e:
            print(f"[FIGYELEM] Seed entitás betöltés hiba: {e}")

        # 1. Inquizitor Sztori kérdések (Deduction)
        for item in INQUIZITOR_STORIES:
            q = RawQuizQuestion(
                question_id=item["id"],
                text=item["text"],
                mechanism=QuestionMechanism.DEDUCTION,
                correct_answer=item["correct"],
                options=item["options"],
                domain=item["domain"],
                subdomain=item["subdomain"],
                source_type=SourceType.MANUAL,
                source_name="Inquizitor Curated Bank",
                metadata={"profile": "inquizitor", "type": "sztori"}
            )
            self.q_repo.add_question(q)
            count += 1

        # 2. Inquizitor Szófordítás (ABCD)
        for item in INQUIZITOR_WORDS:
            q = RawQuizQuestion(
                question_id=item["id"],
                text=item["text"],
                mechanism=QuestionMechanism.ABCD,
                correct_answer=item["correct"],
                options=item["options"],
                domain=item["domain"],
                subdomain=item["subdomain"],
                source_type=SourceType.MANUAL,
                source_name="Inquizitor Curated Bank",
                metadata={"profile": "inquizitor", "type": "szófordítás"}
            )
            self.q_repo.add_question(q)
            count += 1

        # 3. Inquizitor Betűkiegészítés (Missing Letters)
        for item in INQUIZITOR_LETTERS:
            q = RawQuizQuestion(
                question_id=item["id"],
                text=item["text"],
                mechanism=QuestionMechanism.MISSING_LETTERS,
                correct_answer=item["correct"],
                options=item["options"],
                domain=item["domain"],
                subdomain=item["subdomain"],
                source_type=SourceType.MANUAL,
                source_name="Inquizitor Curated Bank",
                metadata={"profile": "inquizitor", "type": "betűkiegészítés"}
            )
            self.q_repo.add_question(q)
            count += 1

        # 4. Kertvárosi & Honfoglaló Saccolások (Estimation)
        for item in ESTIMATION_QUESTIONS:
            q = RawQuizQuestion(
                question_id=item["id"],
                text=item["text"],
                mechanism=QuestionMechanism.ESTIMATION,
                correct_answer=item["correct"],
                options=[],
                domain=item["domain"],
                subdomain=item["subdomain"],
                source_type=SourceType.MANUAL,
                source_name="Kertvárosi & Honfoglaló Bank",
                metadata=item.get("metadata", {})
            )
            self.q_repo.add_question(q)
            count += 1

        # 5. Csömör, QuizKrumpli, Quizland, Honfoglaló ABCD kérdések
        for item in PUB_ABCD_QUESTIONS:
            q = RawQuizQuestion(
                question_id=item["id"],
                text=item["text"],
                mechanism=QuestionMechanism.ABCD,
                correct_answer=item["correct"],
                options=item["options"],
                domain=item["domain"],
                subdomain=item["subdomain"],
                source_type=SourceType.MANUAL,
                source_name="Hungarian Pub Quiz Master",
                metadata={"profile_tags": ["csomor", "quizkrumpli", "quizland", "honfoglalo"]}
            )
            self.q_repo.add_question(q)
            count += 1

        # 6. Igaz-Hamis kérdések
        for item in TRUE_FALSE_QUESTIONS:
            q = RawQuizQuestion(
                question_id=item["id"],
                text=item["text"],
                mechanism=QuestionMechanism.TRUE_FALSE,
                correct_answer=item["correct"],
                options=item["options"],
                domain=item["domain"],
                subdomain=item["subdomain"],
                source_type=SourceType.MANUAL,
                source_name="Quizland & QuizKrumpli Bank",
                metadata=item.get("metadata", {})
            )
            self.q_repo.add_question(q)
            count += 1

        # 7. Kapcsolat kérdések
        for item in CONNECTION_QUESTIONS:
            q = RawQuizQuestion(
                question_id=item["id"],
                text=item["text"],
                mechanism=QuestionMechanism.CONNECTION,
                correct_answer=item["correct"],
                options=[],
                domain=item["domain"],
                subdomain=item["subdomain"],
                source_type=SourceType.MANUAL,
                source_name="Quizland Kapcsolat",
                metadata={"profile": "quizland"}
            )
            self.q_repo.add_question(q)
            count += 1

        # 8. Sorrend kérdések
        for item in ORDERING_QUESTIONS:
            q = RawQuizQuestion(
                question_id=item["id"],
                text=item["text"],
                mechanism=QuestionMechanism.ORDERING,
                correct_answer=item["correct"],
                options=item.get("options", []),
                domain=item["domain"],
                subdomain=item["subdomain"],
                source_type=SourceType.MANUAL,
                source_name="Quizland & QuizKrumpli Sorrend",
                metadata=item.get("metadata", {})
            )
            self.q_repo.add_question(q)
            count += 1

        # 9. Párosító kérdések (Matching)
        for item in MATCHING_QUESTIONS:
            q = RawQuizQuestion(
                question_id=item["id"],
                text=item["text"],
                mechanism=QuestionMechanism.MATCHING,
                correct_answer=item["correct"],
                options=item.get("options", []),
                domain=item["domain"],
                subdomain=item["subdomain"],
                source_type=SourceType.MANUAL,
                source_name="QuizKrumpli & Inquizitor Párosító",
                metadata=item.get("metadata", {})
            )
            self.q_repo.add_question(q)
            count += 1

        # Parquet exportálás a tartós megmaradáshoz
        try:
            self.db.export_to_parquet()
        except Exception as e:
            print(f"[FIGYELEM] Parquet export hiba: {e}")

        return count


def expand_database_bank(db: DatabaseManager) -> int:
    """Kényelmi függvény a bank bővítéséhez."""
    expander = KnowledgeBankExpander(db)
    return expander.populate_all_curated_questions()
