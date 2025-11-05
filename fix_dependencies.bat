@echo off
REM ========================================
REM StreamHighlightAI - Fix Dependencies
REM Répare les problèmes courants d'installation
REM ========================================

echo.
echo ========================================
echo  Reparation des dependances
echo ========================================
echo.

REM Vérifier si l'environnement virtuel existe
if not exist "venv\Scripts\activate.bat" (
    echo ERREUR: Environnement virtuel non trouve
    echo.
    echo Lancez d'abord: install_windows.bat
    echo.
    pause
    exit /b 1
)

REM Activer l'environnement virtuel
call venv\Scripts\activate.bat

echo Ce script va reparer les problemes courants:
echo - MoviePy et ses dependances
echo - Numpy/Scipy incompatibilites
echo - OpenCV
echo.
pause

echo.
echo ========================================
echo Reparation de MoviePy...
echo ========================================
echo.

pip uninstall -y moviepy decorator proglog pillow
pip install decorator>=4.4.2
pip install proglog>=0.1.10
pip install pillow>=9.0.0
pip install moviepy>=1.0.3

echo.
echo ========================================
echo Verification...
echo ========================================
echo.

python -c "from moviepy.editor import VideoFileClip; print('[OK] MoviePy fonctionne')"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo  REPARATION REUSSIE !
    echo ========================================
    echo.
    echo Vous pouvez maintenant utiliser StreamHighlightAI
) else (
    echo.
    echo ========================================
    echo  PROBLEME PERSISTANT
    echo ========================================
    echo.
    echo Essayez:
    echo 1. Reinstaller completement:
    echo    - Supprimez le dossier venv
    echo    - Relancez install_windows.bat
    echo.
    echo 2. Consultez WINDOWS.md section Depannage
)

echo.
pause
