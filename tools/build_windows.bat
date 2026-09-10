@echo off
setlocal EnableDelayedExpansion
REM ============================================================
REM  AltMinimapVehiclenames - Windows Build & Deploy Script
REM  Erzeugt mod_altminimap_vehiclenames.pyc und packt die .wotmod.
REM  Haengt die .wotmod direkt in deine WoT-Mods ab.
REM ============================================================

set "PYCOMPILE=py -2 -m py_compile"
REM Falls du Python 2.7 als richtigen Befehl hast, dort alternativ:
REM set "PYCOMPILE=python27 -m py_compile"
REM set "PYCOMPILE=C:\Python27\python.exe -m py_compile"

REM --- Pfade (anspassen, falls abweichend) ---
REM WoT-Installation. Standard aus dem Protokoll:
set "WOTPATH=J:\Wargaming\World_of_Tanks_EU"
set "CUSTOMMODSDIR=%WOTPATH%\Aslain_Modpack\Custom_mods\mods\version"
REM Mods-Versionordner deines Clients:
set "MODSVER=2.4.0.0"

REM --- Arbeitsverzeichnis des Repos ---
set "REPO=%~dp0.."

set "SRC=%REPO%\modsrc\mod_altminimap_vehiclenames.py"
set "MODNAME=AltMinimapVehiclenames"

echo.
echo == 1/5 - Kompiliere mit Python 2.7 ==
cd /d "%REPO%\modsrc"
%PYCOMPILE% mod_altminimap_vehiclenames.py
if errorlevel 1 (
  echo [FEHLER] Kompilierung fehlgeschlagen.
  echo   Bitte Pfad zu Python 2.7 oben in PYCOMPILE setzen.
  exit /b 1
)
if not exist "mod_altminimap_vehiclenames.pyc" (
  echo [FEHLER] .pyc wurde nicht erzeugt.
  exit /b 1
)
echo  .pyc erzeugt.

echo.
echo == 2/5 - .wotmod zusammenstellen ==
set "STAGE=%TEMP%\AltMinimap_build"
if exist "%STAGE%" rmdir /s /q "%STAGE%"
mkdir "%STAGE%\res\scripts\client\gui\mods"
copy /y "%REPO%\meta.xml" "%STAGE%\meta.xml" ^
  >nul
copy /y "mod_altminimap_vehiclenames.pyc" "%STAGE%\res\scripts\client\gui\mods\" ^
  >nul
set "OUTWOTMOD=%REPO%\build\%MODNAME%.wotmod"
if not exist "%REPO%\build" mkdir "%REPO%\build"

REM ZIP ohne Kompression via .NET (kein externe Tool noetig).
powershell -NoProfile -Command ^
  "Add-Type -AssemblyName System.IO.Compression.FileSystem; ^
   [System.IO.Compression.ZipFile]::CreateFromDirectory('%STAGE%', '%OUTWOTMOD%', [System.IO.Compression.CompressionLevel]::NoCompression, $false)"
if errorlevel 1 (
  echo [FEHLER] .wotmod konnte nicht gepackt werden.
  exit /b 1
)
echo  %OUTWOTMOD%

echo.
echo == 3/5 - In WoT-Mods abhaengen ==
set "MODSDIR=%WOTPATH%\mods\%MODSVER%"
if not exist "%MODSDIR%" (
  echo  Modsdordner nicht gefunden: %MODSDIR%
  echo  Lege Ordner an...
  mkdir "%MODSDIR%"
)
copy /y "%OUTWOTMOD%" "%MODSDIR%\" ^
  >nul && echo  nach "%MODSDIR%"

if exist "%CUSTOMMODSDIR%" (
  copy /y "%OUTWOTMOD%" "%CUSTOMMODSDIR%\" ^
    >nul && echo  fuer Aslain nach "%CUSTOMMODSDIR%"
)

echo.
echo == 4/5 - Alten (SWF) Build nicht ueberschrieben ==
echo  (build\\%MODNAME%.wotmod ist der neue Python-Build.)

echo.
echo ==============================
echo FERTIG. Starte WoT und pruefe python.log:
echo   [AltMinimapVehiclenames] Registriert ...
echo   Beim Kampfstart: [AltMinimapVehiclenames] Patch aktiv ...
echo ==============================
endlocal
