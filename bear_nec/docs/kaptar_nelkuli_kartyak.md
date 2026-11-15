# Kaptár nélküli kártyák listája (Bear Necessities)

Ez a dokumentum azokat a játékkártyákat listázza, amelyek **NEM tartalmaznak kaptárt** (`beeHives: 0`), azaz a kijátszásukkor nem adnak kaptár ikont a kör végi Bee Time döntéshez.

A katalógus 94 lapjából a pontosított adatok alapján **58 darab kártya** nem tartalmaz kaptárt.

> [!NOTE]
> **Számozási magyarázat (Képfájl vs Katalógus ID):**
> A játék eredeti spritesheet táblájában minden színcsoport után egy kártyahátlap volt elhelyezve (slot 23: Víz hátlap, slot 45: Sivatag hátlap, slot 70: Város hátlap).
> A `public/assets/cards` mappában csak a játszható kártyák lettek folytonosan számozva (`card_01.webp` – `card_94.webp`). Ezért:
> - A **Víz** kártyáknál (slot 0..22) a képfájl sorszáma `ID + 1` (pl. ID 0 = `card_01.webp`).
> - A **Sivatag** kártyáknál (slot 24..44) az 1 hátlap kivonása miatt az ID és a képfájl száma pontosan megegyezik (pl. ID 26 = `card_26.webp`, ID 42 = `card_42.webp`).
> - A **Város (Piros)** kártyáknál (slot 46..69) már 2 hátlap esett ki előtte, így a képfájl száma `ID - 1` (pl. ID 46 Macska = `card_45.webp`, ID 59 Színész = `card_58.webp`, ID 63 Kismedve = `card_62.webp`).
> - A **Hegy (Zöld)** kártyáknál (slot 71..96) 3 hátlap esett ki, így a képfájl száma `ID - 2` (pl. ID 71 Sas = `card_69.webp`).

> [!TIP]
> A táblázatban minden kártya képe közvetlenül megjelenik előnézetként, rákattintva pedig megnyílik az eredeti WebP képfájl.

---

## Összesítés színek / élőhelyek szerint

| Élőhely / Szín | Kártyák száma | Összes lap a pakliban | Arány |
| :--- | :---: | :---: | :---: |
| **Víz (Water - Kék)** | 15 db | 23 db | 65.2% |
| **Sivatag (Desert - Sárga)** | 14 db | 21 db | 66.7% |
| **Város (City - Piros)** | 14 db | 24 db | 58.3% |
| **Hegy (Mountain - Zöld)** | 15 db | 26 db | 57.7% |
| **Összesen** | **58 db** | **94 db** | **61.7%** |

---

## Víz (Water - Kék) (15 db)

