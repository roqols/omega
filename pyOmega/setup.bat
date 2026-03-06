@echo off
setlocal EnableDelayedExpansion
chcp 437 >nul
title OMEGA :: Setup Wizard
color 0B

fsutil dirty query %systemdrive% >nul 2>&1
if %errorLevel% neq 0 (
    echo.
    echo   [!] ADMINISTRATOR REQUIRED
    pause
    exit /b 1
)

set "PROJECT_DIR=%~dp0"
if "%PROJECT_DIR:~-1%"=="\" set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"

echo   [*] Checking Python...
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo   [!] Python not found. Installing...
    winget install --id Python.Python.3.12 -e --source winget
    echo   [!] Python installed. PLEASE RESTART THIS SETUP.
    pause
    exit
)

set "DEPS=PyQt5 PyOpenGL PyOpenGL_accelerate numpy psutil requests"

echo   [*] Updating PIP...
python -m pip install --upgrade pip --quiet

echo   [*] Installing Dependencies...
for %%P in (%DEPS%) do (
    echo   [~] Checking %%P...
    python -m pip install %%P --quiet
)

echo   [*] Registering stomega command...
(
    echo @echo off
    echo python "%PROJECT_DIR%\omega.py" %%*
) > "C:\Windows\stomega.bat"

copy /y "C:\Windows\stomega.bat" "C:\Windows\System32\stomega.bat" >nul 2>&1

echo.
echo   ==========================================
echo      SETUP COMPLETED SUCCESSFULLY
echo   ==========================================
echo.
echo   Type 'stomega' in any terminal to start.
pause
