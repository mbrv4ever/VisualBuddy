@echo off
cd /d "%~dp0"
set PY=
for %%v in (3.10 3.11 3.12) do (
  if not defined PY ( py -%%v -c "import sys" >nul 2>&1 && set PY=py -%%v )
)
if not defined PY ( echo Geen Python 3.10-3.12 gevonden. & pause & exit /b 1 )
%PY% -c "import pygame" >nul 2>&1 || %PY% -m pip install pygame
%PY% -c "import uiautomation" >nul 2>&1 || %PY% -m pip install uiautomation
%PY% -c "import neuvoice, sounddevice" >nul 2>&1 || %PY% -m pip install "numpy<2" neuvoice sounddevice
%PY% -c "import PyQt6.QtWebEngineWidgets" >nul 2>&1 || %PY% -m pip install PyQt6 PyQt6-WebEngine
for %%f in (handen.py klusjes.py bescherm.py handen_qt.py) do if exist "..\DraveHanden\%%f" copy /y "..\DraveHanden\%%f" %%f >nul
%PY% -c "import send2trash" >nul 2>&1 || %PY% -m pip install send2trash
%PY% -c "import PyInstaller" >nul 2>&1 || %PY% -m pip install pyinstaller
%PY% make_icon.py
rem 0.7: jouw gegevens in dist eerst bewaren (inloggen, instellingen, logboek), na het bouwen terugzetten
if exist _bewaar rmdir /s /q _bewaar
mkdir _bewaar
if exist "dist\DraveVisualBuddy\browserdata" xcopy /e /i /y /q "dist\DraveVisualBuddy\browserdata" "_bewaar\browserdata" >nul
for %%f in (buddy_instellingen.json instellingen.txt handen_logboek.txt handen_terug.json) do if exist "dist\DraveVisualBuddy\%%f" copy /y "dist\DraveVisualBuddy\%%f" _bewaar\ >nul
%PY% -m PyInstaller --noconfirm --clean --windowed --onedir --name DraveVisualBuddy --icon assets\icon.ico --hidden-import lezer --hidden-import stem --hidden-import uitspraak --hidden-import browser --hidden-import handen --hidden-import klusjes --hidden-import bescherm --hidden-import handen_qt --hidden-import send2trash --collect-all PyQt6 --collect-all uiautomation --collect-all comtypes --collect-all neuvoice --collect-binaries onnxruntime --collect-all sounddevice main.py
if errorlevel 1 ( echo BOUWEN MISLUKT & pause & exit /b 1 )
if not exist "dist\DraveVisualBuddy\DraveVisualBuddy.exe" ( echo GEEN EXE GEVONDEN & pause & exit /b 1 )
xcopy /e /i /y assets "dist\DraveVisualBuddy\assets" >nul
if exist "_bewaar\browserdata" xcopy /e /i /y /q "_bewaar\browserdata" "dist\DraveVisualBuddy\browserdata" >nul
for %%f in (buddy_instellingen.json instellingen.txt handen_logboek.txt handen_terug.json) do if exist "_bewaar\%%f" copy /y "_bewaar\%%f" "dist\DraveVisualBuddy\" >nul
if exist DraveVisualBuddy_snelgids.pdf copy /y DraveVisualBuddy_snelgids.pdf "dist\DraveVisualBuddy\" >nul
echo KLAAR: dist\DraveVisualBuddy\DraveVisualBuddy.exe
