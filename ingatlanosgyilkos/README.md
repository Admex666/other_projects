# Budapest Albérlet Elemző Projekt 🏠

Átfogó adatelemzési és gépi tanulási projekt Budapest kiadó lakásainak piacának elemzésére és árpredikciójára.

## 🎯 Funkciók

### 1. Web Scraping
- Automatikus hirdetésgyűjtés a Zenga.hu-ról
- Párhuzamos feldolgozás (8-9 Selenium driver)
- ~33 hirdetés/perc sebesség
- Inkrementális mentés és cache kezelés

### 2. Adatelemzés
- Interaktív szűrőrendszer (kerület, ár, terület, szobák)
- Statisztikai alapú "legjobb ajánlatok" azonosítása
- Vizualizációk (Plotly, ipywidgets)

### 3. Árpredikciós Model
- ML modellek: RandomForest, XGBoost, LightGBM, stb.
- Fejlett feature engineering (minőségi/lokációs indexek)
- Célfüggvény: bérleti díj/m² előrejelzése

## 📁 Projekt Struktúra

```
ingatlanosgyilkos/
├── data/               # Adatfájlok
│   ├── raw/           # Nyers scrapelt adatok
│   ├── processed/     # Tisztított adatok
│   └── external/      # Külső források (kerületi árak)
├── models/            # Betanított ML modellek (.pkl)
├── scripts/           #CLI scriptek (futtatható Python fájlok)
│   ├── scrape_details.py
│   ├── train_model.py
│   └── analyze_deals.py
├── notebooks/         # Jupyter notebook elemzések
│   ├── 01_data_collection/
│   ├── 02_exploration/
│   ├── 03_modeling/
│   └── 04_analysis/
├── src/               # Python modulok (újrafelhasználható kód)
│   ├── scraper.py
│   ├── preprocessing.py
│   ├── models.py
│   ├── analysis.py
│   └── utils.py
└── cache/             # Scraping cache fájlok
```

## 🚀 Telepítés

### Előfeltételek
- Python 3.8+
- Chrome böngésző (Selenium-hoz)

### Függőségek telepítése

```bash
pip install -r requirements.txt
```

## 💡 Használat

### Python Scriptek (Ajánlott)

#### 1. Adatgyűjtés

```bash
python scripts/scrape_details.py \
    --input data/raw/zenga_links.csv \
    --output data/raw/zenga_rentals_details.csv \
    --max-workers 9
```

#### 2. Modell Tanítás

```bash
python scripts/train_model.py \
    --data data/raw/zenga_rentals_details.csv \
    --district-prices data/external/budapest_district_prices_2023.csv \
    --output-dir models
```

#### 3. Legjobb Ajánlatok Keresése

```bash
python scripts/analyze_deals.py \
    --data data/raw/zenga_rentals_details.csv \
    --top-n 20 \
    --output results/best_deals.csv
```

**Szűréssel:**

```bash
python scripts/analyze_deals.py \
    --data data/raw/zenga_rentals_details.csv \
    --district 6 \
    --min-rooms 2 \
    --max-price 300
```

### Jupyter Notebookok (Exploráció)

Az eredeti notebookok megtekinthetők a `notebooks/` mappában.

```bash
jupyter notebook notebooks/04_analysis/01_interactive_rental_filter.ipynb
```

## 📊 Főbb Eredmények

- **1762 hirdetés** részletes adattal
- **R² score**: ~0.85-0.90 (modell függő)
- **RMSE**: ~10-15% relatív hiba
- **Statisztikai deal-finder**: Z-score alapú alulértékelt lakások

## 🛠️ Technológiák

- **Web Scraping**: Selenium, BeautifulSoup
- **Adatfeldolgozás**: Pandas, NumPy
- **ML**: scikit-learn, XGBoost, LightGBM
- **Vizualizáció**: Matplotlib, Seaborn, Plotly
- **Interaktív UI**: ipywidgets

## 📝 Megjegyzések

- A scraper csak kiadó lakásokat gyűjt
- Az adatok a Zenga.hu-ról származnak (2023-2025)
- A modellek csak Budapest területére érvényesek

## ⚖️ Licenc

Személyes/oktatási célra
