# 8_Tudástár.py
import streamlit as st
from datetime import datetime
import pandas as pd
from database import db

def load_lesson_states(user_id):
    """Betölti a felhasználó lecke-teljesítéseit és kvíz eredményeit a MongoDB-ből."""
    lesson_keys = [
        "költségvetés", "be_nem_vallott_kiadasok", "koltsegvetesi_modszerek",
        "bevetel_kiadas_merleg", "mini_rutin_szokas", "penzugyi_kovetes_ritmusa"
    ]
    status = {key: {"completed": False, "quiz_score": None} for key in lesson_keys}

    completed_records = db.lesson_completions.find({"user_id": user_id})
    for record in completed_records:
        if record["lesson_key"] in status:
            status[record["lesson_key"]]["completed"] = record.get("completed", False)
            status[record["lesson_key"]]["quiz_score"] = record.get("quiz_score", None)
    return status

if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("Kérjük, először jelentkezzen be!")
    st.stop()

if 'show_quiz' not in st.session_state:
    st.session_state.show_quiz = False

# Lecke tartalom definíciója
lesson_contents = {
    "költségvetés": {
        "content": [
            "**„Hónap végére mindig elfogy a pénz?” – A költségvetés nem korlát, hanem kulcs a szabadsághoz**\n\n„Hónap végére mindig elfogy a pénz, pedig nem is éltél nagy lábon?” Ha magadra ismertél ebben a mondatban, nem vagy egyedül. Sok ember érez frusztrációt, amikor azt tapasztalja, hogy a fizetés „egyszerűen eltűnik”, pedig nem költekezett különösebben felelőtlenül. Ez azonban nem lustaság, nem pénzügyi analfabetizmus, és nem is balszerencse – gyakran csak annyi történik, hogy nincs egy tudatosan elkészített, átlátható költségvetés.",
            "**Mi is az a költségvetés?**\n\nA költségvetés egyszerűen egy terv arról, hogyan osztod be a bevételeidet. Olyan, mint egy térkép: megmutatja, hová megy a pénzed, és segít eldönteni, merre szeretnéd irányítani. Nem a pénz mennyisége határozza meg, hogy szükséged van-e költségvetésre, hanem az, hogy szeretnéd-e tudni, mire megy el, és mit lehetne vele jobban csinálni.",
            "**Mi történik, ha nincs?**\n\nKépzeld el, hogy egy szitán próbálsz vizet tartani. Lehet bármilyen nagy vödröd – ha lyukas, a víz kifolyik. A költségvetés segít „betömni a lyukakat”, vagyis észrevenni a rejtett kiadásokat, szokássá vált apró költéseket, amik végül komoly összegeket emésztenek fel. Legyen szó napi egy kávéról, havonta elfelejtett előfizetésekről vagy impulzusvásárlásokról, ezek akkor is ott vannak, ha nem figyelsz rájuk.",
            "**Mire jó a költségvetés?**\n\nA költségvetés elsődleges célja nem az, hogy korlátozzon, hanem hogy tudatosabb döntésekhez segítsen hozzá. Ez az az eszköz, amivel:\n* Előre láthatod, milyen fix és változó kiadásaid vannak.\n* Megtervezheted, mennyit tudsz félretenni.\n* Prioritásokat állíthatsz fel: mi fontos számodra, mire szeretnél valóban költeni?\n* Elkerülheted a túlköltést, hiszen láthatóvá válik, hogy mikor léped át a kereteidet.",
            "**Hogyan kezdj neki?**\n\n* Írd össze a havi bevételeidet: fizetés, támogatások, mellékes jövedelmek.\n* Írd össze az összes kiadásodat: lakhatás, élelmiszer, közlekedés, szórakozás, adósság, előfizetések.\n* Kategorizálj: válaszd szét a fix (pl. lakbér) és változó (pl. étkezés, szórakozás) kiadásokat.\n* Hasonlítsd össze a bevételeidet a kiadásokkal: ha több megy ki, mint amennyi bejön, változtatnod kell.\n* Készíts egy reális tervet a következő hónapra – hagyj benne mozgásteret is, ne legyen túl szigorú.\n\nNem kell tökéletesnek lennie az első alkalommal. A költségvetés nem kőbe vésett szabályrendszer, hanem egy rugalmas eszköz, amit idővel egyre jobban fogsz használni.",
            "**Miért éri meg?**\n\nA költségvetés nem elvesz a szabadságodból – épp ellenkezőleg: visszaadja. Ha tudod, mire megy el a pénzed, képes leszel tudatosan irányítani. Ez pedig nemcsak kevesebb stresszt, hanem nagyobb biztonságot, sőt akár megtakarításokat is jelenthet – anélkül, hogy le kellene mondanod minden örömről.",
            "**Összegzés**\n\nA költségvetés nem csak a pénzügyekről szól, hanem a kontrollról, a nyugalomról és a lehetőségről, hogy te döntsd el, mire fordítod az erőforrásaidat. Nem bonyolult elkezdeni – csak egy kis figyelem, papír, toll (vagy egy alkalmazás) kell hozzá. A kérdés nem az, hogy „meg tudod-e csinálni”, hanem az, hogy mikor kezded el."
        ],
        "quiz": [
            {
              "question": "Mi a költségvetés legfőbb célja a lecke szerint?",
              "options": [
                "Korlátozni a felesleges kiadásokat",
                "Megmutatni, mennyi pénz van a számládon",
                "Tudatosabb pénzügyi döntések meghozatalát segíteni",
                "Megakadályozni, hogy elkölts túl sokat szórakozásra"
              ],
              "correct": 2
            },
            {
              "question": "Mi történhet, ha nincs tudatos költségvetésed?",
              "options": [
                "Semmi különös, ha amúgy nem költesz sokat",
                "Valószínűleg minden hónapban marad megtakarításod",
                "Könnyen elszivároghat a pénzed rejtett, apró kiadások miatt",
                "Csak a nagy kiadások kerülhetik el a figyelmedet"
              ],
              "correct": 2
            },
            {
              "question": "Melyik állítás igaz a költségvetés készítésére vonatkozóan?",
              "options": [
                "A fix és változó kiadásokat nem érdemes elkülöníteni",
                "Csak akkor kell költségvetést készítened, ha kevés a jövedelmed",
                "A költségvetésnek mindig szigorúnak kell lennie, hogy működjön",
                "A bevételek és kiadások összehasonlítása segít meghatározni, van-e szükség változtatásra"
              ],
              "correct": 3
            },
            {
              "question": "Miért hasonlítható a költségvetés egy térképhez a lecke szerint?",
              "options": [
                "Mert megmutatja, hol vannak a pénzügyi veszélyzónák",
                "Mert segít követni, hol tartod a pénzed készpénzben",
                "Mert segít eldönteni, merre szeretnéd irányítani a pénzed",
                "Mert minden térképen szerepelnek költségek és bevételek"
              ],
              "correct": 2
             }
                ]
    },
    "be_nem_vallott_kiadasok": {
        "content": [
            "**„Nem is költöttem semmire!” – A be nem vallott kiadások titkos élete**\n\n„Nem is költöttem semmire!” – mondod, miközben a bankszámlád szerint épp most ment el harmincezer forint az „egy kis ez, egy kis az” nevű, láthatatlan kategóriára. A be nem vallott kiadások pont ilyenek: alattomosak, hétköznapiak és meglepően sokba kerülnek. Ideje felfedni őket, mielőtt újra eltűnik a fizetésed nyomtalanul.",
            "**Mik azok a „be nem vallott kiadások”?**\n\nEz nem bűntudatkeltő kifejezés – inkább egy őszinte elnevezés azoknak a költéseknek, amiket nem szívesen ismerünk el magunknak sem. Nem tartjuk őket „igazi” költésnek, mert kicsik, gyorsak, rutinszerűek. Egy reggeli kávé, egy random leárazott póló, egy foodpanda rendelés, vagy az automatikusan levont előfizetések. Nem mindig luxus dolgok – gyakran csak kényelmi döntések, amiket nem tervezünk be.\nA gond nem az, hogy ezek önmagukban hibák lennének – hanem hogy nem számolunk velük tudatosan.",
            "**Miért veszélyesek?**\n\nAz apró, rendszeres költések könnyen láthatatlanná válnak, különösen, ha nem vezetjük őket. De ha összeadod, hamar kijön a havi 20-30-40 ezer forintos „szivárgás”, ami aztán ellehetetleníti a spórolást, a megtakarítást – sőt, gyakran még a hónap végét is. Ezek a tételek nem egyszerre csapnak le, ezért nem tűnnek veszélyesnek. Csak amikor összeadódnak.\nA legnagyobb trükkjük az, hogy nem érezzük őket költésnek, csak „könnyű döntésnek”.",
            "**Hol lapulnak ezek a kiadások?**\n\nÍme néhány gyakori „be nem vallott” kategória:\n\n* Napi apróságok: pékség, kávé, boltban „csak egy valami”.\n* Előfizetések: streaming, edzésapp, tárhely – amiket talán nem is használsz.\n* Kényelmi vásárlás: ételrendelés, taxi, kiszállítási díj.\n* Impulzusvásárlás: „csak most akciós”, „megérdemlem”, „jó lesz még valamire”.\n\nEzek mindegyike önmagában ártalmatlan – de együtt teljesen eltorzíthatják a havi költségvetést.",
            "**Hogyan leplezd le őket?**\n\n**Nézz szembe a bankszámláddal.**\n\nNyisd meg az elmúlt 1-2 hónap tranzakcióit, és színezd ki, mi volt valójában nem tervezett, apróság, vagy impulzus. Ez már önmagában döbbenetes felismeréseket hozhat.\n**Vezess kiadási naplót – pár napig is elég.**\n\nJegyezd fel minden kiadásod, még a legapróbbakat is. Nem kell örökre csinálni, de már néhány nap után látni fogod a mintázatokat.\n**Kategorizálj és nevesíts!**\n\nHozz létre egy „szokásos apróságok” nevű kategóriát, és állíts be rá limitet. Ne csak utólag számold meg – előre határozd meg, mennyit érnek meg neked ezek a kényelmi döntések havonta.\n**Tedd tudatossá!**\n\nKérdezd meg magadtól vásárlás előtt: „Ez now tényleg kell, vagy csak megszokásból veszem meg?” Sokszor már ez a kérdés is elég.",
            "**A tudatosság nem spórolás – hanem szabadság**\n\nA cél nem az, hogy mindent megvonj magadtól. A cél az, hogy te dönts a pénzedről, ne a rutinjaid vagy a figyelmetlenséged tegye meg helyetted. Ha felismered a be nem vallott kiadásaidat, újra uralhatod a pénzügyeidet – és lehet, hogy épp ezek az apróságok nyitják meg az utat a megtakarítások, a nyugodtabb hónapvége vagy egy régóta vágyott cél előtt.",
            "**Zárógondolat**\n\nA pénz nem mindig akkor tűnik el, amikor sokat költünk – néha akkor folyik ki, amikor nem figyelünk oda. Most, hogy tudod, hol keresd, talán te is rájössz: nem a pénzed tűnik el. Csak nem volt szem előtt."
        ],
        "quiz": [
                {
                  "question": "Mi jellemző leginkább a 'be nem vallott kiadásokra' az alábbiak közül?",
                  "options": [
                    "Nagy összegű, előre betervezett vásárlások",
                    "Olyan kiadások, amelyekről szívesen beszélünk másoknak",
                    "Apró, rutinszerű döntések, amelyeket gyakran nem tartunk 'igazi' költésnek",
                    "Rendszeres, fix kiadások, mint a lakbér vagy a rezsi"
                  ],
                  "correct": 2,
                  "explanation": "A 'be nem vallott kiadások' lényege, hogy aprók és rutinszerűek, ezért gyakran nem ismerjük el őket tudatos kiadásként."
                },
                {
                  "question": "Miért veszélyesek a be nem vallott kiadások hosszú távon?",
                  "options": [
                    "Mert mindig luxuscikkekre vonatkoznak",
                    "Mert általában felesleges előfizetésekhez kötődnek",
                    "Mert gyorsan túl lehet őket lépni, ha felismerjük őket",
                    "Mert összeadódva jelentős összeget emészthetnek fel, miközben szinte észrevétlenek"
                  ],
                  "correct": 3,
                  "explanation": "A kis összegek szinte észrevétlenül csúsznak be a kiadások közé, de rendszeresen megismétlődve nagy költséggé válhatnak."
                },
                {
                  "question": "Melyik stratégia segít legjobban a be nem vallott kiadások feltárásában?",
                  "options": [
                    "Csak a nagyobb vásárlásokat kell figyelemmel kísérni",
                    "Érdemes néhány napig kiadási naplót vezetni és kategóriákat létrehozni",
                    "Legjobb teljesen elhagyni az impulzusvásárlásokat",
                    "Minden vásárlás után azonnal visszavinni a terméket, ha megbánjuk"
                  ],
                  "correct": 1,
                  "explanation": "A naplózás és kategorizálás segít tudatosítani a mintázatokat, így felismerhetők az ismétlődő, apró költések."
                },
                {
                  "question": "Hogyan értelmezi a szöveg a 'tudatosságot' a költési szokásokban?",
                  "options": [
                    "Minden apró vásárlás kerülését jelenti a spórolás érdekében",
                    "A kiadások teljes megszüntetését a megtakarítás maximalizálásához",
                    "A tudatos döntéshozatalt, ahol mi kontrolláljuk, mire megy el a pénzünk",
                    "A szigorú pénzügyi szabályok betartását minden körülmények között"
                  ],
                  "correct": 2,
                  "explanation": "A szöveg szerint a tudatosság azt jelenti, hogy te hozod meg a döntést a pénz sorsáról, nem pedig a szokások vagy figyelmetlenség."
                }
              ]
    },
    "koltsegvetesi_modszerek": {
        "content": [
            "**Költségvetés, ami működik – A legnépszerűbb módszerek, laikusoknak**\n\nA pénzügyi zűrzavar nem feltétlenül a fegyelmezetlenségen múlik – gyakran csak hiányzik egy jó módszer, ami segít keretben tartani a pénzügyeinket. Ha csak sodródsz, és hónapról hónapra próbálod túlélni a kiadásaidat, nem veled van a baj – valószínűleg még nem találtad meg a hozzád illő költségvetési rendszert. Ebben a cikkben bemutatunk néhány egyszerű, mégis hatékony megközelítést, amelyek segíthetnek, hogy végre átlásd, mire megy el a pénzed.",
            "**Miért van szükség módszerre?**\n\nA költségvetés célja nem az, hogy „megmondja, mire költhetsz” – hanem hogy **te mondd meg magadnak**, mire szeretnél költeni. Ehhez viszont rendszer kell. Olyan eszköz, ami egyszerre ad áttekinthetőséget és irányítást. Mert ha a pénzügyek csak fejben „vannak valahogy”, abból gyorsan lesz frusztráció, viták és hónap végi meglepetések.",
            "**1. 50/30/20 szabály – Egyszerű és rugalmas**\n\nEz a módszer három nagy kategóriába osztja a bevételed:\n- **50%**: alapvető szükségletek (lakhatás, rezsi, élelmiszer)\n- **30%**: személyes kiadások (szórakozás, ruházkodás, étterem)\n- **20%**: megtakarítás és adósságtörlesztés\n\n**Kinek jó?**\nHa most kezded a költségvetést, és még nem szeretnél tételesen számolgatni, ez a rendszer segít arányokat látni, miközben elég rugalmas marad.",
            "**2. Borítékos módszer – Kézzelfogható kontroll**\n\nEbben a klasszikus rendszerben minden költségkategóriára (pl. élelmiszer, közlekedés, szórakozás) egy külön „borítékba” teszed a havi keretet – régen ezt valóban készpénzben tették, ma digitális változata is létezik.\n\n**Hogyan működik?**\nCsak addig költhetsz egy kategóriára, amíg van benne „borítékpénz”. Ha elfogy, várnod kell a következő hónapig.\n\n**Kinek jó?**\nAnnak, aki hajlamos túlköltekezni bizonyos területeken, és segít neki, ha látja a kereteket „kifogyni”.",
            "**3. Nullegyenleges költségvetés – Minden forintnak neve van**\n\nEz a módszer azt mondja: **minden forintod kapjon feladatot**. Vagyis a bevételedet teljes egészében elosztod a hónap elején – akár kiadásra, akár megtakarításra, akár befektetésre. A hónap végén a „szabadon maradt” összeg: 0 Ft.\n\n**Kinek jó?**\nHa pontosan szeretnéd tudni, hova megy a pénzed, és maximalizálnád a tudatosságot. Ideális azoknak is, akik konkrét célokra gyűjtenek.",
            "**Hogyan válaszd ki a megfelelőt?**\n\nA jó költségvetési módszer **nem az, amit mások használnak – hanem amit te is követni tudsz hosszú távon**. Próbálj ki egyet pár hétig, és figyeld meg: ad-e tisztánlátást? Segít-e előre tervezni? Könnyen fenntartható számodra?",
            "**Zárógondolat**\n\nA költségvetés nem korlát, hanem eszköz. Segít, hogy a pénzedet arra használd, ami valóban számít neked. Találd meg a hozzád illő módszert – és kezdj el nemcsak pénzt kezelni, hanem pénzügyi szabadságot építeni."
        ],
        "quiz": [
                  {
                    "question": "Mi a költségvetés elsődleges szerepe a lecke szerint?",
                    "options": [
                      "A kiadások szigorú korlátozása",
                      "A megtakarítási célok maximalizálása",
                      "Annak eldöntése, hogy te mire szeretnél költeni",
                      "Az adósságok mihamarabbi visszafizetése"
                    ],
                    "correct": 2,
                    "explanation": "A költségvetés célja nem korlátozás, hanem az, hogy te irányítsd tudatosan a pénzed felhasználását – a lecke ezt hangsúlyozza."
                  },
                  {
                    "question": "Milyen arányokkal dolgozik az 50/30/20 szabály?",
                    "options": [
                      "50% alapvető szükségletek, 20% személyes kiadások, 30% megtakarítás",
                      "50% megtakarítás, 30% szükségletek, 20% szórakozás",
                      "50% szükségletek, 30% személyes kiadások, 20% megtakarítás/adósságtörlesztés",
                      "33% szükségletek, 33% vágyak, 34% megtakarítás"
                    ],
                    "correct": 2,
                    "explanation": "A helyes arány: 50% szükségletek, 30% személyes kiadások, 20% megtakarítás/adósságtörlesztés – ez segít egyszerű, de hatékony pénzügyi képet adni."
                  },
                  {
                    "question": "Melyik módszert érdemes választani, ha hajlamos vagy túlköltekezni egyes kategóriákban, és szükséged van vizuális kontrollra?",
                    "options": [
                      "50/30/20 szabály",
                      "Borítékos módszer",
                      "Nullegyenleges költségvetés",
                      "Rendszeres készpénzes fizetés minden vásárláskor"
                    ],
                    "correct": 1,
                    "explanation": "A borítékos módszer segít látványosan érzékelni a keretek kimerülését, így visszafogja az impulzív költést – pontosan ezt célozza."
                  },
                  {
                    "question": "Mi az egyik fő előnye a nullegyenleges költségvetésnek?",
                    "options": [
                      "Csak megtakarításokra fókuszál, a többit figyelmen kívül hagyja",
                      "A hónap végén marad pénz a szórakozásra",
                      "Segít előre meghatározni minden forint szerepét, így nincs 'elveszett' összeg",
                      "Nem igényel előre tervezést, a költések spontán alakulnak"
                    ],
                    "correct": 2,
                    "explanation": "A nullegyenleges költségvetés lényege, hogy minden forintnak nevet adsz – így nincs 'maradék' vagy kontrollálatlan pénzmozgás."
                  }
                ]
    },
    "bevetel_kiadas_merleg": {
        "content": [
            "**Bevétel jó, kiadás rossz – de mi van a kettő között?**\n\nA pénzügyi mérleged az egyik legfontosabb mutató, mégis ritkán beszélünk róla. Miközben sokan hajtanak magasabb fizetésre, vagy próbálják lefaragni a kiadásaikat, a lényeg gyakran elsikkad: a kettő közötti különbség számít igazán. Ez a mérleged – vagyis az, hogy a hónap végén marad-e pénz a számládon. És ha igen, mennyi.",
            "**Mi az a pénzügyi mérleg?**\n\nEgyszerűbben nem is lehetne megfogalmazni: **a pénzügyi mérleged a bevételeid és kiadásaid különbsége**. Ha több a bevételed, mint amennyit elköltesz, akkor pozitív mérlegről beszélünk. Ha viszont többet költesz, mint amennyit keresel, akkor negatív a mérleged – és ezt nem sokáig lehet büntetlenül csinálni.",
            "**Miért fontos ezt figyelni?**\n\nMert a pénzügyi mérleged az, ami mozgásteret ad. Ez az, ami lehetővé teszi a megtakarítást, az előre tervezést, vagy akár a váratlan kiadások fedezését. Ha nem figyelsz rá, akkor könnyen abba a hibába esel, hogy „elég a fizetésem” – miközben valójában minden hónap végén mínuszba csúszol. A jó hír: a mérleget te alakítod.",
            "**Hogyan számold ki a saját mérleged?**\n\n1. Gyűjtsd össze a **teljes havi bevételedet** – ide számít minden, amit rendszeresen kapsz: fizetés, ösztöndíj, albérleti bevétel, stb.\n2. Gyűjtsd össze az **összes havi kiadásodat** – lakhatás, rezsi, élelmiszer, utazás, előfizetések, szórakozás, apróságok.\n3. Vond ki a kiadásokat a bevételből. A kapott szám a havi mérleged.\n\nHa pozitív: jól állsz. Ha nulla körüli: van mit javítani. Ha negatív: azonnali beavatkozásra van szükség.",
            "**Mit kezdj vele?**\n\nA cél: minden hónapban **pozitív mérleget** elérni, még ha csak néhány ezer forinttal is. Ez az a pénz, amit félretehetsz, célokra fordíthatsz, vagy vésztartalékot képezhetsz belőle. De ehhez tudatosság kell. Nézd meg, hol csúszik el a mérleged – sokszor a probléma nem a bevétel kevés, hanem a kiadások rendszertelenek vagy túlzóak.",
            "**Gyakori tévhitek**\n\n„Majd ha többet keresek, jobb lesz a mérlegem.” – Nem feltétlenül. A kiadások hajlamosak együtt nőni a bevételekkel, ha nincs kontroll. A pénzügyi egyensúly nem a jövedelem szintjén múlik, hanem azon, **hogyan osztod be azt, amid van**. Sok kis keresetű embernek van pozitív mérlege – és sok nagy keresetű ember él fizetéstől fizetésig.",
            "**Kezdd el most**\n\nNem kell túlbonyolítani. Elég bevinned a NestCash-re a pénzmozgásaidat. A lényeg, hogy **láthatóvá tedd**: hol tartasz most, és merre szeretnél haladni. A pénzügyi mérleg nem ítélkezik – csak visszajelzést ad arról, hogy a pénzed **neked dolgozik-e, vagy ellened**.",
            "**Zárógondolat**\n\nA pénzügyi biztonság nem varázslat, hanem aránykérdés. A bevételek, kiadások és a különbségük mindennapi döntéseink lenyomatai. Ha te hozod meg ezeket a döntéseket tudatosan, akkor a pénzügyi mérleged idővel a szabadságod térképévé válik."
        ],
        "quiz": [
                  {
                    "question": "Mi a pénzügyi mérleg legegyszerűbb meghatározása a lecke szerint?",
                    "options": [
                      "A kiadások százalékos aránya a bevételhez képest",
                      "A havi pénzmozgások részletes nyilvántartása",
                      "A bevételek és a kiadások különbsége",
                      "Az elérhető megtakarítási lehetőségek listája"
                    ],
                    "correct": 2
                  },
                  {
                    "question": "Miért lehet veszélyes az a gondolat, hogy majd több bevétel automatikusan jobb mérleget eredményez?",
                    "options": [
                      "Mert a magasabb jövedelemmel több adó is jár",
                      "Mert a kiadások hajlamosak együtt növekedni a bevételekkel, ha nincs kontroll",
                      "Mert a magasabb jövedelmet nem lehet pontosan követni",
                      "Mert a bankköltségek is arányosan emelkednek"
                    ],
                    "correct": 1
                  },
                  {
                    "question": "Tegyük fel, hogy valaki minden hónapban ugyanannyit keres, de mégis gyakran mínuszba kerül. Mi lehet ennek legvalószínűbb oka a lecke alapján?",
                    "options": [
                      "A bevétel túl alacsony ahhoz, hogy bármit félretegyen",
                      "Túl kevés előfizetése van, ami megnehezíti a nyomon követést",
                      "A kiadások rendszertelenek és nem tudatosan kezeltek",
                      "Nincs elég külön kategória a kiadásokhoz"
                    ],
                    "correct": 2
                  },
                  {
                    "question": "Melyik állítás fejezi ki leginkább a lecke zárógondolatát a pénzügyi mérlegről?",
                    "options": [
                      "A pénzügyi mérleg a gazdagság kulcsa, ha jól vezetik",
                      "A pénzügyi biztonság csak a bevételek növelésén múlik",
                      "A pénzügyi mérleg az ítélet eszköze, ami megmutatja, mennyire vagy felelős",
                      "A pénzügyi mérleg tudatos döntések lenyomata, és idővel a szabadság térképévé válhat"
                    ],
                    "correct": 3
                  }
                ]

    },
    "mini_rutin_szokas": {
        "content": [
            "**Tökéletesség helyett ismétlés: a pénzügyi szokások valódi titka**\n\nSokan próbálják vezetni a kiadásaikat – pár napig. Aztán jön egy fáradt este, egy hosszú hét, és máris eltűnik a jó szándék. A megoldás? Ne akarj tökéletes lenni, csak tedd egyszerűvé. A mini-rutinok segítenek abban, hogy a pénzügyi önfegyelem ne küzdelem, hanem reflex legyen.",
            "**Miért nem működnek a nagy elhatározások?**\n\nAz új év elején vagy egy fizetés utáni napon sokan éreznek kedvet az „újrakezdéshez”: mostantól minden kiadást vezetni fogok, költségvetést készítek, félreteszek. A probléma, hogy ezek gyakran túl ambiciózus célok. Nagy elvárások, amikhoz idő, energia és mentális kapacitás kell – és ezekből a hétköznapokban kevés van. Így a jó szándék gyorsan elhalványul.",
            "**A szokás nem döntés – hanem rendszer**\n\nAhhoz, hogy egy pénzügyi gyakorlat szokássá váljon, nem kell naponta sok időt rászánnod. Az agyunk akkor tanulja meg egy viselkedés ismétlését, ha az **kicsi**, **könnyen kivitelezhető** és **visszatérő**. Ez a mini-rutin lényege: egy olyan apró tevékenység, amit szinte automatikusan be tudsz illeszteni a napodba, például este fogmosás után vagy reggel kávé mellett.",
            "**Példák pénzügyi mini-rutinokra**\n\n- Írd fel este a nap három legnagyobb kiadásod. \n- Minden reggel nézd meg az egyenleged, mielőtt megnyitod a közösségi médiát.\n- Hetente egyszer 5 percet szánj arra, hogy átnézed, voltak-e felesleges költéseid.\n\nNem a pontosság számít, hanem a rendszeresség. Ezekből lesznek a szokások, amikből végül pénzügyi önismeret és tudatosság épül.",
            "**Hogyan kezdj hozzá?**\n\n1. **Válassz egyetlen mini-rutint.** Ne tervezd túl, csak egy dolgot válassz.\n2. **Kapcsold egy meglévő szokáshoz.** Például ha reggelente kávézol, tedd mellé a pénzügyi rutint is.\n3. **Legyen olyan egyszerű, hogy ne tudj kifogást találni.** Egy mozdulat, egy lista, egy gondolat – ennyi elég.\n4. **Add hozzá NestCash-en a szokásaidhoz, és pipáld ki minden nap, ha megcsináltad.** Ez láthatóvá teszi a fejlődést, és motivál.",
            "**Miért működik ez jobban?**\n\nMert a mini-rutin nem igényel döntést, energiát, vagy épp szupernapot. Akkor is működik, amikor fáradt vagy, amikor késésben vagy, vagy amikor nincs kedved semmihez. És pont ez a lényege: **nem rajtad múlik, hanem a szokáson**. Ez az alapja minden hosszú távú pénzügyi eredménynek.",
            "**Zárógondolat**\n\nA pénzügyi önfegyelem nem veleszületett tulajdonság – hanem apró, napi ismétlések eredménye. A mini-rutin nem gyors megoldás, hanem stabil alap. És ha ma este csak annyit csinálsz, hogy leírod: „ma mire költöttem a legtöbbet?”, akkor már elindultál az úton. Kicsiben kezdődik – és nagyban változtat."
        ],
        "quiz": [
                   {
                     "question": "Mi a pénzügyi mini-rutinok legfőbb előnye a leckében olvasottak szerint?",
                     "options": [
                       "Pontos és részletes költségvetést eredményeznek",
                       "Segítenek elkerülni a nagyobb kiadásokat",
                       "Egyszerűségükkel és rendszerességükkel szokást építenek",
                       "Helyettesítik a havi pénzügyi tervezést"
                     ],
                     "correct": 2,
                     "explanation": "A lecke szerint a mini-rutin lényege, hogy kis, könnyű, ismételhető lépésekből szokás válik, ami hosszú távon alakítja ki a pénzügyi tudatosságot."
                   },
                   {
                     "question": "Miért buknak el gyakran az újévi pénzügyi elhatározások a lecke szerint?",
                     "options": [
                       "Mert az emberek nem tudják, hogyan készítsenek költségvetést",
                       "Mert túl kevés pénzük van megtakarítani",
                       "Mert túl magas elvárásokkal és kevés energiával indulnak neki",
                       "Mert a banki alkalmazások nem elég hatékonyak"
                     ],
                     "correct": 2,
                     "explanation": "A szöveg kiemeli, hogy a túl ambiciózus célok, és a hétköznapi energiahiány gyakran akadályozzák a hosszú távú kitartást."
                   },
                   {
                     "question": "Melyik lehet a legjobb módja egy új pénzügyi mini-rutin beépítésének?",
                     "options": [
                       "Egyszerre több pénzügyi szokást elkezdeni",
                       "Egy bonyolult rendszer kidolgozása még az elején",
                       "Egy egyszerű tevékenységet hozzákötni egy meglévő szokáshoz",
                       "Csak hétvégén foglalkozni a pénzügyekkel, amikor van idő"
                     ],
                     "correct": 2,
                     "explanation": "A lecke azt tanácsolja, hogy válasszunk egyetlen, nagyon egyszerű mini-rutint, és kapcsoljuk össze egy meglévő napi szokással – ettől válik automatikussá."
                   },
                   {
                     "question": "Melyik állítás tükrözi legjobban a lecke zárógondolatát?",
                     "options": [
                       "A pénzügyi siker a részletes elemzéseken és jelentéseken múlik",
                       "A pénzügyi önfegyelem veleszületett képesség, amit nem lehet tanulni",
                       "A legfontosabb, hogy pontosan kövessük a költségvetést minden nap",
                       "A szokások kis ismétléseken alapulnak, nem tökéletes teljesítményen"
                     ],
                     "correct": 3,
                     "explanation": "A zárógondolat szerint a pénzügyi önfegyelem nem tökéletességen, hanem napi, apró ismétléseken alapul – ez a hosszú távú siker kulcsa."
                   }
                 ]
    },
    "penzugyi_kovetes_ritmusa": {
        "content": [
            "**A pénzügyek követésének ritmusa – a szorongás és a káosz között**\n\nTúl gyakran követed a pénzügyeidet? Az már szorongáshoz vezethet. Túl ritkán? Az már káoszt jelent. A cél nem a végletek, hanem egy fenntartható pénzügyi figyelem, ami támogat, nem kontrollál. Ebben a leckében megmutatjuk, milyen gyakoriság működik a legtöbb embernek – és hogyan találhatod meg a saját ritmusodat.",
            "**Miért fontos a ritmus?**\n\nA pénzügyeid figyelemmel kísérése olyan, mint egy egészséges étkezés vagy a mozgás: ha teljesen elhanyagolod, baj lesz, ha túlzásba viszed, az is fárasztó és fenntarthatatlan. Az ideális gyakoriság nem azt jelenti, hogy állandóan figyeled a bankszámládat – hanem hogy épp annyit nézel rá, amennyi segít a tudatosságban, de nem veszi el az életed örömét.",
            "**Túl gyakori követés: a kontroll illúziója**\n\nVannak, akik naponta többször is ellenőrzik a bankszámlájukat, számolgatják a kiadásokat, újraszámolják a költségvetést. Ez kezdetben megnyugtatónak tűnhet, de hosszú távon stresszhez, döntési fáradtsághoz és túlzott aggodalomhoz vezethet. A pénz figyelése helyett épp az lesz a hatás, hogy a pénz figyel téged – minden mozdulatodat uralja.",
            "**Túl ritka követés: a láthatatlan problémák**\n\nA másik véglet azok, akik hónapokig nem néznek rá a kiadásaikra. Így könnyen felhalmozódnak a rejtett előfizetések, az impulzusvásárlások, vagy épp a kis apróságok, amik együttesen viszik el a pénzt. Amikor végül ránéznek a számlára, gyakran jön a sokk: „hova tűnt a pénzem?” – és ezzel a motiváció is gyorsan elillan.",
            "**Milyen gyakoriság a legjobb?**\n\nNincsen mindenki számára univerzális válasz, de van néhány bevált ritmus:\n\n- **Napi 1 perc:** Egy gyors ránézés az egyenlegre vagy kiadásokra – nem elemzés, csak tudatosság.\n- **Heti 5-10 perc:** Rövid áttekintés: mi ment ki, mi jön még, mire kell figyelni jövő héten.\n- **Havi 30-60 perc:** Részletesebb áttekintés: célok, megtakarítás, költségvetés felülvizsgálata.\n\nEz a három szint együtt adja a pénzügyi önismeret ritmusát: nem túl sok, nem túl kevés.",
            "**Találd meg a saját ritmusod**\n\nHa kezdő vagy, a heti egyszeri átnézés már hatalmas előrelépés. Ha haladóbb vagy, a napi mikroszint segíthet finomítani a döntéseket. A lényeg, hogy a pénzügyeid követése ne legyen nyomasztó projekt, hanem támogató szokás – mint egy GPS: nem irányít, csak mutatja, merre jársz.",
            "**Zárógondolat**\n\nA pénzügyi tudatosság nem a tökéletes kontrollról szól, hanem arról, hogy ne érjenek meglepetések. Ahogy a tested is jelez, ha túlterhelt vagy elhanyagolt, úgy a pénzügyeid is „beszélnek” – csak figyelni kell rájuk a megfelelő időben. Egy jól beállított követési ritmus segít, hogy ne a pénzed uraljon téged, hanem te urald a pénzed."
        ],
        "quiz": [
              {
                "question": "Mi a pénzügyi követés megfelelő ritmusának fő célja a lecke szerint?",
                "options": [
                  "A kiadások teljes megszüntetése",
                  "A bankszámla folyamatos ellenőrzése",
                  "A tudatos figyelem kialakítása túlzás nélkül",
                  "A pénzügyi döntések automatizálása"
                ],
                "correct": 2
              },
              {
                "question": "Mi lehet a túl gyakori pénzügyi követés egyik veszélye a lecke szerint?",
                "options": [
                  "A rejtett kiadások elsikkadása",
                  "A megtakarítások elmaradása",
                  "A pénzügyek kontrollálhatatlanná válása",
                  "Stresszhez és döntési fáradtsághoz vezethet"
                ],
                "correct": 3
              },
              {
                "question": "Ha valaki hetente 5-10 percet szán a pénzügyei áttekintésére, akkor mit tesz leginkább?",
                "options": [
                  "Részletes költségvetést készít",
                  "Átnézi a hosszú távú pénzügyi célokat",
                  "Áttekinti az aktuális mozgásokat és felkészül a következő hétre",
                  "Automatizálja a megtakarításokat"
                ],
                "correct": 2
              },
              {
                "question": "Melyik állítás fejezi ki legjobban a lecke zárógondolatát?",
                "options": [
                  "A pénzügyek teljes kontroll alatt tartása csökkenti a szorongást",
                  "A pénzügyi tudatosság lényege, hogy minden kiadást előre meg kell tervezni",
                  "A megfelelő követési ritmus segít elkerülni a meglepetéseket és megerősíti az irányítást",
                  "A napi szintű követés az egyetlen megbízható módja a pénzügyi biztonságnak"
                ],
                "correct": 2
              }
            ]

    }
}