| Kép | Katalógus ID | Kártya neve | Típus | Cél? | Képesség / Pontozás leírása |
| :---: | :---: | :--- | :--- | :---: | :--- |
| <a href="file:///C:/Users/Adam/Data/other_projects/bear_nec/public/assets/cards/card_01.webp"><img src="../public/assets/cards/card_01.webp" width="130" alt="Baby Beaver" /></a> | `0` | **Baby Beaver** | `animal` | Igen | 2 points. Goal: 8 points if adjacent to Beaver Dad or Beaver Mom. |
| <a href="file:///C:/Users/Adam/Data/other_projects/bear_nec/public/assets/cards/card_08.webp"><img src="../public/assets/cards/card_08.webp" width="130" alt="Fish" /></a> | `7` | **Fish** | `animal` | Nem | 2 points per BLUE card in your largest group of adjacent BLUE cards. |
| <a href="file:///C:/Users/Adam/Data/other_projects/bear_nec/public/assets/cards/card_09.webp"><img src="../public/assets/cards/card_09.webp" width="130" alt="Fish" /></a> | `8` | **Fish** | `animal` | Nem | 2 points per BLUE card in your largest group of adjacent BLUE cards. |
| <a href="file:///C:/Users/Adam/Data/other_projects/bear_nec/public/assets/cards/card_10.webp"><img src="../public/assets/cards/card_10.webp" width="130" alt="Fish" /></a> | `9` | **Fish** | `animal` | Nem | 2 points per BLUE card in your largest group of adjacent BLUE cards. |
| <a href="file:///C:/Users/Adam/Data/other_projects/bear_nec/public/assets/cards/card_11.webp"><img src="../public/assets/cards/card_11.webp" width="130" alt="Fish" /></a> | `10` | **Fish** | `animal` | Nem | 2 points per BLUE card in your largest group of adjacent BLUE cards. |
| <a href="file:///C:/Users/Adam/Data/other_projects/bear_nec/public/assets/cards/card_12.webp"><img src="../public/assets/cards/card_12.webp" width="130" alt="Cabin" /></a> | `11` | **Cabin** | `building` | Nem | 4 points if adjacent to exactly 1 Bearfolk. |
| <a href="file:///C:/Users/Adam/Data/other_projects/bear_nec/public/assets/cards/card_13.webp"><img src="../public/assets/cards/card_13.webp" width="130" alt="Harbor" /></a> | `12` | **Harbor** | `building` | Igen | 2 points. Goal: 7 points if adjacent to at least 2 BLUE cards. |
| <a href="file:///C:/Users/Adam/Data/other_projects/bear_nec/public/assets/cards/card_14.webp"><img src="../public/assets/cards/card_14.webp" width="130" alt="Lighthouse" /></a> | `13` | **Lighthouse** | `building` | Nem | 2 points per BLUE card in this row and this column (counting itself once). |
| <a href="file:///C:/Users/Adam/Data/other_projects/bear_nec/public/assets/cards/card_15.webp"><img src="../public/assets/cards/card_15.webp" width="130" alt="Binoculars" /></a> | `14` | **Binoculars** | `item` | Nem | Activate a BLUE card in your tableau. |
| <a href="file:///C:/Users/Adam/Data/other_projects/bear_nec/public/assets/cards/card_16.webp"><img src="../public/assets/cards/card_16.webp" width="130" alt="Collector" /></a> | `15` | **Collector** | `bearfolk` | Nem | 3 points per Item in your tableau. |
| <a href="file:///C:/Users/Adam/Data/other_projects/bear_nec/public/assets/cards/card_17.webp"><img src="../public/assets/cards/card_17.webp" width="130" alt="Collector" /></a> | `16` | **Collector** | `bearfolk` | Igen | 2 points. Goal: 12 points if you have at least 5 cards of the same color. |
| <a href="file:///C:/Users/Adam/Data/other_projects/bear_nec/public/assets/cards/card_18.webp"><img src="../public/assets/cards/card_18.webp" width="130" alt="Telescope" /></a> | `17` | **Telescope** | `item` | Nem | Activate an Item in your tableau. |
| <a href="file:///C:/Users/Adam/Data/other_projects/bear_nec/public/assets/cards/card_19.webp"><img src="../public/assets/cards/card_19.webp" width="130" alt="Fisherbear" /></a> | `18` | **Fisherbear** | `bearfolk` | Nem | 4 points if adjacent to at least 1 BLUE card. |
| <a href="file:///C:/Users/Adam/Data/other_projects/bear_nec/public/assets/cards/card_20.webp"><img src="../public/assets/cards/card_20.webp" width="130" alt="Spy" /></a> | `19` | **Spy** | `bearfolk` | Nem | 2 points per BLUE card in any one opponent's tableau. |
| <a href="file:///C:/Users/Adam/Data/other_projects/bear_nec/public/assets/cards/card_23.webp"><img src="../public/assets/cards/card_23.webp" width="130" alt="Water Lily" /></a> | `22` | **Water Lily** | `plant` | Nem | 3 points per adjacent BLUE card. |

---

## Sivatag (Desert - Sárga) (14 db)

