@echo off
setlocal EnableDelayedExpansion
chcp 437 >nul
title OMEGA :: Setup Wizard
color 0B

cls
echo.
echo.
echo    ___  __  __ ___  ____    __
echo   / _ \^|  \/  ^| __^|^|  __^|  / /\
echo  ^| ^| ^| ^| ^|\/^| ^| _^| ^| ^|_   / /--\
echo  ^| ^|_^| ^| ^|  ^| ^| ^|__^| ^|__ / /----\
echo   \___/^|_^|  ^|_^|____^|____^|/_/
echo.
echo   ================================================
echo              S E T U P   W I Z A R D
echo   ================================================
echo.

timeout /t 1 /nobreak >nul

:: Admin check
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo.
    echo   +------------------------------------------+
    echo   ^|  [!]  ADMINISTRATOR REQUIRED             ^|
    echo   ^|                                          ^|
    echo   ^|  Right-click setup.bat and choose:       ^|
    echo   ^|  "Run as administrator"                  ^|
    echo   +------------------------------------------+
    echo.
    pause
    exit /b 1
)

set "PROJECT_DIR=%~dp0"
if "%PROJECT_DIR:~-1%"=="\" set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"

echo   [*] Project directory ........ %PROJECT_DIR%
echo.

if not exist "%PROJECT_DIR%\omega.py" (
    echo.
    echo   +------------------------------------------+
    echo   ^|  [!]  omega.py NOT FOUND                 ^|
    echo   ^|                                          ^|
    echo   ^|  Place setup.bat in the same folder      ^|
    echo   ^|  as omega.py and try again.              ^|
    echo   +------------------------------------------+
    echo.
    pause
    exit /b 1
)

echo   [+] omega.py ................. found
echo.

echo   ================================================
echo                   PYTHON RUNTIME
echo   ================================================
echo.
echo   [*] Searching for Python installation...

set "PYTHON_EXE="
for /f "tokens=*" %%P in ('python -c "import sys; print(sys.executable)" 2^>nul') do set "PYTHON_EXE=%%P"

if "!PYTHON_EXE!"=="" (
    echo   [!] Python not found. Attempting install via winget...
    echo.
    winget install --id Python.Python.3.12 --source winget --accept-package-agreements --accept-source-agreements
    if %errorLevel% neq 0 (
        echo.
        echo   [!] Automatic install failed.
        echo       Please install Python manually:
        echo       https://www.python.org/downloads/
        echo.
        pause
        exit /b 1
    )
    for /f "tokens=*" %%P in ('python -c "import sys; print(sys.executable)" 2^>nul') do set "PYTHON_EXE=%%P"
)

echo   [+] Python ................... !PYTHON_EXE!
echo.

echo   ================================================
echo                    DEPENDENCIES
echo   ================================================
echo.

for %%P in (PyQt5 PyOpenGL numpy psutil requests) do (
    python -c "import %%P" >nul 2>&1
    if !errorLevel! neq 0 (
        echo   [~] Installing %%P ...
        python -m pip install %%P --quiet
        if !errorLevel! neq 0 (
            echo   [!] Failed to install %%P
        ) else (
            echo   [+] %%P installed successfully.
        )
    ) else (
        echo   [+] %%P .................. already satisfied
    )
)

echo.

echo   ================================================
echo                   GLOBAL COMMAND
echo   ================================================
echo.
echo   [*] Registering stomega command...

(
    echo @echo off
    echo "!PYTHON_EXE!" "%PROJECT_DIR%\omega.py"
) > "C:\Windows\System32\stomega.bat"

if exist "C:\Windows\System32\stomega.bat" (
    echo   [+] stomega .................. registered in System32
) else (
    echo   [!] Failed to register command.
    echo       Make sure you are running as Administrator.
    echo.
    pause
    exit /b 1
)

echo.
echo.
echo   +------------------------------------------+
echo   ^|                                          ^|
echo   ^|      SETUP COMPLETED SUCCESSFULLY        ^|
echo   ^|                                          ^|
echo   +==========================================+
echo   ^|                                          ^|
echo   ^|  Open any terminal and type:             ^|
echo   ^|                                          ^|
echo   ^|          stomega                         ^|
echo   ^|                                          ^|
echo   +==========================================+
echo   ^|                                          ^|
echo   ^|  In-game keybinds:                       ^|
echo   ^|    P        Toggle ESP on / off          ^|
echo   ^|    INSERT   Close the overlay            ^|
echo   ^|                                          ^|
echo   +------------------------------------------+
echo.
pause
endlocal