st.set_page_config(layout="wide")

# Oldal fejléc
col1, col2 = st.columns([1, 4])
with col1:
    st.image("https://i.ytimg.com/vi/vhl9wWLv2Yo/hqdefault.jpg", width=100)  # Ide jöhet a Tudástár ikon
with col2:
    st.title("Tudástár (szemléltető oldal, fejlesztés alatt...)")
    st.caption("Rövid, könnyen emészthető pénzügyi leckék - Mindennapi pénzügyi tudatosságért")

# Gamifikációs elemek
st.subheader("🏆 Saját tanulási statisztikáim")
with st.container(border=True):
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Tanulási streak", "🔥 3 nap")
    with col2:
        # A teljesített leckék számának dinamikus frissítése
        if 'completed_lessons' not in st.session_state:
            st.session_state.completed_lessons = 0
        st.metric("Teljesített leckék", f"{st.session_state.completed_lessons}/{len(lesson_contents)}")

st.divider()

# Napi tanulási ajánlás
st.subheader("⏳ Tanulj ma is 5 perc alatt:")
with st.container(border=True):
    st.markdown("**Mi az a vésztartalék, és hogyan építsd fel?**")
    st.caption("2 perces lecke · Kezdő szint")
    if st.button("Tanulás megkezdése", key="daily_lesson"):
        st.session_state.current_lesson = "vésztartalék"

