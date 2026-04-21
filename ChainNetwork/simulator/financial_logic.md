# ChainNetwork - Stratégiai és Pénzügyi Lebontás (ROI)

Ez a dokumentum bemutatja a **Decision Engine** (B csoport) működésének közgazdasági hátterét a 180 napos szimuláció alapján. A számítások 500 tesztfelhasználó viselkedésén alapulnak.

---

## 1. Modul: Lemorzsolódás megelőzése (Retention)
**Probléma:** A vásárlók egy része elfelejt visszatérni, vagy átpártol a konkurenciához.
**Megoldás:** Automatikus kupon küldése az egyéni látogatási ciklus megkétszereződésekor (Relative Recency > 2.0).

### A számok nyelve:
*   **Kiváltott események:** 2,800 alkalommal észlelt a rendszer "kritikus késést".
*   **Beavatkozás:** 2,800 db digitális kupon kiküldése (-20% kedvezmény).
*   **Konverziós ráta (Cvr):** 30% (840 felhasználó tért vissza a kupon hatására).
*   **Lemorzsolódás (Fail):** 70% (1,960 felhasználó az ajánlat ellenére sem jött vissza).

### Pénzügyi mérleg (Retention):
| Tétel | Számítás | Összeg |
| :--- | :--- | :--- |
| Mentett tranzakciók bevétele | 840 alkalom * 4,500 HUF | +3,780,000 HUF |
| **Kuponok költsége (Discount)** | 840 alkalom * 500 HUF | **-420,000 HUF** |
| Mentett tranzakciók alap árrése | 70% alap margin | +2,646,000 HUF |
| **Tiszta Profit Növekmény** | Bruttó profit - Discount | **+2,226,000 HUF** |

---

## 2. Modul: Kosárméret növelés (Upsell)
**Probléma:** Sok vásárló csak egy burgert venne, elfelejtve a kiegészítőket (ital, köret).
**Megoldás:** POS-szintű intelligens ajánlás (Next-Best-Offer) a kosárelemzés adatai alapján.

### A számok nyelve:
*   **Ajánlási lehetőség:** 3,200 tranzakció (ahol csak burger volt a kosárban).
*   **Sikeres ajánlat (Hit rate):** 20% (640 esetben vettek extra köretet/italt).
*   **Átlagos kosár növekmény:** +1,100 HUF / sikeres alkalom.

### Pénzügyi mérleg (Upsell):
| Tétel | Számítás | Összeg |
| :--- | :--- | :--- |
| Extra árbevétel | 640 alkalom * 1,100 HUF | +704,000 HUF |
| **Extra alap árrés (80%)** | Ital/Köret margin magasabb | **+563,200 HUF** |
| Marketing költség | 0 HUF (helyi ajánlás) | 0 HUF |
| **Tiszta Profit Növekmény** | | **+563,200 HUF** |

---

## 3. Összesített Üzleti Eredmény (180 nap / 500 user)

| Kategória | Érték | Megjegyzés |
| :--- | :--- | :--- |
| **Összes extra árbevétel** | **+4,484,000 HUF** | |
| **Összes tiszta profit növekmény** | **+2,789,200 HUF** | Kedvezmények után |
| **Egy felhasználóra jutó extra profit** | **+5,578 HUF** | 6 hónap alatt |
| **ROI (Marketing megtérülés)** | **6.6x** | Minden 1 forint kedvezmény 6.6 forint profitot hozott |

### Konklúzió az étteremvezető számára:
A rendszer nem csak "osztogatja a kedvezményt". A fenti adatok bizonyítják, hogy a **célzott beavatkozás** akkor is nyereséges, ha a vásárlók többsége nem reagál. A "B" csoportnál elért +23%-os bevételnövekedés mögött egy **kőkemény matematikai alapokon álló profit-optimalizáció** áll.
