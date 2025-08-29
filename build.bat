@echo off
echo Building NetTools executable...

REM Clean previous builds
echo Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Create executable
echo Creating executable with PyInstaller...
pyinstaller NetTools.spec

REM Check if build was successful
if exist "dist\NetTools.exe" (
    echo Build successful! Executable created at dist\NetTools.exe
    for %%I in ("dist\NetTools.exe") do echo File size: %%~zI bytes
) else (
    echo Build failed!
    exit /b 1
)

echo Build complete!
pause
