import streamlit as st

if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("Kérjük, először jelentkezzen be!")
    st.stop()
    
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
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Tanulási streak", "🔥 3 nap")
    with col2:
        # A teljesített leckék számának dinamikus frissítése
        if 'completed_lessons' not in st.session_state:
            st.session_state.completed_lessons = 0
        st.metric("Teljesített leckék", f"{st.session_state.completed_lessons}/24")
    with col3:
        st.metric("Gyűjtött kitűzők", "2")

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
             {"name": "Pénzügyu gondolkodás", "value": "gondolkodás"}, 
             {"name": "Haladó", "value": "haladó"}, 
             {"name": "Gyakorlat", "value": "gyakorlati"}, 
             ],
    format_func=lambda x: x["name"],
    horizontal=True
)["value"]

st.divider()

# Lecke tartalom definíciója
lesson_contents = {
    "költségvetés": [
        "**„Hónap végére mindig elfogy a pénz?” – A költségvetés nem korlát, hanem kulcs a szabadsághoz**\n\n„Hónap végére mindig elfogy a pénz, pedig nem is éltél nagy lábon?” Ha magadra ismertél ebben a mondatban, nem vagy egyedül. Sok ember érez frusztrációt, amikor azt tapasztalja, hogy a fizetés „egyszerűen eltűnik”, pedig nem költekezett különösebben felelőtlenül. Ez azonban nem lustaság, nem pénzügyi analfabetizmus, és nem is balszerencse – gyakran csak annyi történik, hogy nincs egy tudatosan elkészített, átlátható költségvetés.",
        "**Mi is az a költségvetés?**\n\nA költségvetés egyszerűen egy terv arról, hogyan osztod be a bevételeidet. Olyan, mint egy térkép: megmutatja, hová megy a pénzed, és segít eldönteni, merre szeretnéd irányítani. Nem a pénz mennyisége határozza meg, hogy szükséged van-e költségvetésre, hanem az, hogy szeretnéd-e tudni, mire megy el, és mit lehetne vele jobban csinálni.",
        "**Mi történik, ha nincs?**\n\nKépzeld el, hogy egy szitán próbálsz vizet tartani. Lehet bármilyen nagy vödröd – ha lyukas, a víz kifolyik. A költségvetés segít „betömni a lyukakat”, vagyis észrevenni a rejtett kiadásokat, szokássá vált apró költéseket, amik végül komoly összegeket emésztenek fel. Legyen szó napi egy kávéról, havonta elfelejtett előfizetésekről vagy impulzusvásárlásokról, ezek akkor is ott vannak, ha nem figyelsz rájuk.",
        "**Mire jó a költségvetés?**\n\nA költségvetés elsődleges célja nem az, hogy korlátozzon, hanem hogy tudatosabb döntésekhez segítsen hozzá. Ez az az eszköz, amivel:\n* Előre láthatod, milyen fix és változó kiadásaid vannak.\n* Megtervezheted, mennyit tudsz félretenni.\n* Prioritásokat állíthatsz fel: mi fontos számodra, mire szeretnél valóban költeni?\n* Elkerülheted a túlköltést, hiszen láthatóvá válik, hogy mikor léped át a kereteidet.",
        "**Hogyan kezdj neki?**\n\n* Írd össze a havi bevételeidet: fizetés, támogatások, mellékes jövedelmek.\n* Írd össze az összes kiadásodat: lakhatás, élelmiszer, közlekedés, szórakozás, adósság, előfizetések.\n* Kategorizálj: válaszd szét a fix (pl. lakbér) és változó (pl. étkezés, szórakozás) kiadásokat.\n* Hasonlítsd össze a bevételeidet a kiadásokkal: ha több megy ki, mint amennyi bejön, változtatnod kell.\n* Készíts egy reális tervet a következő hónapra – hagyj benne mozgásteret is, ne legyen túl szigorú.\n\nNem kell tökéletesnek lennie az első alkalommal. A költségvetés nem kőbe vésett szabályrendszer, hanem egy rugalmas eszköz, amit idővel egyre jobban fogsz használni.",
        "**Miért éri meg?**\n\nA költségvetés nem elvesz a szabadságodból – épp ellenkezőleg: visszaadja. Ha tudod, mire megy el a pénzed, képes leszel tudatosan irányítani. Ez pedig nemcsak kevesebb stresszt, hanem nagyobb biztonságot, sőt akár megtakarításokat is jelenthet – anélkül, hogy le kellene mondanod minden örömről.",
        "**Összegzés**\n\nA költségvetés nem csak a pénzügyekről szól, hanem a kontrollról, a nyugalomról és a lehetőségről, hogy te döntsd el, mire fordítod az erőforrásaidat. Nem bonyolult elkezdeni – csak egy kis figyelem, papír, toll (vagy egy alkalmazás) kell hozzá. A kérdés nem az, hogy „meg tudod-e csinálni”, hanem az, hogy mikor kezded el."
    ],
    "be_nem_vallott_kiadasok": [
        "**„Nem is költöttem semmire!” – A be nem vallott kiadások titkos élete**\n\n„Nem is költöttem semmire!” – mondod, miközben a bankszámlád szerint épp most ment el harmincezer forint az „egy kis ez, egy kis az” nevű, láthatatlan kategóriára. A be nem vallott kiadások pont ilyenek: alattomosak, hétköznapiak és meglepően sokba kerülnek. Ideje felfedni őket, mielőtt újra eltűnik a fizetésed nyomtalanul.",
        "**Mik azok a „be nem vallott kiadások”?**\n\nEz nem bűntudatkeltő kifejezés – inkább egy őszinte elnevezés azoknak a költéseknek, amiket nem szívesen ismerünk el magunknak sem. Nem tartjuk őket „igazi” költésnek, mert kicsik, gyorsak, rutinszerűek. Egy reggeli kávé, egy random leárazott póló, egy foodpanda rendelés, vagy az automatikusan levont előfizetések. Nem mindig luxus dolgok – gyakran csak kényelmi döntések, amiket nem tervezünk be.\nA gond nem az, hogy ezek önmagukban hibák lennének – hanem hogy nem számolunk velük tudatosan.",
        "**Miért veszélyesek?**\n\nAz apró, rendszeres költések könnyen láthatatlanná válnak, különösen, ha nem vezetjük őket. De ha összeadod, hamar kijön a havi 20-30-40 ezer forintos „szivárgás”, ami aztán ellehetetleníti a spórolást, a megtakarítást – sőt, gyakran még a hónap végét is. Ezek a tételek nem egyszerre csapnak le, ezért nem tűnnek veszélyesnek. Csak amikor összeadódnak.\nA legnagyobb trükkjük az, hogy nem érezzük őket költésnek, csak „könnyű döntésnek”.",
        "**Hol lapulnak ezek a kiadások?**\n\nÍme néhány gyakori „be nem vallott” kategória:\n\n* Napi apróságok: pékség, kávé, boltban „csak egy valami”.\n* Előfizetések: streaming, edzésapp, tárhely – amiket talán nem is használsz.\n* Kényelmi vásárlás: ételrendelés, taxi, kiszállítási díj.\n* Impulzusvásárlás: „csak most akciós”, „megérdemlem”, „jó lesz még valamire”.\n\nEzek mindegyike önmagában ártalmatlan – de együtt teljesen eltorzíthatják a havi költségvetést.",
        "**Hogyan leplezd le őket?**\n\n**Nézz szembe a bankszámláddal.**\n\nNyisd meg az elmúlt 1-2 hónap tranzakcióit, és színezd ki, mi volt valójában nem tervezett, apróság, vagy impulzus. Ez már önmagában döbbenetes felismeréseket hozhat.\n**Vezess kiadási naplót – pár napig is elég.**\n\nJegyezd fel minden kiadásod, még a legapróbbakat is. Nem kell örökre csinálni, de már néhány nap után látni fogod a mintázatokat.\n**Kategorizálj és nevesíts!**\n\nHozz létre egy „szokásos apróságok” nevű kategóriát, és állíts be rá limitet. Ne csak utólag számold meg – előre határozd meg, mennyit érnek meg neked ezek a kényelmi döntések havonta.\n**Tedd tudatossá!**\n\nKérdezd meg magadtól vásárlás előtt: „Ez most tényleg kell, vagy csak megszokásból veszem meg?” Sokszor már ez a kérdés is elég.",
        "**A tudatosság nem spórolás – hanem szabadság**\n\nA cél nem az, hogy mindent megvonj magadtól. A cél az, hogy te dönts a pénzedről, ne a rutinjaid vagy a figyelmetlenséged tegye meg helyetted. Ha felismered a be nem vallott kiadásaidat, újra uralhatod a pénzügyeidet – és lehet, hogy épp ezek az apróságok nyitják meg az utat a megtakarítások, a nyugodtabb hónapvége vagy egy régóta vágyott cél előtt.",
        "**Zárógondolat**\n\nA pénz nem mindig akkor tűnik el, amikor sokat költünk – néha akkor folyik ki, amikor nem figyelünk oda. Most, hogy tudod, hol keresd, talán te is rájössz: nem a pénzed tűnik el. Csak nem volt szem előtt."
    ]
}

