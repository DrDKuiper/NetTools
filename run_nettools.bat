@echo off
echo ========================================
echo          NETTOOLS - EXECUCAO
echo ========================================
echo.

REM Verifica se o Python está disponível
C:/Users/Kuiper/Documents/GitHub/NetTools/.venv/Scripts/python.exe --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Erro: Python nao encontrado no ambiente virtual
    echo Tente executar: python main.py
    pause
    exit /b 1
)

echo Iniciando NetTools...
echo.
echo Nota: O warning "Could not find platform independent libraries"
echo pode aparecer mas nao afeta o funcionamento da aplicacao.
echo.

REM Executa o NetTools
C:/Users/Kuiper/Documents/GitHub/NetTools/.venv/Scripts/python.exe main.py

pause
