# ADR 0002: UI/UX Design System Kiválasztása – Stripe Enterprise (1A)

## Státusz
Elfogadva (Accepted)

## Dátum
2026-11-12

## Döntéshozók
Felhasználó (Terméktulajdonos) & Lead Orchestrator

## Kontextus
A PeerPlay korábbi felületei az AI kódgenerátorok tipikus hibáit (sötét cyberpunk fekete háttér, lila/cián gradiens, emoji-túltengés, doboz-a-dobozban zűrzavar) hordozták magukon.
A human-crafted vizsgálat ([knowledge/rules/human_centered_design_standards.md](file:///E:/Data/other_projects/PeerPlay/knowledge/rules/human_centered_design_standards.md)) után 3 iparági benchmark stílusvariációt teszteltünk a prototípusban:
1. **1A: Stripe Enterprise** (Cobalt & Slate, Plus Jakarta Sans)
2. **1B: Vercel Monochrome** (Pitch Black, Geist)
3. **1C: Mercury Executive** (Forest Emerald, Space Grotesk)

A terméktulajdonos az **1A (Stripe Enterprise)** irányvonalat hagyta jóvá a PeerPlay hivatalos design alapjaként.

## Döntés
A PeerPlay felhasználói felületeinek hivatalos tervezési rendszere a **Stripe Enterprise (1A)** standardra épül:
1. **Színvilág & Megjelenés:**
   - Alapvászon (Canvas): Hűvös palafehér (`#F8FAFC`).
   - Kártyák és felületek: Tiszta papírfehér (`#FFFFFF`), finom kőszürke határolóvonalakkal (`#E2E8F0`) és visszafogott mikró-árnyékokkal (`0 1px 3px rgba(0,0,0,0.05)`).
   - Elsődleges akciógomb (CTA): Stripe kobaltkék (`#2563EB` hover: `#1D4ED8`).
   - Jelzőszínek: Smaragdzöld (`#059669`) készpénzhez és átvételhez, meleg borostyán (`#D97706`) piaci eseményekhez, rubinvörös (`#DC2626`) elutasításhoz és időzítőhöz.
2. **Tipográfia:**
   - Címek, címkék és szövegtörzs: **Plus Jakarta Sans** (modern, feszes, geometriai neo-groteszk, `-0.03em` tracking címeknél).
   - Pénzügyi összegek, visszaszámláló és darabszámok: **JetBrains Mono** tabuláris számokkal (`tabular-nums`).
3. **Zéró Emojik & Ikonográfia:**
   - Szigorúan tilos dekorációs emojikat használni.
   - Vékony (1.25px - 1.5px) funkcionális monokróm SVG ikonok vagy mérnöki szimbólumok használandók.
4. **Alkalmazási Terület:**
   - Facilitátori Konzol (laptop / tablet / kivetítő).
   - Csapat Munkaállomás (asztali tablet / laptop).
   - Résztvevői Mobil felület (okostelefonok).
   - HR Elemzői Dashboard & Debrief riportok (kivéve a nyomtatási PDF nézeteket, amelyek ugyanezt a világos sémát követik).

## Következmények
- A design tokens és a CSS komponensek a [knowledge/rules/brand_and_design_guidelines.md](file:///E:/Data/other_projects/PeerPlay/knowledge/rules/brand_and_design_guidelines.md) dokumentumban kerülnek kanonizálásra.
- A következő fázis: A teljes képernyőleltár (Screen Inventory), az állapotok (States) és a felhasználói útvonalak részletes kidolgozása.
