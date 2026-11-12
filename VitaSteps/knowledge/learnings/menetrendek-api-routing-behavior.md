# Learning: Menetrendek.hu API Viselkedés és Átszállási Rendezés

## Felfedezés dátuma: 2026-11-12

### 1. Rendezési mechanizmus (`rendezes`)
- **`rendezes: 0` (Alapértelmezett API viselkedés):** Az algoritmus az **átszállások száma szerint csoportosít**. Először az összes 1 átszállásos kapcsolatot adja vissza (akár jóval hosszabb menetidővel vagy későbbi indulással), és csak a lista végére teszi a 2 átszállásos, de jóval gyorsabb kapcsolatokat.
- **`rendezes: 1` (Webes felület és Google Maps logika):** Szigorúan **indulási idő szerint növekvő** sorrendbe állítja az útvonalakat. Így a reggeli 08:01-es H5 HÉV + 08:24-es Aquincum S76 vonat azonnal az 1. találatként jelenik meg.

### 2. Belső Adatstruktúra azonosítók (`runs` szótárban)
A Menetrendek.hu JSON válaszában a mezők pozíciós indexekkel érkeznek:
- `run['6']`: Indulási idő percben éjféltől (pl. 481 = 08:01)
- `run['7']`: Érkezési idő percben éjféltől (pl. 498 = 08:18)
- `run['11']`: Hálózat ID (`2` = Vasút, `13`/`24` = HÉV/BKK, `1` = Volánbusz)
- `run['23']`: Induló állomás / megállóhely neve (pl. `Pomáz vá.`)
- `run['24']`: Érkező állomás / megállóhely neve (pl. `Aquincum mh.`)
- `run['29']`: Közlekedési naptípus / magyarázat (pl. `szabadnapokon`, `naponta`)
- `run['38']`: Valós járatszám / vonalnév (pl. `H5`, `S76`, `218`)

### 3. Aquincumi átszállás specifitása
Aquincumnál a HÉV megálló (`Aquincum mh.`, ID: `63664`) és a vasúti megállóhely (`Aquincum vmh.`, ID: `27501429`) külön azonosítóval fut, köztük a gyalogos átszállás kb. 150-200 méter (4 perc átszállási idővel kalkulál a rendszer).