st.divider()

# Választó sáv a témakörök között
selected_category = st.radio(
    "Témakörök:",
    options=[{"name": "Pénzügyi alapok", "value": "alapok"}, 
             {"name": "Spórolás", "value": "spórolás"}, 
             {"name": "Pénzügyi gondolkodás", "value": "gondolkodás"}, 
             {"name": "Haladó", "value": "haladó"}, 
             {"name": "Gyakorlat", "value": "gyakorlati"}, 
             ],
    format_func=lambda x: x["name"],
    horizontal=True
)["value"]

st.divider()

# Aktuális lecke állapota
if 'current_lesson_key' not in st.session_state:
    st.session_state.current_lesson_key = None # Jelenleg olvasott lecke kulcsa
if 'lesson_page' not in st.session_state:
    st.session_state.lesson_page = 0
st.session_state.lesson_completion_status = load_lesson_states(st.session_state.user_id)
st.session_state.completed_lessons = sum(pd.DataFrame(st.session_state.lesson_completion_status.values())['completed'])

#%% Segéd függvény a leckék kezeléséhez
def display_lesson(lesson_key, lesson_title):
    if st.session_state.current_lesson_key == lesson_key:
        current_lesson = lesson_contents[lesson_key]
        
        # Kvíz megjelenítése
        if st.session_state.get('show_quiz', False):
            st.markdown("### 📝 Tudáspróba")
            
            # Ha van már eredmény, azt mutatjuk
            if st.session_state.lesson_completion_status[lesson_key]["quiz_score"] is not None:
                st.success(f"✔️ Ezt a kvízt már teljesítetted! Pontszám: {st.session_state.lesson_completion_status[lesson_key]['quiz_score']}%")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Kvíz újrakezdése", key=f"retry_quiz_{lesson_key}"):
                        # Teljes állapot reset a kvízhez
                        st.session_state.lesson_completion_status[lesson_key]["quiz_score"] = None
                        st.session_state.show_quiz = True  # Biztosítjuk, hogy a kvíz megjelenjen
                        # Töröljük a korábbi válaszokat
                        if 'quiz_answers' in st.session_state:
                            del st.session_state.quiz_answers
                        st.rerun()
                with col2:
                    if st.button("Vissza a Tudástárba", key=f"back_to_knowledge_{lesson_key}"):
                        st.session_state.current_lesson_key = None
                        st.session_state.show_quiz = False
                        st.rerun()
                # JAVÍTÁS: Eltávolítjuk a return-t itt, hogy a kvíz kérdések megjelenjenek
                # return  # Ez volt a probléma!
            
            # Kvíz kitöltése
            # Inicializáljuk a válaszokat, ha még nem léteznek
            if 'quiz_answers' not in st.session_state:
                st.session_state.quiz_answers = {}
            
            # Kvíz kérdések megjelenítése
            for i, question in enumerate(current_lesson["quiz"]):
                st.write(f"**{i+1}. {question['question']}**")
                
                # Alapértelmezett válasz a session state-ből vagy None
                default_answer = st.session_state.quiz_answers.get(i, None)
                answer = st.radio(
                    f"Válasz {i+1}",
                    options=question["options"],
                    key=f"quiz_{lesson_key}_{i}",
                    index=question["options"].index(default_answer) if default_answer in question["options"] else None
                )
                
                # Mentjük a választ
                if answer:
                    st.session_state.quiz_answers[i] = answer
            
            # Gombok a kvíz alján
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Kvíz beküldése", key=f"submit_quiz_{lesson_key}"):
                    # Ellenőrizzük, hogy minden kérdés meg van-e válaszolva
                    if len(st.session_state.quiz_answers) < len(current_lesson["quiz"]):
                        st.warning("Kérlek válaszolj meg minden kérdést!")
                    else:
                        # Pontszám számítás
                        score = 0
                        for i, question in enumerate(current_lesson["quiz"]):
                            if st.session_state.quiz_answers[i] == question["options"][question["correct"]]:
                                score += 1
                        
                        quiz_score = int((score / len(current_lesson["quiz"])) * 100)
                        
                        # Mentés az adatbázisba és session state-be
                        st.session_state.lesson_completion_status[lesson_key]["completed"] = True
                        st.session_state.lesson_completion_status[lesson_key]["quiz_score"] = quiz_score
                        
                        db.lesson_completions.update_one(
                            {"user_id": st.session_state.user_id, "lesson_key": lesson_key},
                            {"$set": {
                                "completed": True,
                                "quiz_score": quiz_score,
                                "completed_at": datetime.now()
                            }},
                            upsert=True
                        )
                        
                        # Frissítjük a teljesített leckék számát
                        if not st.session_state.lesson_completion_status.get(lesson_key, {}).get("completed", False):
                            st.session_state.completed_lessons += 1
                        
                        # Kvíz elrejtése a beküldés után
                        st.session_state.show_quiz = False
                        
                        st.rerun()
            with col2:
                if st.button("Vissza a leckéhez", key=f"back_to_lesson_{lesson_key}"):
                    st.session_state.show_quiz = False
                    st.rerun()
        
        # Normál lecke megjelenítése
        else:
            total_pages = len(current_lesson["content"])
            current_page_display = st.session_state.lesson_page + 1

            # Progress bar - biztosítjuk, hogy a lesson_page ne menjen túl a határon
            if st.session_state.lesson_page >= total_pages:
                st.session_state.lesson_page = total_pages - 1
            
            current_page_display = st.session_state.lesson_page + 1
            st.write(f"Oldal: {current_page_display}/{total_pages}")
            col_head1, col_head2 = st.columns([5, 2])
            col_head1.progress(min(current_page_display / total_pages, 1.0))
            if col_head2.button("Lecke elhagyása"):
                st.session_state.current_lesson_key = None
                st.rerun()
            
            st.markdown(current_lesson["content"][st.session_state.lesson_page])

            col_nav1, col_nav2 = st.columns(2)
            with col_nav1:
                if st.session_state.lesson_page > 0:
                    if st.button("Előző", key=f"prev_page_{lesson_key}"):
                        st.session_state.lesson_page -= 1
                        st.rerun()
            with col_nav2:
                if st.session_state.lesson_page < len(current_lesson["content"]) - 1:
                    if st.button("Következő", key=f"next_page_{lesson_key}"):
                        st.session_state.lesson_page += 1
                        st.rerun()
                else:
                    if st.button("Lecke befejezése", key=f"complete_{lesson_key}"):
                        if not st.session_state.lesson_completion_status.get(lesson_key, {}).get("completed", False):
                            st.session_state.completed_lessons += 1
                        st.session_state.lesson_completion_status[lesson_key]["completed"] = True
                        
                        db.lesson_completions.update_one(
                            {"user_id": st.session_state.user_id, "lesson_key": lesson_key},
                            {"$set": {
                                "completed": True, 
                                "completed_at": datetime.now()
                            }},
                            upsert=True
                        )
                        
                        st.session_state.current_lesson_key = None
                        st.rerun()
            
            # Kvíz indítása gomb
            if st.session_state.lesson_page == len(current_lesson["content"]) - 1 and current_lesson["quiz"]:
                if st.button("Tudáspróba megkezdése", key=f"start_quiz_{lesson_key}"):
                    st.session_state.show_quiz = True
                    # Reseteljük a kvíz állapotát
                    if 'quiz_answers' in st.session_state:
                        del st.session_state.quiz_answers
                    st.rerun()
    else:
        with st.expander(lesson_title):
            completion_status = st.session_state.lesson_completion_status[lesson_key]
            current_lesson = lesson_contents[lesson_key]
            
            if not completion_status["completed"]:
                if st.button("Lecke elkezdése", key=f"start_{lesson_key}"):
                    st.session_state.current_lesson_key = lesson_key
                    st.session_state.lesson_page = 0
                    st.session_state.show_quiz = False
                    st.rerun()
            else:
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Lecke újrakezdése", key=f"restart_{lesson_key}"):
                        st.session_state.current_lesson_key = lesson_key
                        st.session_state.lesson_page = 0
                        st.session_state.show_quiz = False
                        st.rerun()
                with col2:
                    if current_lesson["quiz"]:
                        if st.button("Tudáspróba", key=f"quiz_{lesson_key}"):
                            st.session_state.current_lesson_key = lesson_key
                            st.session_state.show_quiz = True
                            # Reseteljük a kvíz állapotát
                            if 'quiz_answers' in st.session_state:
                                del st.session_state.quiz_answers
                            st.rerun()
                
                if completion_status["quiz_score"] is not None:
                    st.success(f"✔️ Legjobb eredményed: {completion_status['quiz_score']}%")
                else:
                    st.success("✔️ Lecke elvégezve")

