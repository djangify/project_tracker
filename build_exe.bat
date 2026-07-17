@echo off
title Project Tracker - Build Desktop App
color 0B

echo.
echo  =============================================
echo   Building ProjectTracker.exe (desktop app)
echo  =============================================
echo.

:: -----------------------------------------------
:: VIRTUAL ENVIRONMENT
:: -----------------------------------------------
if not exist "trackervenv\Scripts\activate.bat" (
    echo  Creating virtual environment...
    python -m venv trackervenv
)
call trackervenv\Scripts\activate.bat

:: -----------------------------------------------
:: DEPENDENCIES (app + build tools)
:: -----------------------------------------------
echo  Installing dependencies...
pip install -r requirements.txt --quiet --disable-pip-version-check
pip install pyinstaller --quiet --disable-pip-version-check
if errorlevel 1 (
    color 0C
    echo  ERROR: Failed to install dependencies.
    pause
    exit /b 1
)

:: -----------------------------------------------
:: COLLECT STATIC FILES (bundled into the build)
:: -----------------------------------------------
echo  Collecting static files...
python manage.py collectstatic --noinput >nul 2>&1

:: -----------------------------------------------
:: BUILD
:: -----------------------------------------------
echo  Running PyInstaller...
pyinstaller project_tracker.spec --noconfirm
if errorlevel 1 (
    color 0C
    echo  ERROR: Build failed. Re-run after setting console=True in project_tracker.spec
    echo  to see the underlying error.
    pause
    exit /b 1
)

echo.
echo  =============================================
echo   Done. Your app is in:  dist\ProjectTracker\ProjectTracker.exe
echo   Ship the whole dist\ProjectTracker folder (zip it up before sharing).
echo  =============================================
echo.
pause
