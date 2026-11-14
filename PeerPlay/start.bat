@echo off
setlocal
title PeerPlay V2 - Local Dev Server

cd /d "%~dp0"
set "PATH=E:\nodejs;%PATH%"

echo =======================================================
echo          PeerPlay V2 - The Trading Game
echo       Helyi Fejlesztoi Kornyezet Inditasa
echo =======================================================
echo.

echo [INFO] Prisma Client ellenorzese...
call npx.cmd prisma generate

echo.
echo =======================================================
echo   A Next.js szerver elindul:
echo.
echo   [PC-ROL - BONGESZOBEN]
echo   - Fooldal:           http://localhost:3000
echo   - Facilitatori Pult: http://localhost:3000/dashboard
echo     ^> Vedett PIN Kod: 2026
echo.
echo   [MOBILROL - WI-FI / INTERNET]
echo   - Nyilvanos Tunnel:  Kulon ablakban indul (Localtunnel)
echo   - QR Kod a fooldalon jelenik meg: http://localhost:3000
echo.
echo   Session Kod:         DEMO01
echo =======================================================
echo.

start "PeerPlay - Mobil Tunnel" cmd /k "title PeerPlay Mobil Tunnel & cd /d "%~dp0" & set "PATH=E:\nodejs;%%PATH%%" & node scripts\start-tunnel.js"

start "" "http://localhost:3000"

call npm.cmd run dev

if errorlevel 1 (
    echo.
    echo [HIBA] A szerver futasa leallt!
    pause
)
