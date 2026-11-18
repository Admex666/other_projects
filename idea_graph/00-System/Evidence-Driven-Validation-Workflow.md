---
type: system_workflow
title: Evidence-Driven Venture Validation Workflow (VIS 2.0)
version: 2.0
date: 2026-11-18
status: active_architecture
principles:
  - "Maximize Decision Confidence per Unit of Time and Money Invested"
  - "No hypothesis is validated purely by secondary research"
---

# Evidence-Driven Venture Validation Workflow (VIS 2.0)
## Az Idea Graph adaptív, bizonyítékvezérelt működési modellje

> **A rendszer alapfilozófiája:**  
> **„Maximize Decision Confidence per Unit of Time and Money Invested.”**  
> *(A döntési bizonyosság maximalizálása a befektetett idő és pénz egységére vetítve.)*  
> 
> Az Idea Graph nem egyszerűen azt vizsgálja, hogy egy üzleti ötlet elméletben jónak tűnik-e, hanem azt határozza meg, hogy **hogyan tudjuk a lehető legkisebb ráfordítással (kódolás, hirdetések és felesleges munkaórák nélkül) kideríteni, hogy valóban működőképes és nyereséges vállalkozás építhető-e belőle.**

---

## 1. A Megújult Rendszerarchitektúra és Szintek

A rendszer 3 bizonyossági szintet (Evidence Hierarchy) és 3 új, egymással szorosan összekapcsolódó komponenst vezet be:

```mermaid
graph TD
    subgraph EvHierarchy["3 SZINTŰ BIZONYOSSÁGI RENDSZER (Evidence Hierarchy)"]
        direction TB
        L1["Level 1: Secondary Evidence (Külső kutatás)<br/>• Piaci méret, iparági trendek, versenytársak<br/>• Következtetés: Az ötlet elméletben érdekes"]
        L2["Level 2: Primary Evidence (Saját validáció)<br/>• Ügyfélinterjúk, reach-out konverzió, LoI, idő/figyelem ráfordítás<br/>• Következtetés: Van valós ügyféligény és probléma"]
        L3["Level 3: Economic Evidence (Üzleti bizonyíték)<br/>• Kifizetett pilot, előrendelés, kaució, mért CAC/LTV<br/>• Következtetés: A vállalkozás nyereségesen működtethető"]
        L1 --> L2 --> L3
    end

    subgraph NewEngine["3 ÚJ RENDSZERKOMPONENS"]
        direction TB
        C1["1. Hypothesis & Uncertainty Map<br/>• Kritikus feltételezések összegyűjtése<br/>• Rangsorolás kockázat & bizonytalanság szerint<br/>• 'What must be true?'"]
        C2["2. Adaptive Validation Plan<br/>• Kontextusfüggő, olcsó tesztválasztás<br/>• Indoklás & Költség / Idő keret<br/>• Szigorú Siker / Kudarc küszöbök"]
        C3["3. Evidence & Decision Tracker<br/>• Teszteredmények visszacsatolása a gráfba<br/>• Hipotézis státusz frissítése (L1 -> L2/L3)<br/>• 4-állapotú döntési kapu: PROCEED / TEST / PIVOT / STOP"]
        C1 ==> C2 ==> C3
        C3 -.->|Visszacsatolási hurok / Gráf frissítés| C1
    end
```

---

## 2. A Teljes End-to-End Munkafolyamat (Workflow Flowchart)

A folyamat két fő ciklusra oszlik: az **Elméleti Elemzésre (Desk Research)** és a közvetlenül ráépülő **Adaptív Validációs Ciklusra (Actionable Validation Loop)**.

```mermaid
flowchart TD
    %% Start
    Start(["💡 Új Üzleti Ötlet"]) --> P1["01. Idea Framing<br/>(Koncepció & Kezdeti Kérdésgráf)"]
    
    %% Szekunder Fázis
    P1 --> P2["Párhuzamos Szekunder Kutatások (L1)<br/>• Market, Customer, Competition<br/>• Business Model, Financial, Execution"]
    P2 --> P3["Keresztelemzés & Adversarial Review<br/>(Ellentmondások & Bukási Pontok)"]
    
    %% Átmenet a Validációs Motorba
    P3 --> C1["1. Hypothesis & Uncertainty Map<br/>Melyik feltételezés bukása öli meg az ötletet?"]
    
    %% Kérdés 5 pontja
    C1 --> C2{"2. Adaptive Validation Plan<br/>Mi a legolcsóbb, leggyorsabb teszt?"}
    
    %% Kontextusfüggő tesztek
    C2 -->|B2B Enterprise / Szolgáltatás| T_B2B["Célzott Cold Reach-out &<br/>Problémafeltáró Interjúk"]
    C2 -->|B2C / E-commerce| T_B2C["Landing Page Smoke Test &<br/>Előrendelés / Várólista"]
    C2 -->|Technológiai / Komplex| T_TECH["Concierge MVP / Manuális szerviz<br/>(Kódolás nélkül)"]
    
    %% Végrehajtás
    T_B2B --> RUN["Kísérlet végrehajtása<br/>(Max 14-30 nap, Min. Költség)"]
    T_B2C --> RUN
    T_TECH --> RUN
    
    %% Tracker & Döntés
    RUN --> C3["3. Evidence & Decision Tracker<br/>Eredmények mérése a kritériumokhoz képest"]
    
    C3 --> GATE{"Döntési Kapu"}
    
    GATE -->|PROCEED| DEC_PROC(["🚀 PROCEED<br/>Elegendő bizonyíték a következő<br/>nagyobb lépéshez (pl. MVP építés)"])
    GATE -->|TEST FURTHER| C1
    GATE -->|PIVOT| DEC_PIV["🔄 PIVOT<br/>Modell/célcsoport módosítása<br/>az Idea Graphban"]
    DEC_PIV --> C1
    GATE -->|STOP| DEC_STOP(["🛑 STOP<br/>Kritikus alaptétel megdőlt;<br/>Projekt lezárása"])
```

