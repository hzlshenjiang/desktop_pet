@echo off
chcp 65001 >nul 2>&1

echo ========================================
echo   Desktop Pet Build Script
echo ========================================
echo.

echo [1/3] Installing dependencies...
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo [2/3] Building executable...
pyinstaller desktop_pet.spec --clean --noconfirm
if %errorlevel% neq 0 (
    echo [ERROR] Build failed
    pause
    exit /b 1
)

echo.
echo [3/3] Done!
echo.
echo ========================================
echo   Build complete!
echo   EXE: dist\desktop_pet.exe
echo ========================================
pause
