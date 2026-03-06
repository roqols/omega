@echo off
setlocal EnableDelayedExpansion
title OMEGA -- Uninstall
color 0B

echo.
echo =====================================
echo        OMEGA -- Uninstall Wizard
echo =====================================
echo.

:: Verify administrator privileges using fsutil
fsutil dirty query %systemdrive% >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] ERROR: Administrator privileges required!
    echo     Right-click uninstall.bat and select:
    echo     "Run as administrator"
    echo.
    pause
    exit /b 1
)

echo [*] Starting system cleanup...

:: 1. Remove from System32
if exist "C:\Windows\System32\stomega.bat" (
    del /f /q "C:\Windows\System32\stomega.bat"
    echo [+] 'stomega' command removed from System32.
)

:: 2. Remove from Windows directory (modern setup path)
if exist "C:\Windows\stomega.bat" (
    del /f /q "C:\Windows\stomega.bat"
    echo [+] 'stomega' command removed from C:\Windows.
)

:: 3. Remove from SysWOW64 (legacy versions)
if exist "C:\Windows\SysWOW64\stomega.bat" (
    del /f /q "C:\Windows\SysWOW64\stomega.bat"
    echo [+] 'stomega' command removed from SysWOW64.
)

:: 4. Remove legacy folders
if exist "C:\omega-launcher" (
    rd /s /q "C:\omega-launcher"
    echo [+] Legacy folder C:\omega-launcher deleted.
)

echo.
echo =====================================
echo    [OK] UNINSTALL COMPLETED!
echo =====================================
echo.
echo The .py and .bat files in this folder 
echo were NOT deleted. Only the global 
echo command was removed from the system.
echo.
pause
endlocal
