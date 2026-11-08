@echo off
title Bear Necessities - Game Server
cd /d "%~dp0"

echo ========================================================
echo   Bear Necessities - Inditas...
echo ========================================================
echo.

:: 1. Build ellenorzese: ha nincs dist mappa, lebuildeljuk
if not exist "dist" (
    echo [1/2] Elso inditas: Frontend leforditasa (npm run build)...
    call npm run build
    if errorlevel 1 (
        echo HIBA: A frontend build sikertelen volt!
        pause
        exit /b 1
    )
) else (
    echo [1/2] Frontend mar le van forditva.
)

:: 2. Bongeszo automatikus megnyitasa kis kesleltetessel a hatterben
echo [2/2] Szerver inditasa es bongeszo megnyitasa...
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:3001"

:: 3. Node.js WebSocket + HTTP szerver futtatasa
echo.
echo ========================================================
echo   A jatek elindult!
echo   Bongeszo cime: http://localhost:3001
echo   (A szerver leallitasahoz zard be ezt az ablakot)
echo ========================================================
echo.

call npm run server

pause
