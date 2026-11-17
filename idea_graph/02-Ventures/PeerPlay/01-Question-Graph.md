---
type: venture_question_graph
venture: PeerPlay
status: enriched_with_market_customer_evidence
date: 2026-11-17
opportunity_doc: "[[02-Ventures/PeerPlay/00-Opportunity]]"
assumptions_doc: "[[02-Ventures/PeerPlay/02-Assumptions]]"
market_research_doc: "[[02-Ventures/PeerPlay/Research/Market]]"
customer_research_doc: "[[02-Ventures/PeerPlay/Research/Customer]]"
---

# PeerPlay — Kiterjesztett Rendszergráf és Kérdésháló (Q-001 – Q-706)

Ez a kérdésgráf a piaci és vevői Deep Research bizonyítékok integrálásával kibővített, hálózatos modell. Nem pusztán fentről lefelé ágazik el, hanem tartalmazza a **dimenziók közötti keresztkapcsolatokat (cross-domain dependencies)**, a **visszacsatolási hurkokat (feedback loops)** és az **invalidációs kapukat (decision gates)**.

---

## 1. Részletes Rendszer- és Kérdésháló (Mermaid)

```mermaid
graph TD
    %% Központi Kérdés
    Q000["Q-000: Érdemes a PeerPlay-ből önálló, skálázható venture-t építeni?"]

    %% 6 Fő Dimenzió
    Q001["Q-001: Customer:<br/>Létezik sürgető, monetizálható silóprobléma?"]
    Q002["Q-002: Market:<br/>Elég nagy és elérhető a célpiac (HU / CEE-6)?"]
    Q003["Q-003: Solution & Validity:<br/>Hiteles és akcióképes értéket nyújt az ONA riport?"]
    Q004["Q-004: Competition & Moat:<br/>Védhető a pozíció a trénerekkel és az ONA-val szemben?"]
    Q005["Q-005: Financial & Unit Economics:<br/>Képes a modell magas árrést és LTV-t termelni?"]
    Q006["Q-006: Execution & Operations:<br/>Képes a szolgáltatás az alapítón túl skálázódni?"]

    %% Központi fa kapcsolatok
    Q000 --> Q001
    Q000 --> Q002
    Q000 --> Q003
    Q000 --> Q004
    Q000 --> Q005
    Q000 --> Q006

    %% Specifikus Kérdéscsomópontok
    Q103["Q-103: Trigger Events:<br/>Mi váltja ki a vásárlást (M&A, AI, átszervezés)?"]
    Q105["Q-105: Vétópontok:<br/>Üzemi Tanács (Mt. 264. §) és DPO blokkolja?"]
    Q202["Q-202: Piacméret korlát:<br/>HU SOM max 75M Ft (150 alkalom) - elég ez?"]
    Q204["Q-204: CEE Régiós ugrás:<br/>CZ/AT magasabb képzési hajlandóság vs. PL/RO"]
    Q405["Q-405: Partner vs. Competitor:<br/>Külső OD cégek mint értékesítési csatorna"]
    Q501["Q-501: Ismétlődő bevétel:<br/>1 alkalmas rendezvény vs. Negyedéves mérés / LTV"]
    Q602["Q-602: Facilitátor szűk keresztmetszet:<br/>Playbook és külső trénerek minőségbiztosítása"]
    Q701["Q-701: Ökológiai validitás:<br/>Tükrözi-e a 90 perces játék a valódi munkát?"]

    %% Alágak hozzárendelése
    Q001 --> Q103
    Q001 --> Q105
    Q002 --> Q202
    Q002 --> Q204
    Q003 --> Q701
    Q004 --> Q405
    Q005 --> Q501
    Q006 --> Q602

    %% ==========================================
    %% SZERTEÁGAZÓ KERESZTKAPCSOLATOK (CROSS-LINKS)
    %% ==========================================

    %% Piac korlát -> Üzleti modell kényszer
    Q202 ==>|Korlátozza a növekedést| Q501
    Q204 ==>|Megköveteli a partnercsatornát| Q405

    %% Vevői jogi vétó -> Megvalósítási architektúra
    Q105 ==>|Kikényszeríti az aggregált anonim mérést| Q006
    Q105 -.->|Ha a dolgozók megfigyelésnek érzik| GATE_SURVEILLANCE["GATE: Ellenállás miatti kudarc"]

    %% Módszertani hitelesség -> Gazdasági vásárlói elfogadás
    Q701 -->|Meghatározza a fizetési hajlandóságot| Q001
    Q701 -.->|Ha a vezetés csak 'játéknak' látja| GATE_TRIVIAL["GATE: L&D büdzsé megtagadva"]

    %% Facilitátor skálázás -> Pénzügyi árrés és Partner modell
    Q602 -->|Emeli a változó költséget (tréneri napidíj)| Q005
    Q405 -->|Csökkenti a CAC-ot, de viszi a margin 20-30%-át| Q005
    Q602 -.->|Ha nem tanítható be külsős| GATE_BOUTIQUE["GATE: Boutique Consulting Csapda"]

    %% Ismétlődő bevétel (LTV) visszacsatolása az értékesítési megtérülésre
    Q501 -->|Magasabb LTV megengedi a magasabb CAC-ot| Q202

    %% ==========================================
    %% VÉGSŐ DÖNTÉSI KAPUK (DECISION GATES)
    %% ==========================================
    Q501 -.->|Ha nincs re-measurement| STOP_TREADMILL["STOP: Egyalkalmas mókuskerék modell"]
```

