@echo off
setlocal EnableDelayedExpansion
title OMEGA -- Uninstall
color 0C

echo.
echo  =====================================
echo       OMEGA -- Desinstalacao
echo  =====================================
echo.

:: Verificar admin
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo  [!] Execute como Administrador!
    echo      Clique com botao direito em uninstall.bat
    echo      e escolha "Executar como administrador".
    pause
    exit /b 1
)

:: Remover stomega do System32
echo  [*] Removendo comando stomega...
if exist "C:\Windows\System32\stomega.bat" (
    del /f /q "C:\Windows\System32\stomega.bat"
    echo  [+] stomega removido com sucesso.
) else (
    echo  [~] stomega nao encontrado. Nada a remover.
)

:: Limpar instalacoes antigas de versoes anteriores
if exist "C:\Windows\SysWOW64\stomega.bat" (
    del /f /q "C:\Windows\SysWOW64\stomega.bat"
    echo  [+] Versao antiga removida de SysWOW64.
)
if exist "C:\omega-launcher" (
    rd /s /q "C:\omega-launcher"
    echo  [+] Pasta legada C:\omega-launcher removida.
)

echo.
echo  =====================================
echo   [OK] Desinstalacao concluida!
echo  =====================================
echo.
echo   Os arquivos do projeto NAO foram alterados.
echo.
pause
endlocal