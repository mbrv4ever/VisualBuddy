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
%PY% main.py