---

## 2. A Kérdések Kereszthatás- és Függőségi Mátrixa

A fenti gráf nemcsak hierarchikus, hanem az alábbi konkrét összefüggéseket kényszeríti ki az elemzés során:

| Forrás kérdés / Dimenzió | Cél kérdés / Dimenzió | Kapcsolat jellege | Üzleti következmény és szabály |
| :--- | :--- | :--- | :--- |
| **Q-202 (HU SAM/SOM Plafon)** | **Q-501 (Ismétlődő LTV)** | *Kényszerítő függőség (Constraint)* | Mivel a magyar piac 3. évben legfeljebb 75M Ft-ot (150 workshop) bír el, a cég nem maradhat egyalkalmas rendezvénymodellben; kötelező a negyedéves újramérés vagy a termékbővítés. |
| **Q-204 (CEE Terjeszkedés)** | **Q-405 (Partnercsatorna)** | *Stratégiai előfeltétel (Enabler)* | A cseh és osztrák piac elérése saját értékesítési csapattal túl drága (magas CAC); helyi OD partnerekkel és nemzetközi BSC ajánlásokkal kell belépni. |
| **Q-105 (Üzemi Tanács / Mt. 264. §)** | **Q-603 (GDPR & Adatstruktúra)** | *Jogi korlát (Hard Compliance)* | Nem lehet egyéni neveket és teljesítményértékelést a riportba tenni. Csak szerepkör- és csapatszintű aggregált hálózat mutatható, különben a bevezetés elakad. |
| **Q-701 (Ökológiai Validitás)** | **Q-101 (Gazdasági Vásárló)** | *Befolyásolás (Influence)* | A COO szkeptikus, hogy 90 perc kockadobálás leképezi-e a valóságot. Ha a debrief nem kapcsolja össze a játékot a hétfő reggeli folyamatokkal, a szolgáltatás élménycsapatépítővé degradálódik. |
| **Q-602 (Facilitátor Skálázás)** | **Q-506 (Unit Economics)** | *Költség-áttétel (Trade-off)* | Ha a tréninget alvállalkozó tartja (napi 150–250e Ft díjért), a bruttó árrés 75–80%-ról 45–55%-ra esik. Ezt csak a platformlicenc-díjjal vagy magasabb árazással lehet ellensúlyozni. |
| **Q-405 (Partner OD cégek)** | **Q-507 (CAC & Értékesítés)** | *Csatornaszinergia (Synergy)* | Ha a tréningügynökségek nem versenytársak, hanem viszonteladók (20–30% jutalékkal), a PeerPlay B2B értékesítési költsége és átfutási ideje drasztikusan lecsökken. |

---

## 3. A 6 Kutatási Terület Frissített Térképe & Fájljai

* 🧑‍💼 **Customer & Problem:** [[02-Ventures/PeerPlay/Research/Customer]]  
  *Státusz:* ✅ Elkészült (Krónikus silófájdalom, kiváltó események, 5 érintetti perszóna, Mt. 264. § megfelelőség).
* 📈 **Market Intelligence:** [[02-Ventures/PeerPlay/Research/Market]]  
  *Státusz:* ✅ Elkészült (1 759 magyar 150+ cég, 888M Ft SAM, 75M Ft SOM, BSC beachhead, CEE-6 potenciál).
* ⚔️ **Competitive Intelligence:** [[02-Ventures/PeerPlay/Research/Competition]]  
  *Bemenet:* `[[Prompt-04-Input.md]]` $\rightarrow$ Csapatépítők, Boutique OD cégek, RunIT szimulációk, OrgMapper / Viva Insights.
* 💰 **Business Model Intelligence:** [[02-Ventures/PeerPlay/Research/Business-Model]]  
  *Bemenet:* `[[Prompt-05-Input.md]]` $\rightarrow$ Tranzakciós vs. Előfizetéses újramérés vs. Partner licenszmodell.
* 📊 **Financial Intelligence:** [[02-Ventures/PeerPlay/Research/Financial]]  
  *Bemenet:* `[[Prompt-06-Input.md]]` $\rightarrow$ 400k/500k/600k Ft árrések, Facilitátori napidíjak, CAC:LTV, fedezeti pont.
* ⚖️ **Execution & Operations:** [[02-Ventures/PeerPlay/Research/Execution]]  
  *Bemenet:* `[[Prompt-07-Input.md]]` $\rightarrow$ PWA offline architektúra, ONA PDF motor, Facilitátor playbook, Mt. 264. § DPO egyoldalas.
