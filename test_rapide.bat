@echo off
REM ========================================
REM StreamHighlightAI - Test Rapide
REM Génère et teste avec une petite vidéo
REM ========================================

echo.
echo ========================================
echo  StreamHighlightAI - Test Rapide
echo ========================================
echo.

REM Vérifier si l'environnement virtuel existe
if not exist "venv\Scripts\activate.bat" (
    echo ERREUR: Environnement virtuel non trouve
    echo.
    echo Veuillez d'abord installer le projet:
    echo   python -m venv venv
    echo   venv\Scripts\activate.bat
    echo   pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

REM Activer l'environnement virtuel
call venv\Scripts\activate.bat

echo Ce script va:
echo 1. Generer une petite video de test (2 minutes)
echo 2. L'analyser avec la config rapide
echo 3. Creer un fichier highlights.mp4
echo.
echo Temps estime: 3-5 minutes
echo.
pause

echo.
echo ========================================
echo Etape 1/2: Generation video de test
echo ========================================
echo.

python tests\generate_test_video.py -d 2

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERREUR lors de la generation de la video de test
    pause
    exit /b 1
)

echo.
echo ========================================
echo Etape 2/2: Analyse de la video
echo ========================================
echo.

python main.py -i tests\test_video.mp4 -c examples\config_fast_preview.yaml -o test_highlights.mp4

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo  TEST TERMINE AVEC SUCCES !
    echo ========================================
    echo.
    echo Videos creees:
    echo - tests\test_video.mp4 (video de test)
    echo - test_highlights.mp4 (video analysee)
    echo.
    echo Ouvrir le resultat maintenant ? (O/N)
    set /p OPEN="Choix: "
    if /i "%OPEN%"=="O" (
        start test_highlights.mp4
    )
) else (
    echo.
    echo ========================================
    echo  ERREUR LORS DU TEST
    echo ========================================
    echo.
    echo Verifiez:
    echo - FFmpeg est installe
    echo - Python fonctionne correctement
    echo - Les dependances sont installees
)

echo.
pause