---

## 3. A Kontextusfüggő Tesztválasztási Mátrix

Az Idea Graph nem sablonos ellenőrzőlistát ad, hanem a felismert üzleti modell és a bizonytalanság jellege alapján választja ki a legolcsóbb tesztet:

```mermaid
graph LR
    subgraph Bizonytalanságok["Mit nem tudunk?"]
        U1["Létezik-e a valós probléma?"]
        U2["Elég fontos-e / Sürgető-e?"]
        U3["Fizetnének-e érte (WTP)?"]
        U4["Milyen konkrét csomagot akarnak?"]
        U5["Megismételhető-e az eladás?"]
    end

    subgraph Modszerek["Legolcsóbb Validációs Eszköz"]
        M1["10-15 Célzott Customer Discovery Interjú"]
        M2["Jelenlegi alternatívák & Költségek auditja"]
        M3["Előértékesítés, Kaució, Szándéknyilatkozat (LoI)"]
        M4["Offer Testing / Concierge egyoldalas ajánlat"]
        M5["Hideg megkeresési tölcsér teszt (Outreach Funnel)"]
    end

    U1 ==> M1
    U2 ==> M2
    U3 ==> M3
    U4 ==> M4
    U5 ==> M5
```

### Konkrét Teszt Tervezési Sablon (Minden ajánláshoz kötelező)
Minden generált kísérletnek az alábbi 9 pontot kell kötelezően tartalmaznia:
1. **Hypothesis:** *Mit tesztelünk pontosan?*
2. **Why this test:** *Miért ez a legolcsóbb és legmegbízhatóbb módszer az adott kontextusban?*
3. **Uncertainty reduced:** *Milyen kockázatot zár ki a teszt?*
4. **Execution:** *Lépésről lépésre mit kell csinálni a következő 14 napban?*
5. **Cost & Time:** *Pontosan hány forintba és munkaórába kerül? (Tilos kódolást és drága hirdetést előírni)*
6. **Success criteria (Zöld lámpa):** *Mi az a számszerűsíthető eredmény, ami bizonyítja a feltevést?*
7. **Failure criteria (Piros lámpa):** *Mi az az eredmény, ami cáfolja (hamisítja) a feltevést?*
8. **Limitations:** *Mit NEM tudunk meg ebből a tesztből?*
9. **Next decision:** *Hogyan lépünk tovább az eredmény fényében?*

---

## 4. Visszacsatolási Hurok a Kérdésgráfba (Feedback Loop)

A rendszer legfontosabb technikai újítása, hogy a teszteredmények nem elszigetelt jegyzetek maradnak, hanem **visszacsatolódnak a kérdésgráf csomópontjaira**:

```mermaid
sequenceDiagram
    autonumber
    actor U as Alapító / Felhasználó
    participant IG as Idea Graph / Kérdésháló
    participant AM as 02-Assumptions.md
    participant VP as Adaptive Validation Plan
    participant EXP as Valós Piac (Ügyfelek)
    participant TR as Evidence & Decision Tracker

    IG->>AM: 1. Kritikus feltételezések azonosítása
    AM->>VP: 2. 'What must be true?' feltételek átadása
    VP->>U: 3. Személyre szabott, olcsó tesztterv (outreach / interjú)
    U->>EXP: 4. Kísérlet végrehajtása (kódolás nélkül)
    EXP-->>U: 5. Valós viselkedési adatok (konverzió, fizetés)
    U->>TR: 6. Tények rögzítése
    TR->>AM: 7. Bizonyossági szint frissítése (L1 -> L2 vagy L3)
    TR->>IG: 8. Csomópont státuszának átírása (Zöld / Piros)
    TR->>U: 9. Kötelező döntés: PROCEED / TEST FURTHER / PIVOT / STOP
```

---

## 5. Az Arany Szabály (The Golden Rule)

> [!CAUTION]
> ### Rendszerszintű Védelmi Szabály
> **Az AI soha nem nyilváníthat egy hipotézist validálttá pusztán azért, mert több másodlagos kutatási forrás vagy elemzés alátámasztja!**
> 
> * Külső kutatási források (L1) = **Lehetőség (Opportunity Hypothesis)**
> * Saját ügyfél-viselkedés (L2) = **Igény-bizonyíték (Demand Evidence)**
> * Saját bevétel és megtartás (L3) = **Üzleti bizonyíték (Economic Viability)**
> 
> A rendszer nem engedi meg a `PROCEED` döntést nagytőkéjű fázisba (pl. teljes szoftverfejlesztés), amíg a kritikus túlélési feltételekre nincs legalább L2 vagy L3 szintű saját bizonyíték.
