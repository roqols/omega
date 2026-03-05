@echo off
setlocal EnableDelayedExpansion
title OMEGA -- Setup
color 0A

echo.
echo  =====================================
echo       OMEGA -- Setup e Instalacao
echo  =====================================
echo.

:: Verificar admin
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo  [!] Execute como Administrador!
    echo      Clique com botao direito em setup.bat
    echo      e escolha "Executar como administrador".
    pause
    exit /b 1
)

:: Pasta do projeto = pasta onde este .bat esta
set "PROJECT_DIR=%~dp0"
if "%PROJECT_DIR:~-1%"=="\" set "PROJECT_DIR=%PROJECT_DIR:~0,-1%"
echo  [*] Pasta do projeto: %PROJECT_DIR%
echo.

:: Verificar omega.py
if not exist "%PROJECT_DIR%\omega.py" (
    echo  [!] omega.py nao encontrado em: %PROJECT_DIR%
    echo      Coloque setup.bat na mesma pasta que omega.py
    pause
    exit /b 1
)

:: Localizar python.exe
echo  [*] Localizando Python...
set "PYTHON_EXE="
for /f "tokens=*" %%P in ('python -c "import sys; print(sys.executable)" 2^>nul') do set "PYTHON_EXE=%%P"
if "!PYTHON_EXE!"=="" (
    echo  [!] Python nao encontrado. Instalando via winget...
    winget install --id Python.Python.3.12 --source winget --accept-package-agreements --accept-source-agreements
    if %errorLevel% neq 0 (
        echo  [!] Falha. Instale manualmente em: https://www.python.org/
        pause
        exit /b 1
    )
    for /f "tokens=*" %%P in ('python -c "import sys; print(sys.executable)" 2^>nul') do set "PYTHON_EXE=%%P"
)
echo  [+] !PYTHON_EXE!
echo.

:: Instalar dependencias (so instala o que falta)
echo  [*] Verificando dependencias...
for %%P in (PyQt5 PyOpenGL numpy psutil requests) do (
    python -c "import %%P" >nul 2>&1
    if !errorLevel! neq 0 (
        echo  [~] Instalando %%P...
        python -m pip install %%P --quiet
        if !errorLevel! neq 0 (
            echo  [!] Falha ao instalar %%P
        ) else (
            echo  [+] %%P instalado.
        )
    ) else (
        echo  [+] %%P ok.
    )
)
echo.

:: Criar stomega.bat no System32
echo  [*] Instalando comando stomega...
(
    echo @echo off
    echo "!PYTHON_EXE!" "%PROJECT_DIR%\omega.py"
) > "C:\Windows\System32\stomega.bat"

if exist "C:\Windows\System32\stomega.bat" (
    echo  [+] Comando stomega instalado com sucesso!
) else (
    echo  [!] Falha ao instalar stomega. Rode como Administrador.
    pause
    exit /b 1
)

echo.
echo  =====================================
echo   [OK] Setup concluido!
echo  =====================================
echo.
echo   Abra qualquer CMD e digite:
echo.
echo       stomega
echo.
echo   Teclas durante o jogo:
echo     P       = Ativar / Desativar ESP
echo     INSERT  = Fechar o overlay
echo.
pause
endlocal