| Kép | Katalógus ID | Kártya neve | Típus | Cél? | Képesség / Pontozás leírása |
| :---: | :---: | :--- | :--- | :---: | :--- |
| <a href="file:///C:/Users/Adam/Data/other_projects/bear_nec/public/assets/cards/card_24.webp"><img src="../public/assets/cards/card_24.webp" width="130" alt="Coyote" /></a> | `24` | **Coyote** | `animal` | Nem | 4 points per adjacent GREEN card. |
| <a href="file:///C:/Users/Adam/Data/other_projects/bear_nec/public/assets/cards/card_25.webp"><img src="../public/assets/cards/card_25.webp" width="130" alt="Queen Bee" /></a> | `25` | **Queen Bee** | `animal` | Nem | 4 points per adjacent Hive symbol. |
| <a href="file:///C:/Users/Adam/Data/other_projects/bear_nec/public/assets/cards/card_29.webp"><img src="../public/assets/cards/card_29.webp" width="130" alt="Small Trading Post" /></a> | `29` | **Small Trading Post** | `building` | Igen | 2 points. Goal: 8 points if adjacent to exactly 2 different colors. |
| <a href="file:///C:/Users/Adam/Data/other_projects/bear_nec/public/assets/cards/card_30.webp"><img src="../public/assets/cards/card_30.webp" width="130" alt="Medium Trading Post" /></a> | `30` | **Medium Trading Post** | `building` | Igen | 2 points. Goal: 12 points if adjacent to exactly 3 different colors. |
| <a href="file:///C:/Users/Adam/Data/other_projects/bear_nec/public/assets/cards/card_31.webp"><img src="../public/assets/cards/card_31.webp" width="130" alt="Bearbecue" /></a> | `31` | **Bearbecue** | `item` | Nem | 6 points per adjacent Fish. |
| <a href="file:///C:/Users/Adam/Data/other_projects/bear_nec/public/assets/cards/card_32.webp"><img src="../public/assets/cards/card_32.webp" width="130" alt="Binoculars" /></a> | `32` | **Binoculars** | `item` | Nem | Activate a YELLOW card in your tableau. |
| <a href="file:///C:/Users/Adam/Data/other_projects/bear_nec/public/assets/cards/card_35.webp"><img src="../public/assets/cards/card_35.webp" width="130" alt="Signpost" /></a> | `35` | **Signpost** | `item` | Nem | 4 points per adjacent RED card. |
| <a href="file:///C:/Users/Adam/Data/other_projects/bear_nec/public/assets/cards/card_36.webp"><img src="../public/assets/cards/card_36.webp" width="130" alt="Water Canteen" /></a> | `36` | **Water Canteen** | `item` | Nem | 4 points per adjacent YELLOW card. |
| <a href="file:///C:/Users/Adam/Data/other_projects/bear_nec/public/assets/cards/card_37.webp"><img src="../public/assets/cards/card_37.webp" width="130" alt="Explorer" /></a> | `37` | **Explorer** | `bearfolk` | Nem | 3 points per different color adjacent. |
| <a href="file:///C:/Users/Adam/Data/other_projects/bear_nec/public/assets/cards/card_38.webp"><img src="../public/assets/cards/card_38.webp" width="130" alt="Photographer" /></a> | `38` | **Photographer** | `bearfolk` | Igen | 2 points. Goal: 8 points if an Animal is adjacent to its right. |
| <a href="file:///C:/Users/Adam/Data/other_projects/bear_nec/public/assets/cards/card_39.webp"><img src="../public/assets/cards/card_39.webp" width="130" alt="Spy" /></a> | `39` | **Spy** | `bearfolk` | Nem | 1 point per RED and 1 point per GREEN card in any one opponent's tableau. |
| <a href="file:///C:/Users/Adam/Data/other_projects/bear_nec/public/assets/cards/card_40.webp"><img src="../public/assets/cards/card_40.webp" width="130" alt="Spy" /></a> | `40` | **Spy** | `bearfolk` | Nem | 3 points per Goal symbol in any one opponent's tableau. |
| <a href="file:///C:/Users/Adam/Data/other_projects/bear_nec/public/assets/cards/card_41.webp"><img src="../public/assets/cards/card_41.webp" width="130" alt="Treasure Hunter" /></a> | `41` | **Treasure Hunter** | `bearfolk` | Igen | 2 points. Goal: 8 points if adjacent to at least 1 Goal symbol. |
| <a href="file:///C:/Users/Adam/Data/other_projects/bear_nec/public/assets/cards/card_44.webp"><img src="../public/assets/cards/card_44.webp" width="130" alt="Yucca" /></a> | `44` | **Yucca** | `plant` | Nem | 3 points per YELLOW card in your tableau. |

---

## Város (City - Piros) (14 db)

