# 📊 Pilis Vertical Kampány P&L és Cashflow Szimulációk

Ez a dokumentum a Pilis Vertical kampány részletes pénzügyi forgatókönyv-elemzését tartalmazza (ár: **8,990 Ft**), különválasztva az **eredményszemléletű nyereséget (P&L)** és a **pénzforgalmi szemléletet (Cashflow)**.

---

## 🗺️ 1. Meta Ads CPA vs. Eladott Érmek Heatmap (EBIT Profit / Veszteség)
A táblázat cellái a nettó eredményt (EBIT) mutatják a különböző ügyfélszerzési költségek (CPA) és eladott darabszámok mellett.
*Pirossal jelölve a veszteséges szcenáriók.*

| Eladott db | CPA: 1 000 Ft | CPA: 2 000 Ft | CPA: 3 000 Ft | CPA: 4 000 Ft | CPA: 5 000 Ft | CPA: 6 000 Ft |
|:---|---:|---:|---:|---:|---:|---:|
| **15 db** | <span style='color: #c4ff00;'>+16,805 Ft</span> | <span style='color: #c4ff00;'>+1,805 Ft</span> | <span style='color: #ff4a4a;'>-13,195 Ft</span> | <span style='color: #ff4a4a;'>-28,195 Ft</span> | <span style='color: #ff4a4a;'>-43,195 Ft</span> | <span style='color: #ff4a4a;'>-58,195 Ft</span> | 
| **30 db** | <span style='color: #c4ff00;'>+92,030 Ft</span> | <span style='color: #c4ff00;'>+62,030 Ft</span> | <span style='color: #c4ff00;'>+32,030 Ft</span> | <span style='color: #c4ff00;'>+2,030 Ft</span> | <span style='color: #ff4a4a;'>-27,970 Ft</span> | <span style='color: #ff4a4a;'>-57,970 Ft</span> | 
| **45 db** | <span style='color: #c4ff00;'>+167,255 Ft</span> | <span style='color: #c4ff00;'>+122,255 Ft</span> | <span style='color: #c4ff00;'>+77,255 Ft</span> | <span style='color: #c4ff00;'>+32,255 Ft</span> | <span style='color: #ff4a4a;'>-12,745 Ft</span> | <span style='color: #ff4a4a;'>-57,745 Ft</span> | 
| **60 db** | <span style='color: #c4ff00;'>+233,300 Ft</span> | <span style='color: #c4ff00;'>+173,300 Ft</span> | <span style='color: #c4ff00;'>+113,300 Ft</span> | <span style='color: #c4ff00;'>+53,300 Ft</span> | <span style='color: #ff4a4a;'>-6,700 Ft</span> | <span style='color: #ff4a4a;'>-66,700 Ft</span> | 
| **80 db** | <span style='color: #c4ff00;'>+333,560 Ft</span> | <span style='color: #c4ff00;'>+253,560 Ft</span> | <span style='color: #c4ff00;'>+173,560 Ft</span> | <span style='color: #c4ff00;'>+93,560 Ft</span> | <span style='color: #c4ff00;'>+13,560 Ft</span> | <span style='color: #ff4a4a;'>-66,440 Ft</span> | 
| **100 db** | <span style='color: #c4ff00;'>+433,900 Ft</span> | <span style='color: #c4ff00;'>+333,900 Ft</span> | <span style='color: #c4ff00;'>+233,900 Ft</span> | <span style='color: #c4ff00;'>+133,900 Ft</span> | <span style='color: #c4ff00;'>+33,900 Ft</span> | <span style='color: #ff4a4a;'>-66,100 Ft</span> | 

---

## 🎯 2. Veszteség Valószínűsége (Kockázatelemzés)
Ha feltételezzük, hogy a hirdetési **CPA normális eloszlást követ** (várható érték: **3 000 Ft**, szórás: **1 000 Ft**), kiszámolható, mekkora eséllyel zárjuk veszteséggel a kampányt:

| Eladott db | Küszöb CPA (Fedezeti CPA)* | Veszteség esélye | Minősítés |
|:---|---:|---:|:---|
| **15 db** | 2120 Ft | **81.0%** | 🔴 Kritikus kockázat |
| **30 db** | 4068 Ft | **14.3%** | 🟢 Alacsony kockázat |
| **45 db** | 4717 Ft | **4.3%** | 🟢 Alacsony kockázat |
| **60 db** | 4888 Ft | **2.9%** | 🟢 Alacsony kockázat |
| **80 db** | 5170 Ft | **1.5%** | 🟢 Alacsony kockázat |
| **100 db** | 5339 Ft | **1.0%** | 🟢 Alacsony kockázat |

*\* Fedezeti CPA: Az a maximális CPA, aminél a projekt éppen nullszaldós. Ha a valós CPA ennél magasabb, a projekt veszteséges.*

---

## 💸 3. Cashflow Profil (Pénzforgalmi Szemlélet)
**A cashflow eltér az eredményszemlélettől:**
*   **Júliusban** azonnal kifizetjük a teljes 100 darabos éremgyártást (**151 244 Ft**) és a borítékokat (**4 527 Ft**), függetlenül attól, hány nevezőnk van.
*   **A szállítási díjat (FoxPost)** viszont csak a teljesítések ütemében (augusztusban 20%, szeptemberben 80%) fizetjük ki.
*   *Feltételezés:* Átlagos **3 000 Ft-os CPA**-val számolva.

| Szcenárió | Július Net CF (Pre-launch) | Augusztus CF | Szeptember CF | Halmozott Egyenleg (Profit) |
|:---|---:|---:|---:|---:|
| **15 db** | -97,622 Ft | -18,600 Ft | -29,400 Ft | **-145,622 Ft** |
| **30 db** | -11,057 Ft | -22,200 Ft | -43,800 Ft | **-77,057 Ft** |
| **45 db** | +75,508 Ft | -25,800 Ft | -58,200 Ft | **-8,492 Ft** |
| **60 db** | +152,916 Ft | -29,400 Ft | -72,600 Ft | **+50,916 Ft** |
| **80 db** | +268,336 Ft | -34,200 Ft | -91,800 Ft | **+142,336 Ft** |
| **100 db** | +383,756 Ft | -39,000 Ft | -111,000 Ft | **+233,756 Ft** |

> [!WARNING]
> **Finanszírozási rés (Cashflow kockázat):**
> *   **15 és 30 db eladott éremnél** a júliusi pre-launch időszakot még **negatív egyenleggel** zárjuk, mert a kevés eladás nem fedezi a 100 darab érem előre kifizetett gyártási díját.
> *   A júliusi cashflow **45 db eladott éremtől válik pozitívvá** (+75 508 Ft), a teljes projekt szintű halmozott egyenlegünk pedig **60 eladott éremtől fordul nyereségbe** (+50 916 Ft). Ez a minimális eladási célunk, hogy a projekt önfinanszírozó legyen!
