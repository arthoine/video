@echo off
REM Script de vérification GPU pour Windows
REM Vérifie que le GPU NVIDIA est bien configuré

echo ========================================
echo StreamHighlightAI - Verification GPU
echo ========================================
echo.

REM Activer l'environnement virtuel si existe
if exist venv\Scripts\activate.bat (
    echo Activation environnement virtuel...
    call venv\Scripts\activate.bat
    echo.
)

REM Lancer le script de vérification
python check_gpu.py

echo.
echo ========================================
echo.
echo Appuyez sur une touche pour fermer...
pause >nul
