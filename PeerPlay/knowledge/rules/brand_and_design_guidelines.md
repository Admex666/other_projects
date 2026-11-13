# 🎨 PeerPlay Design System & Brand Guidelines (Stripe Enterprise Standard)

> **Státusz:** Kanonikus Szabvány (Jóváhagyva: ADR 0002)  
> **Dátum:** 2026-11-12  
> **Benchmark Alap:** Stripe Dashboard, Apple Enterprise B2B, Pitch  
> **Kapcsolódó ADR:** [0002_design_system_stripe_enterprise.md](file:///E:/Data/other_projects/PeerPlay/knowledge/decisions/0002_design_system_stripe_enterprise.md)  
> **Alapelv Referencia:** [human_centered_design_standards.md](file:///E:/Data/other_projects/PeerPlay/knowledge/rules/human_centered_design_standards.md)

---

## 1. Vizuális Identitás & Hangvétel

A PeerPlay vizuális nyelve a **modern B2B Fintech & Enterprise intelligencia platformok** megbízhatóságát, pontosságát és professzionalizmusát közvetíti.
- **Tiszta és Kontrasztos:** Világos alapú (Daylight-First), ami mind a laptopokon, mind a tréningtermi kivetítőkön és mobilokon maximális olvashatóságot biztosít.
- **Funkcionális & Adatvezérelt:** A díszítőelemeket minimálisra szorítjuk; az esztétikát a tökéletes térközök (4px grid), a feszes tipográfia és a finom mikró-interakciók adják.
- **Zéró Emojik:** Nincsenek gyerekes matricák vagy emojik; a felületen kizárólag funkcionális 1.25px SVG piktogramok vagy precíz műszaki jelölések szerepelnek.

---

## 2. Design Tokens & Színrendszer

### 2.1. Felületek és Hátterek
| Token Név | Hex Kód | Tailwind Megfelelő | Szerep |
| :--- | :--- | :--- | :--- |
| `--bg-canvas` | `#F8FAFC` | `bg-slate-50` | Teljes alkalmazás háttér / munkaterület |
| `--bg-surface` | `#FFFFFF` | `bg-white` | Kártyák, panelek, modális ablakok |
| `--bg-subtle` | `#F1F5F9` | `bg-slate-100` | Inaktív beviteli mezők, táblázat fejlécek, chip hátterek |
| `--border-color` | `#E2E8F0` | `border-slate-200` | Alapértelmezett kártya- és elválasztóvonalak (1px) |
| `--border-strong`| `#CBD5E1` | `border-slate-300` | Kiemelt határolók, fókuszált mezők kerete |

### 2.2. Tipográfiai Színek
| Token Név | Hex Kód | Szerep |
| :--- | :--- | :--- |
| `--text-main` | `#0F172A` | Főcímek, aktív értékek, legfontosabb adatok |
| `--text-muted`| `#64748B` | Leíró szövegek, magyarázatok, táblázat címkék |
| `--text-soft` | `#94A3B8` | Időbélyegek, másodlagos metaadatok, segédcímkék |

### 2.3. Akció- és Jelzőszínek (Semantic Tokens)
| Token Név | Hex Kód | Szerep |
| :--- | :--- | :--- |
| `--primary` | `#2563EB` | Elsődleges CTA gombok, aktív fülek, fókuszpontok |
| `--primary-hover`| `#1D4ED8` | Gomb hover állapot |
| `--accent-green` | `#059669` | Jóváhagyás, bevételek, nyereség, banki felvásárlás |
| `--accent-green-bg` | `#ECFDF5` | Zöld státuszcímke háttér |
| `--accent-amber` | `#D97706` | Piaci események (Breaking News), figyelmeztetések |
| `--accent-amber-bg` | `#FFFBEB` | Sárga eseménykártya háttér |
| `--accent-red` | `#DC2626` | Elutasítás, hiány, visszaszámláló utolsó percei |
| `--accent-red-bg` | `#FEF2F2` | Vész- vagy elutasítási címke háttér |

---

## 3. Tipográfiai Rendszer

A rendszer a modern digitális termékek aranystandardjának számító **Plus Jakarta Sans** és **JetBrains Mono** betűpárosításra épül:

1. **Címek & Szövegtörzs:** `Plus Jakarta Sans`, sans-serif
   - `H1 (Főcím):` 24px - 28px, `font-extrabold` (800), `letter-spacing: -0.03em`.
   - `H2 (Panel Cím):` 16px - 18px, `font-bold` (700), `letter-spacing: -0.02em`.
   - `Body (Kenyérszöveg):` 13px - 14px, `font-normal` (400) / `font-medium` (500), `line-height: 1.5`.
   - `Label / Badge:` 10px - 11px, `font-bold` (700), `text-transform: uppercase`, `letter-spacing: 0.05em`.

2. **Számadatok, Időzítő & Pénzügy:** `JetBrains Mono`, monospace
   - Szigorúan kötelező tabuláris számokkal (`tabular-nums`), hogy a számlálók és egyenlegek ne ugráljanak értékváltozáskor.
   - Időzítő: 36px - 44px, `font-bold`.
   - Egyenlegek: 20px - 24px, `font-bold`.

---

## 4. Komponens Szabályok & Minták

1. **Kártyák és Konténerek (`.theme-card`):**
   - Fehér háttér (`#FFFFFF`), `border: 1px solid #E2E8F0`, lekerekítés: `12px` (`rounded-xl`).
   - Finom, természetes mikró-árnyék: `box-shadow: 0 1px 3px rgba(0,0,0,0.05), 0 1px 2px -1px rgba(0,0,0,0.05)`.
   - Tilos a doboz-a-dobozban halmozás: egy kártyán belül a belső elválasztást finom vonalak (`border-t border-slate-100`) és térközök adják.

2. **Gombok:**
   - **Elsődleges (Primary):** Kék (`#2563EB`), fehér szöveg, `rounded-lg`, finom hover sötétedéssel.
   - **Másodlagos (Secondary):** Törtfehér (`#F1F5F9`) vagy fehér vékony kerettel (`border border-slate-200`), sötét szöveg.
   - **Műveleti Stepperek (`+` / `-`):** 36px × 36px minimális érintési célpont a facilitátori gyors darabszám-beállításhoz.

3. **Adattáblázatok:**
   - Fejléc: 10px csupa nagybetűs monospaced felirat, szürke tónus (`#64748B`), vékony alsó vonal.
   - Sorok: 12px szövegek, elválasztva `1px solid #F1F5F9` vonalakkal.
