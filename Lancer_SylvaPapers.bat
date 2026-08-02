@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "PYTHON_EXE=%CD%\.venv\Scripts\python.exe"
set "FACTORY_CONFIG=%CD%\configs\factory.yaml"
set "EDITOR_URL=http://127.0.0.1:8766/"
set "UV_EXE="

if exist "%PYTHON_EXE%" (
  "%PYTHON_EXE%" -c "import sys; from importlib.metadata import version; import sylvapapers_contracts, sylvapapers_digital_twin; raise SystemExit(0 if sys.version_info >= (3, 12) and version('sylvapapers-digital-twin') == '0.2.0' else 1)" >nul 2>&1
  if not errorlevel 1 goto validate
)

for /f "delims=" %%U in ('where uv.exe 2^>nul') do if not defined UV_EXE set "UV_EXE=%%U"
if not defined UV_EXE if exist "%USERPROFILE%\.local\bin\uv.exe" set "UV_EXE=%USERPROFILE%\.local\bin\uv.exe"
if not defined UV_EXE goto missing_uv

echo Installation ou mise a jour de l'environnement SylvaPapers...
"%UV_EXE%" sync --frozen --extra dev
if errorlevel 1 goto install_failed
if not exist "%PYTHON_EXE%" goto install_failed

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
