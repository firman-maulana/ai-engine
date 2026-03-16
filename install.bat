@echo off
echo ========================================
echo AI Engine Installation Script
echo ========================================
echo.

echo Step 1: Upgrading pip...
python -m pip install --upgrade pip
echo.

echo Step 2: Installing dependencies...
echo Trying requirements.txt first...
pip install -r requirements.txt

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ========================================
    echo Error with requirements.txt
    echo Trying simplified installation...
    echo ========================================
    echo.
    
    pip install fastapi
    pip install "uvicorn[standard]"
    pip install openai
    pip install python-dotenv
    
    if %ERRORLEVEL% NEQ 0 (
        echo.
        echo ========================================
        echo Installation failed!
        echo Please see TROUBLESHOOTING_INSTALL.md
        echo ========================================
        pause
        exit /b 1
    )
)

echo.
echo ========================================
echo Testing installation...
echo ========================================
python -c "import fastapi; import openai; print('✅ All packages installed successfully!')"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo ✅ Installation Complete!
    echo ========================================
    echo.
    echo Next steps:
    echo 1. Edit .env file and add your OpenAI API key
    echo 2. Run: python -m uvicorn main:app --reload --port 9000
    echo.
) else (
    echo.
    echo ========================================
    echo ❌ Installation verification failed
    echo Please see TROUBLESHOOTING_INSTALL.md
    echo ========================================
)

pause
