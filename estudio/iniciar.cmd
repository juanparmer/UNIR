@echo off
cd /d "%~dp0"
where py >nul 2>nul
if not errorlevel 1 (
  py -3 app.py
  pause
  exit /b
)
where python >nul 2>nul
if not errorlevel 1 (
  python app.py
  pause
  exit /b
)
if exist "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" (
  "%USERPROFILE%\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" app.py
  pause
  exit /b
)
echo Instala Python 3.11 o posterior y vuelve a abrir este archivo.
pause
