@echo off
REM ========================================
REM StreamHighlightAI - Arc Raiders
REM Script de lancement rapide pour Windows
REM ========================================

echo.
echo ========================================
echo  StreamHighlightAI - Arc Raiders
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

REM Demander le fichier d'entrée
echo Entrez le chemin COMPLET de votre video (avec guillemets si espaces):
echo Exemple: "C:\Videos\arc_raiders_stream.mp4"
echo.
set /p INPUT="Chemin video: "

REM Vérifier si le fichier existe
if not exist %INPUT% (
    echo.
    echo ERREUR: Fichier non trouve: %INPUT%
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo Configuration: Arc Raiders optimisee
echo GPU: Active (si disponible)
echo Duree cible: 18 minutes
echo ========================================
echo.
echo Traitement en cours...
echo.

REM Lancer le traitement
python main.py -i %INPUT% -c examples\config_arc_raiders.yaml --gpu -o highlights_arc_raiders.mp4

REM Vérifier si la création a réussi
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo  TRAITEMENT TERMINE AVEC SUCCES !
    echo ========================================
    echo.
    echo Video creee: highlights_arc_raiders.mp4
    echo.
    echo Ouvrir la video maintenant ? (O/N)
    set /p OPEN="Choix: "
    if /i "%OPEN%"=="O" (
        start highlights_arc_raiders.mp4
    )
) else (
    echo.
    echo ========================================
    echo  ERREUR LORS DU TRAITEMENT
    echo ========================================
    echo.
    echo Verifiez les messages d'erreur ci-dessus
)

echo.
pause
