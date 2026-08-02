@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "RUNTIME_DIR=%CD%\.venv_sylvapapers"
set "PYTHON_EXE=%RUNTIME_DIR%\Scripts\python.exe"
set "FACTORY_CONFIG=%CD%\configs\factory.yaml"
set "EDITOR_URL=http://127.0.0.1:8766/"
set "UV_EXE="
set "UV_PROJECT_ENVIRONMENT=%RUNTIME_DIR%"
set "PYTHONNOUSERSITE=1"
set "PYTHONPATH="
set "PYTHONHOME="

if exist "%PYTHON_EXE%" (
  "%PYTHON_EXE%" -c "import sys, yaml; from importlib.metadata import version; from pydantic import BaseModel; import matplotlib, networkx, simpy, sylvapapers_contracts, sylvapapers_digital_twin; assert callable(yaml.safe_load); raise SystemExit(0 if sys.version_info >= (3, 12) and version('sylvapapers-digital-twin') == '0.3.0' else 1)" >nul 2>&1
  if not errorlevel 1 goto validate
)

for /f "delims=" %%U in ('where uv.exe 2^>nul') do if not defined UV_EXE set "UV_EXE=%%U"
if not defined UV_EXE if exist "%USERPROFILE%\.local\bin\uv.exe" set "UV_EXE=%USERPROFILE%\.local\bin\uv.exe"
if not defined UV_EXE goto missing_uv

echo Installation ou mise a jour de l'environnement SylvaPapers...
if exist "%RUNTIME_DIR%" (
  "%UV_EXE%" sync --frozen --extra dev --reinstall
) else (
  "%UV_EXE%" sync --frozen --extra dev
)
if errorlevel 1 goto install_failed
if not exist "%PYTHON_EXE%" goto install_failed

"%PYTHON_EXE%" -c "import yaml; from pydantic import BaseModel; import sylvapapers_contracts, sylvapapers_digital_twin; assert callable(yaml.safe_load)" >nul 2>&1
if errorlevel 1 goto install_failed

:validate
"%PYTHON_EXE%" -m sylvapapers_digital_twin validate-config --config "%CD%\configs\scenarios\baseline.yaml" >nul
if errorlevel 1 goto invalid_config

start "" /b powershell.exe -NoLogo -NoProfile -WindowStyle Hidden -Command ^
  "$u=$env:EDITOR_URL; for($i=0; $i -lt 80; $i++){ try { $j=Invoke-RestMethod -Uri ($u + 'factory.json') -TimeoutSec 1; if($j.factory_id -eq 'sylvapapers-demo'){ Start-Process $u; exit 0 } } catch {}; Start-Sleep -Milliseconds 250 }; exit 1"

echo.
echo SylvaPapers demarre sur %EDITOR_URL%
echo Fermez cette fenetre ou appuyez sur Ctrl+C pour arreter le serveur.
echo.

"%PYTHON_EXE%" -m sylvapapers_digital_twin factory-editor --factory "%FACTORY_CONFIG%" --host 127.0.0.1 --port 8766
set "EXIT_CODE=%ERRORLEVEL%"
if not "%EXIT_CODE%"=="0" pause
exit /b %EXIT_CODE%

:missing_uv
echo.
echo L'environnement Python est absent ou invalide et uv.exe est introuvable.
echo Installez uv puis relancez ce fichier :
echo https://docs.astral.sh/uv/getting-started/installation/
pause
exit /b 1

:install_failed
echo.
echo Echec de la creation de l'environnement depuis uv.lock.
echo Fermez les programmes Python qui utilisent ce dossier, puis relancez ce fichier.
pause
exit /b 1

:invalid_config
echo.
echo La configuration SylvaPapers est invalide. Le serveur n'a pas ete lance.
pause
exit /b 1
