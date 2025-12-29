# PokerPro - Quick Setup Guide

## 🚀 Gyors Indítás (5 perc)

### 1. Backend Setup

```powershell
cd backend

# Függőségek telepítése
pip install -r requirements.txt

# Adatbázis létrehozása (SQLite - automatikus)
python init_db.py

# Backend indítása
uvicorn main:app --reload
```

✅ Backend fut: http://localhost:8000
📚 API dokumentáció: http://localhost:8000/docs

### 2. Frontend Setup

```powershell
cd frontend

# Függőségek telepítése
npm install

# Frontend indítása
npm run dev
```

✅ Frontend fut: http://localhost:5173

---

## 🔧 Hibaelhárítás

### PowerShell Execution Policy Error

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Missing pydantic-settings

```powershell
pip install pydantic-settings
```

### Port már használatban

Backend (8000) vagy Frontend (5173) port foglalt:
```powershell
# Backend más porton
uvicorn main:app --reload --port 8001

# Frontend más porton (vite.config.ts-ben módosítsd)
```

---

## 📦 Használt Technológiák

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy, SQLite
- **Frontend**: React 18, TypeScript, Vite, TailwindCSS
- **Auth**: JWT tokens, bcrypt password hashing

---

## 🎯 Első Lépések

1. Nyisd meg: http://localhost:5173
2. Kattints a "Register" gombra
3. Hozz létre egy fiókot
4. Töltsd ki az onboarding kérdőívet
5. Kezdj el tanulni! 🎓

---

## 📊 Adatbázis

SQLite fájl: `backend/pokerpro.db`

Táblák:
- users
- user_profiles
- user_goals
- learning_progress
- achievements
- hand_histories
- hand_analyses

---

## 🧪 API Tesztelés

### Swagger UI
http://localhost:8000/docs

### Példa API hívás (cURL)

```bash
# Regisztráció
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "password123"
  }'

# GTO range lekérése (token szükséges)
curl -X POST http://localhost:8000/api/gto/preflop \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "position": "BTN",
    "action": "rfi"
  }'
```

---

## 📝 Következő Lépések

- [ ] Academy oldal befejezése (lesson viewer)
- [ ] GTO Practice UI (range grid)
- [ ] Hand Analyzer UI (hand replay)
- [ ] Bankroll tracker
- [ ] Mental game modul

---

Részletes dokumentáció: `walkthrough.md`