# Aktuális lecke állapota
if 'current_lesson_key' not in st.session_state:
    st.session_state.current_lesson_key = None # Jelenleg olvasott lecke kulcsa
if 'lesson_page' not in st.session_state:
    st.session_state.lesson_page = 0
if 'lesson_completion_status' not in st.session_state:
    st.session_state.lesson_completion_status = {
        "költségvetés": False,
        "be_nem_vallott_kiadasok": False
        # Ide jönnek majd a többi lecke kulcsai és állapotai
    }


# Segéd függvény a leckék kezeléséhez
def display_lesson(lesson_key, lesson_title):
    if st.session_state.current_lesson_key == lesson_key:
        current_lesson_content = lesson_contents[lesson_key]
        total_pages = len(current_lesson_content)
        current_page_display = st.session_state.lesson_page + 1

        # Progress bar
        st.write(f"Oldal: {current_page_display}/{total_pages}")
        col_head1, col_head2 = st.columns([5, 2])
        col_head1.progress(current_page_display / total_pages)
        if col_head2.button("Lecke elhagyása"):
            st.session_state.current_lesson_key = None # Kilépés az olvasó módból
            st.rerun()
        
        st.markdown(current_lesson_content[st.session_state.lesson_page])

        col_nav1, col_nav2 = st.columns(2)
        with col_nav1:
            if st.session_state.lesson_page > 0:
                if st.button("Előző", key=f"prev_page_{lesson_key}"):
                    st.session_state.lesson_page -= 1
                    st.rerun()
        with col_nav2:
            if st.session_state.lesson_page < len(current_lesson_content) - 1:
                if st.button("Következő", key=f"next_page_{lesson_key}"):
                    st.session_state.lesson_page += 1
                    st.rerun()
            else:
                if st.button("Lecke befejezése", key=f"complete_{lesson_key}"):
                    st.session_state.lesson_completion_status[lesson_key] = True
                    st.session_state.current_lesson_key = None # Kilépés az olvasó módból
                    st.session_state.completed_lessons += 1
                    st.success(f"Gratulálunk, befejezted a leckét: {lesson_title}! 🎉")
                    st.rerun()
    else:
        with st.expander(lesson_title):
            if not st.session_state.lesson_completion_status[lesson_key]:
                if st.button("Lecke elkezdése", key=f"start_{lesson_key}"):
                    st.session_state.current_lesson_key = lesson_key
                    st.session_state.lesson_page = 0
                    st.rerun()
            if st.session_state.lesson_completion_status[lesson_key]:
                st.success("✔️ Gratulálok, elvégezted a leckét!")
                if st.button("Lecke újrakezdése", key=f"restart_{lesson_key}"):
                    st.session_state.current_lesson_key = lesson_key
                    st.session_state.lesson_page = 0
                    st.rerun()

# Témakörönkénti leckék megjelenítése
if selected_category == "alapok":
    st.subheader("🧱 ALAPOK – „Tudd, hol állsz”")
    st.caption("🟢 Kezdő szint")
    
    st.markdown("#### Költségvetés, kiadások")
    
    # Lecke címek tárolása a kulcsokhoz
    lesson_titles_map = {
        "költségvetés": "Mi az a költségvetés, és miért kell vele foglalkozni?",
        "be_nem_vallott_kiadasok": "Hova tűnik el a pénzem? – Be nem vallott kiadások"
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

        with st.expander("A 3 legnépszerűbb költségvetési módszer"):
            st.write("Fejlesztés alatt...")
        with st.expander("Bevételek, kiadások, különbségek – avagy a mérleged"):
            st.write("Fejlesztés alatt...")

        st.markdown("#### Alap szokások, követés")
        with st.expander("A költésnapló hatása a pénzügyi tudatosságra"):
            st.write("Fejlesztés alatt...")
        with st.expander("Hogyan legyen belőle szokás? – A mini-rutin"):
            st.write("Fejlesztés alatt...")
        with st.expander("Milyen gyakran kövesd a pénzügyeid?"):
            st.write("Fejlesztés alatt...")

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