#%% Témakörönkénti leckék megjelenítése
if selected_category == "alapok":
    st.subheader("🧱 ALAPOK – „Tudd, hol állsz”")
    st.caption("🟢 Kezdő szint")
    
    st.markdown("#### Költségvetés, kiadások")
    
    # Lecke címek tárolása a kulcsokhoz
    lesson_titles_map = {
        "költségvetés": "Mi az a költségvetés, és miért kell vele foglalkozni?",
        "be_nem_vallott_kiadasok": "Hova tűnik el a pénzem? – Be nem vallott kiadások",
        "koltsegvetesi_modszerek": "Legismertebb költségvetési módszerek",
        "bevetel_kiadas_merleg": "Bevételek, kiadások, különbségek - avagy a mérleged",
        "mini_rutin_szokas": "Mini-rutin: Hogyan lehet a pénzügyeid követése szokás?",
        "penzugyi_kovetes_ritmusa": "Milyen gyakran nézd a pénzügyeidet?",
    }

    if st.session_state.current_lesson_key is not None:
        # Ha egy lecke aktív, csak azt jelenítjük meg
        active_lesson_key = st.session_state.current_lesson_key
        active_lesson_title = lesson_titles_map.get(active_lesson_key, "Ismeretlen lecke") 
        st.divider()
        st.markdown(f"##### {active_lesson_title}")
        display_lesson(active_lesson_key, active_lesson_title)
    else:
        # Ha nincs aktív lecke, minden lecke expander megjelenik
        display_lesson("költségvetés", lesson_titles_map["költségvetés"])
        display_lesson("be_nem_vallott_kiadasok", lesson_titles_map["be_nem_vallott_kiadasok"])
        display_lesson("koltsegvetesi_modszerek", lesson_titles_map["koltsegvetesi_modszerek"])

        st.markdown("#### Alap szokások, követés")
        display_lesson("bevetel_kiadas_merleg", lesson_titles_map["bevetel_kiadas_merleg"])
        display_lesson("mini_rutin_szokas", lesson_titles_map["mini_rutin_szokas"])
        display_lesson("penzugyi_kovetes_ritmusa", lesson_titles_map["penzugyi_kovetes_ritmusa"])
        

        st.markdown("#### Tudatos fogyasztás")
        with st.expander("Az impulzusvásárlás felismerése és kezelése"):
            st.write("Fejlesztés alatt...")
        with st.expander("Kell vagy csak akarom? – A döntés 5 másodperce"):
            st.write("Fejlesztés alatt...")
        with st.expander("A „pénz visszanéz” trükk"):
            st.write("Fejlesztés alatt...")

