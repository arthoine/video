@echo off
REM ========================================
REM StreamHighlightAI - Convertir Audio
REM Convertit l'audio pour compatibilité
REM ========================================

echo.
echo ========================================
echo  Conversion Audio pour StreamHighlightAI
echo ========================================
echo.

REM Demander le fichier d'entrée
echo Entrez le chemin COMPLET de votre video (avec guillemets):
echo Exemple: "J:\cliptwitch.mp4"
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

REM Extraire le nom et créer le nom de sortie
for %%F in (%INPUT%) do (
    set BASENAME=%%~nF
    set DIRNAME=%%~dpF
)

set OUTPUT="%DIRNAME%%BASENAME%_fixed.mp4"

echo.
echo ========================================
echo Fichier d'entree: %INPUT%
echo Fichier de sortie: %OUTPUT%
echo ========================================
echo.
echo Cette operation va:
echo - Copier la video telle quelle (rapide)
echo - Reconvertir l'audio en AAC compatible
echo.
echo Temps estime: 5-10 minutes pour 60 min de video
echo.
pause

echo.
echo Conversion en cours...
echo.

ffmpeg -i %INPUT% -c:v copy -c:a aac -b:a 192k -ar 48000 -y %OUTPUT%

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo  CONVERSION REUSSIE !
    echo ========================================
    echo.
    echo Fichier cree: %OUTPUT%
    echo.
    echo Vous pouvez maintenant utiliser ce fichier avec StreamHighlightAI:
    echo python main.py -i %OUTPUT% -c examples\config_arc_raiders.yaml --gpu
    echo.
) else (
    echo.
    echo ========================================
    echo  ERREUR LORS DE LA CONVERSION
    echo ========================================
    echo.
    echo Verifiez:
    echo - FFmpeg est installe
    echo - Le fichier d'entree n'est pas corrompu
    echo - Vous avez assez d'espace disque
)

echo.
pause
