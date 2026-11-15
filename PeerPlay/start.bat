@echo off
setlocal
title PeerPlay V2 - Local Dev Server

cd /d "%~dp0"

if exist "E:\nodejs" (
    set "PATH=E:\nodejs;%PATH%"
)

echo =======================================================
echo          PeerPlay V2 - The Trading Game
echo       Helyi Fejlesztoi Kornyezet Inditasa
echo =======================================================
echo.

if not exist "node_modules" (
    echo [INFO] A fuggosegek hianyoznak, npm install futtatasa...
    call npm.cmd install
    if errorlevel 1 (
        echo [HIBA] Az npm install nem sikerult!
        pause
        exit /b 1
    )
)

echo [INFO] Prisma Client ellenorzese...
call npx.cmd prisma generate

echo [INFO] Szabad port keresese...
for /f "delims=" %%p in ('node scripts\find-free-port.js 3000') do set "PORT=%%p"

if "%PORT%"=="" (
    echo [FIGYELMEZTETES] Nem sikerult automatikusan portot talalni, alapertelmezett 3000-es port hasznalata.
    set "PORT=3000"
)

echo [INFO] Kivalasztott port: %PORT%

echo.
echo =======================================================
echo   A Next.js szerver elindul:
echo.
echo   [PC-ROL - BONGESZOBEN]
echo   - Fooldal:           http://localhost:%PORT%
echo   - Facilitatori Pult: http://localhost:%PORT%/dashboard
echo     ^> Vedett PIN Kod: 2026
echo.
echo   [MOBILROL - WI-FI / INTERNET]
echo   - Nyilvanos Tunnel:  Hatterben fut (Localtunnel)
echo   - QR Kod a fooldalon jelenik meg: http://localhost:%PORT%
echo.
echo   Session Kod:         DEMO01
echo =======================================================
echo.

echo [INFO] Mobil tunnel inditasa a hatterben (%PORT%-es port)...
start /b "" node scripts\start-tunnel.js %PORT%

start "" "http://localhost:%PORT%"

call npm.cmd run dev

if errorlevel 1 (
    echo.
    echo [HIBA] A szerver futasa leallt!
    pause
)