| Kép | Katalógus ID | Kártya neve | Típus | Cél? | Képesség / Pontozás leírása |
| :---: | :---: | :--- | :--- | :---: | :--- |
| <a href="file:///C:/Users/Adam/Data/other_projects/bear_nec/public/assets/cards/card_46.webp"><img src="../public/assets/cards/card_46.webp" width="130" alt="Dog" /></a> | `47` | **Dog** | `animal` | Nem | 3 points per adjacent Bearfolk. |
| <a href="file:///C:/Users/Adam/Data/other_projects/bear_nec/public/assets/cards/card_47.webp"><img src="../public/assets/cards/card_47.webp" width="130" alt="Pigeon" /></a> | `48` | **Pigeon** | `animal` | Nem | 4 points per Bearfolk in all rows below this card. |
| <a href="file:///C:/Users/Adam/Data/other_projects/bear_nec/public/assets/cards/card_50.webp"><img src="../public/assets/cards/card_50.webp" width="130" alt="Suburban Apartments" /></a> | `51` | **Suburban Apartments** | `building` | Nem | 2 points per complete column (3 cards). |
| <a href="file:///C:/Users/Adam/Data/other_projects/bear_nec/public/assets/cards/card_51.webp"><img src="../public/assets/cards/card_51.webp" width="130" alt="Station" /></a> | `52` | **Station** | `building` | Nem | 3 points per complete row (4 cards). |
| <a href="file:///C:/Users/Adam/Data/other_projects/bear_nec/public/assets/cards/card_53.webp"><img src="../public/assets/cards/card_53.webp" width="130" alt="Town Hall" /></a> | `54` | **Town Hall** | `building` | Nem | 2 points per RED card in this row and this column (counting itself once). |
| <a href="file:///C:/Users/Adam/Data/other_projects/bear_nec/public/assets/cards/card_55.webp"><img src="../public/assets/cards/card_55.webp" width="130" alt="Binoculars" /></a> | `56` | **Binoculars** | `item` | Nem | Activate a RED card in your tableau. |
| <a href="file:///C:/Users/Adam/Data/other_projects/bear_nec/public/assets/cards/card_56.webp"><img src="../public/assets/cards/card_56.webp" width="130" alt="Streetlight" /></a> | `57` | **Streetlight** | `item` | Igen | 2 points. Goal: 12 points if adjacent to at least 2 Buildings. |
| <a href="file:///C:/Users/Adam/Data/other_projects/bear_nec/public/assets/cards/card_57.webp"><img src="../public/assets/cards/card_57.webp" width="130" alt="Statue" /></a> | `58` | **Statue** | `item` | Nem | 2 points per column with at least 1 RED card. |
| <a href="file:///C:/Users/Adam/Data/other_projects/bear_nec/public/assets/cards/card_61.webp"><img src="../public/assets/cards/card_61.webp" width="130" alt="Football Player" /></a> | `62` | **Football Player** | `bearfolk` | Igen | 2 points. Goal: 8 points if this row is complete. |
| <a href="file:///C:/Users/Adam/Data/other_projects/bear_nec/public/assets/cards/card_64.webp"><img src="../public/assets/cards/card_64.webp" width="130" alt="Sergeant" /></a> | `65` | **Sergeant** | `bearfolk` | Nem | 3 points per Bearfolk in this row. |
| <a href="file:///C:/Users/Adam/Data/other_projects/bear_nec/public/assets/cards/card_65.webp"><img src="../public/assets/cards/card_65.webp" width="130" alt="Spy" /></a> | `66` | **Spy** | `bearfolk` | Nem | 2 points per YELLOW card in any one opponent's tableau. |
| <a href="file:///C:/Users/Adam/Data/other_projects/bear_nec/public/assets/cards/card_66.webp"><img src="../public/assets/cards/card_66.webp" width="130" alt="Window Cleaner" /></a> | `67` | **Window Cleaner** | `bearfolk` | Igen | 2 points. Goal: 7 points if this column is complete. |
| <a href="file:///C:/Users/Adam/Data/other_projects/bear_nec/public/assets/cards/card_67.webp"><img src="../public/assets/cards/card_67.webp" width="130" alt="Planter Box" /></a> | `68` | **Planter Box** | `plant` | Nem | 2 points per row with at least 1 RED card. |
| <a href="file:///C:/Users/Adam/Data/other_projects/bear_nec/public/assets/cards/card_68.webp"><img src="../public/assets/cards/card_68.webp" width="130" alt="Rose" /></a> | `69` | **Rose** | `plant` | Igen | 2 points. Goal: 10 points if adjacent to exactly 2 Bearfolk. |

---

## Hegy (Mountain - Zöld) (15 db)

