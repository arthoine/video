@echo off
REM Script de vérification complète GPU pour Windows
REM Teste que CHAQUE étape utilise la RTX 4070 Ti

echo ========================================
echo Verification GPU - StreamHighlightAI
echo ========================================
echo.

REM Activer l'environnement virtuel si existe
if exist venv\Scripts\activate.bat (
    echo Activation environnement virtuel...
    call venv\Scripts\activate.bat
    echo.
)

REM Lancer le script de vérification
python verify_gpu_usage.py

echo.
echo ========================================
echo.
echo Appuyez sur une touche pour fermer...
pause >nul
