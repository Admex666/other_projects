---
description: How to run the KnowCoin Analytics Dashboard
---

Ez a workflow segít elindítani a Streamlit alapú analitikai felületet.

### Előfeltételek
- Telepített Python 3.8+
- Ingyenes MongoDB Atlas fiók (már megvan)
- **Kritikus:** A szervernek futnia kell (lehetőleg `npm run start:dev` módban, hogy minden frissítést megkapjon)!

### Lépések

1. Navigálj a dashboard mappába:
```powershell
cd e:\Data\other_projects\QuizCasino\quiz_server\dashboard
```

2. Telepítsd a szükséges csomagokat (csak az első alkalommal):
// turbo
```powershell
pip install -r requirements.txt
```

3. Állítsd be a környezeti változót (vagy hozz létre egy `.env` fájlt a mappában):
```powershell
$env:MONGODB_URI="a-te-mongodb-connection-stringed"
```

4. Indítsd el a dashboardot:
```powershell
streamlit run main.py
```

A böngésződben automatikusan megnyílik a felület (általában a `http://localhost:8501` címen).