| Kép | Katalógus ID | Kártya neve | Típus | Cél? | Képesség / Pontozás leírása |
| :---: | :---: | :--- | :--- | :---: | :--- |
| <a href="file:///C:/Users/Adam/Data/other_projects/bear_nec/public/assets/cards/card_72.webp"><img src="../public/assets/cards/card_72.webp" width="130" alt="Lookout Tower" /></a> | `74` | **Lookout Tower** | `building` | Nem | 1 point per card in your tableau not adjacent to this card. |
| <a href="file:///C:/Users/Adam/Data/other_projects/bear_nec/public/assets/cards/card_74.webp"><img src="../public/assets/cards/card_74.webp" width="130" alt="Visitor Center" /></a> | `76` | **Visitor Center** | `building` | Igen | 2 points. Goal: 7 points if all 4 colors are in your tableau. |
| <a href="file:///C:/Users/Adam/Data/other_projects/bear_nec/public/assets/cards/card_75.webp"><img src="../public/assets/cards/card_75.webp" width="130" alt="Backpack" /></a> | `77` | **Backpack** | `item` | Igen | 2 points. Goal: 8 points if you have at least 3 Items in your tableau. |
| <a href="file:///C:/Users/Adam/Data/other_projects/bear_nec/public/assets/cards/card_76.webp"><img src="../public/assets/cards/card_76.webp" width="130" alt="Binoculars" /></a> | `78` | **Binoculars** | `item` | Nem | Activate a GREEN card in your tableau. |
| <a href="file:///C:/Users/Adam/Data/other_projects/bear_nec/public/assets/cards/card_77.webp"><img src="../public/assets/cards/card_77.webp" width="130" alt="Water Trough" /></a> | `79` | **Water Trough** | `item` | Nem | 4 points per adjacent Animal. |
| <a href="file:///C:/Users/Adam/Data/other_projects/bear_nec/public/assets/cards/card_79.webp"><img src="../public/assets/cards/card_79.webp" width="130" alt="Weather Forecast: City" /></a> | `81` | **Weather Forecast: City** | `item` | Nem | 7 points if the card in your reserve is RED. |
| <a href="file:///C:/Users/Adam/Data/other_projects/bear_nec/public/assets/cards/card_80.webp"><img src="../public/assets/cards/card_80.webp" width="130" alt="Weather Forecast: Water" /></a> | `82` | **Weather Forecast: Water** | `item` | Nem | 7 points if the card in your reserve is BLUE. |
| <a href="file:///C:/Users/Adam/Data/other_projects/bear_nec/public/assets/cards/card_82.webp"><img src="../public/assets/cards/card_82.webp" width="130" alt="Weather Forecast: Desert" /></a> | `84` | **Weather Forecast: Desert** | `item` | Nem | 7 points if the card in your reserve is YELLOW. |
| <a href="file:///C:/Users/Adam/Data/other_projects/bear_nec/public/assets/cards/card_84.webp"><img src="../public/assets/cards/card_84.webp" width="130" alt="Guide" /></a> | `86` | **Guide** | `bearfolk` | Nem | Activate a Bearfolk in your tableau. |
| <a href="file:///C:/Users/Adam/Data/other_projects/bear_nec/public/assets/cards/card_86.webp"><img src="../public/assets/cards/card_86.webp" width="130" alt="Spy" /></a> | `88` | **Spy** | `bearfolk` | Nem | 1 point per YELLOW and 1 point per GREEN card in any one opponent's tableau. |
| <a href="file:///C:/Users/Adam/Data/other_projects/bear_nec/public/assets/cards/card_87.webp"><img src="../public/assets/cards/card_87.webp" width="130" alt="Spy" /></a> | `89` | **Spy** | `bearfolk` | Nem | 1 point per RED and 1 point per BLUE card in any one opponent's tableau. |
| <a href="file:///C:/Users/Adam/Data/other_projects/bear_nec/public/assets/cards/card_88.webp"><img src="../public/assets/cards/card_88.webp" width="130" alt="Spy" /></a> | `90` | **Spy** | `bearfolk` | Nem | 2 points per Bee token owned by any one opponent. |
| <a href="file:///C:/Users/Adam/Data/other_projects/bear_nec/public/assets/cards/card_89.webp"><img src="../public/assets/cards/card_89.webp" width="130" alt="Wildlife Ranger" /></a> | `91` | **Wildlife Ranger** | `bearfolk` | Nem | 3 points per Animal in your tableau. |
| <a href="file:///C:/Users/Adam/Data/other_projects/bear_nec/public/assets/cards/card_90.webp"><img src="../public/assets/cards/card_90.webp" width="130" alt="Berries" /></a> | `92` | **Berries** | `plant` | Nem | 4 points per Animal in this row. |
| <a href="file:///C:/Users/Adam/Data/other_projects/bear_nec/public/assets/cards/card_91.webp"><img src="../public/assets/cards/card_91.webp" width="130" alt="Dandelion" /></a> | `93` | **Dandelion** | `plant` | Nem | 7 points when placed. 1 point when activated by another card. |

---

