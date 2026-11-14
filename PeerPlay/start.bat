@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion
title PeerPlay V2 - Local Dev Server

cd /d "%~dp0"

echo =======================================================
echo          PeerPlay V2 · The Trading Game
echo       Helyi Fejlesztői Környezet Indítása
echo =======================================================
echo.

:: 1. Node.js ellenőrzése
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo [HIBA] A Node.js nincs telepítve vagy nincs a PATH-ban!
    echo Kérlek telepítsd a Node.js-t a https://nodejs.org oldalról.
    echo.
    pause
    exit /b 1
)

:: 2. Függőségek ellenőrzése
if not exist "node_modules\" (
    echo [INFO] node_modules nem található, telepítés folyamatban (npm install)...
    call npm install
    if %errorlevel% neq 0 (
        echo [HIBA] A függőségek telepítése sikertelen volt!
        pause
        exit /b 1
    )
)

:: 3. Prisma Client generálása
echo [INFO] Prisma Client ellenőrzése...
call npx prisma generate >nul 2>nul

:: 4. Adatbázis ellenőrzése és demó adatok betöltése szükség esetén
if not exist "prisma\dev.db" (
    echo [INFO] Adatbázis létrehozása és demó adatok betöltése (seed)...
    call npx prisma db push --skip-generate
    call npx tsx prisma\seed.ts
)

echo.
echo =======================================================
echo   A Next.js szerver elindul a háttérben:
echo   -> URL: http://localhost:3000
echo   -> Teszt munkamenet kód: DEMO01
echo.
echo   Közvetlen oldalak:
echo   - Főoldal:        http://localhost:3000
echo   - HR Dashboard:   http://localhost:3000/dashboard
echo   - Játékos Belépés:http://localhost:3000/join
echo =======================================================
echo.
echo [INFO] Böngésző megnyitása 3 másodperc múlva...

:: Böngésző megnyitása külön háttérszálon kis késleltetéssel
start "" cmd /c "timeout /t 3 /nobreak >nul && start http://localhost:3000"

:: 5. Next.js Dev Szerver futtatása
call npm run dev

if %errorlevel% neq 0 (
    echo.
    echo [HIBA] A szerver futása váratlanul leállt!
    pause
)