elif selected_category == "spórolás":
    st.subheader("💸 SPÓROLÁS ÉS MEGTAKARÍTÁS – „A kevesebb több lehet”")
    st.caption("🟡 Középhaladó szint")
    
    st.markdown("#### Spórolás alapjai")
    with st.expander("Hogyan kezdj el spórolni, ha alig marad valami?"):
        st.write("Fejlesztés alatt...")
    with st.expander("A megtakarítás 4 formája – és melyik való neked?"):
        st.write("Fejlesztés alatt...")
    with st.expander("Spórolási célok beállítása, vizualizálása"):
        st.write("Fejlesztés alatt...")
        
    st.markdown("#### Automatizálás és rendszerek")
    with st.expander("Automatikus megtakarítás – barát vagy csapda?"):
        st.write("Fejlesztés alatt...")
    with st.expander("A „fizess magadnak először” elv"):
        st.write("Fejlesztés alatt...")
    with st.expander("Kategóriaalapú spórolás – kis döntések, nagy hatás"):
        st.write("Fejlesztés alatt...")

    st.markdown("#### Haladó költésoptimalizálás")
    with st.expander("5 kiadástípus, amit újratárgyalhatsz (pl. előfizetések)"):
        st.write("Fejlesztés alatt...")
    with st.expander("Szezonális költések: mire figyelj előre?"):
        st.write("Fejlesztés alatt...")
    with st.expander("Napi mikrospórolások hatása éves szinten"):
        st.write("Fejlesztés alatt...")

