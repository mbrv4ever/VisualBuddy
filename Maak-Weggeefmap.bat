@echo off
rem Maak-Weggeefmap.bat - een schone map om Drave Visual Buddy weg te geven.
rem ZONDER jouw eigen gegevens: geen browserdata (inloggen!), geen instellingen, geen logboek, geen cache.
cd /d "%~dp0"
if not exist "dist\DraveVisualBuddy\DraveVisualBuddy.exe" ( echo Eerst bouwen: Build-DraveVisualBuddy-EXE.bat & pause & exit /b 1 )
if exist "weggeven\DraveVisualBuddy" rmdir /s /q "weggeven\DraveVisualBuddy"
mkdir "weggeven\DraveVisualBuddy"
robocopy "dist\DraveVisualBuddy" "weggeven\DraveVisualBuddy" /E /NFL /NDL /NJH /NJS /XD browserdata cache _bewaar paspoorten /XF buddy_instellingen.json instellingen.txt handen_logboek.txt handen_terug.json *.log >nul
if errorlevel 8 ( echo KOPIEREN MISLUKT & pause & exit /b 1 )
if exist "Lees_mij_eerst.pdf" copy /y "Lees_mij_eerst.pdf" "weggeven\DraveVisualBuddy\" >nul
copy /y "DraveVisualBuddy_snelgids.pdf" "weggeven\DraveVisualBuddy\" >nul
if exist "DraveVisualBuddy_uitleg.mp4" copy /y "DraveVisualBuddy_uitleg.mp4" "weggeven\DraveVisualBuddy\" >nul
if exist "weggeven\DraveVisualBuddy\browserdata" ( echo FOUT: browserdata in de weggeefmap & pause & exit /b 1 )
if not exist "weggeven\DraveVisualBuddy\DraveVisualBuddy.exe" ( echo GEEN EXE IN DE WEGGEEFMAP & pause & exit /b 1 )
echo KLAAR: weggeven\DraveVisualBuddy