elif selected_category == "gondolkodás":
    st.subheader("🧠 PÉNZÜGYI GONDOLKODÁS – „Fejben dől el”")
    st.caption("🟡🔵 Haladó szint")

    st.markdown("#### Viszonyod a pénzhez")
    with st.expander("A pénzügyi énkép: mit hittél el magadról?"):
        st.write("Fejlesztés alatt...")
    with st.expander("Gyerekkori minták – és amit újra kell tanulni"):
        st.write("Fejlesztés alatt...")
    with st.expander("A pénzhez fűződő érzelmek kezelése"):
        st.write("Fejlesztés alatt...")

    st.markdown("#### Pénzügyi döntéshozatal")
    with st.expander("A „sunk cost” csapda – mikor nem szabad folytatni"):
        st.write("Fejlesztés alatt...")
    with st.expander("Mikor hallgass a megérzéseidre, és mikor ne?"):
        st.write("Fejlesztés alatt...")
    with st.expander("A túloptimalizálás paradoxona"):
        st.write("Fejlesztés alatt...")

    st.markdown("#### Stressz és önbizalom")
    with st.expander("Hónap végi szorongás? – 3 gyakorlat a kezelésére"):
        st.write("Fejlesztés alatt...")
    with st.expander("Kis pénzügyi győzelmek és a belső hit"):
        st.write("Fejlesztés alatt...")
    with st.expander("Hogyan ne hasonlítsd magad másokhoz?"):
        st.write("Fejlesztés alatt...")

elif selected_category == "haladó":
    st.subheader("📈 HALADÓ PÉNZÜGYEK – „Láss előre”")
    st.caption("🔵 Profi szint")

    st.markdown("#### Céltervezés és hosszútáv")
    with st.expander("A SMART pénzügyi célok beállítása"):
        st.write("Fejlesztés alatt...")
    with st.expander("Mikor érdemes újraértékelni egy célt?"):
        st.write("Fejlesztés alatt...")
    with st.expander("Kockázat, rugalmasság, biztonsági ráhagyás"):
        st.write("Fejlesztés alatt...")

    st.markdown("#### Élethelyzetek pénzügyi szemmel")
    with st.expander("Összeköltözés, házasság – közös pénzügyek alapjai"):
        st.write("Fejlesztés alatt...")
    with st.expander("Munkahelyváltás, szabadúszás, jövedelmi váltás"):
        st.write("Fejlesztés alatt...")
    with st.expander("Vészhelyzet pénzügyi terv – mi történik, ha...?"):
        st.write("Fejlesztés alatt...")

    st.markdown("#### Jövedelemtípusok")
    with st.expander("Aktív vs. passzív jövedelmek – mi a különbség?"):
        st.write("Fejlesztés alatt...")
    with st.expander("Kiegészítő jövedelemforrás indítása"):
        st.write("Fejlesztés alatt...")
    with st.expander("Pénztermelő szokások, nem csak spórolás"):
        st.write("Fejlesztés alatt...")

elif selected_category == "gyakorlati":
    st.subheader("🧪 GYAKORLATI BLOKKOK – „Csináld meg most”")
    st.caption("🟢🟡🔵 Minden szint")

    st.markdown("#### 7 napos kihívások")
    with st.expander("7 napos „no spend” kihívás"):
        st.write("Fejlesztés alatt...")
    with st.expander("7 napos spórolási cél kitűzés és követés"):
        st.write("Fejlesztés alatt...")
    with st.expander("7 nap, 7 pénzügyi szokás"):
        st.write("Fejlesztés alatt...")

    st.markdown("#### Mini workshopok (interaktív)")
    with st.expander("Költségkategória-rendező miniworkshop"):
        st.write("Fejlesztés alatt...")
    with st.expander("Tervezz egy havi költségvetést nulláról"):
        st.write("Fejlesztés alatt...")
    with st.expander("Vizualizálj egy célhoz vezető megtakarítási útvonalat"):
        st.write("Fejlesztés alatt...")

    st.markdown("#### Tudásellenőrzők")
    with st.expander("Teszt: Milyen típusú pénzügyi döntéshozó vagy?"):
        st.write("Fejlesztés alatt...")
    with st.expander("Kvíz: felismered a megtakarítási csapdákat?"):
        st.write("Fejlesztés alatt...")
    with st.expander("Saját költségvetés-analízis sablonnal"):
        st.write("Fejlesztés alatt...")

# Lábléc
st.divider()
#st.caption("Tudástár v1.0 · Minden jog fenntartva · © 2024")
