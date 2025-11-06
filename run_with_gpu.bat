@echo off
REM Script pour lancer StreamHighlightAI avec GPU NVIDIA
REM Pour RTX 4070 Ti et autres GPUs NVIDIA

echo ========================================
echo StreamHighlightAI - Mode GPU NVIDIA
echo ========================================
echo.

REM Activer l'environnement virtuel
if not exist venv\Scripts\activate.bat (
    echo ERREUR: Environnement virtuel non trouve
    echo Lancez d'abord: python -m venv venv
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

REM Vérification GPU rapide
echo Verification GPU...
python -c "import torch; print('GPU detecte:' if torch.cuda.is_available() else 'GPU NON detecte - utilisera CPU'); print('  Nom:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A')" 2>nul
if errorlevel 1 (
    echo.
    echo ATTENTION: PyTorch non installe ou probleme
    echo Le traitement utilisera le CPU ^(plus lent^)
    echo.
)

echo.
echo ========================================
echo Configuration
echo ========================================
echo.

REM Demander le fichier d'entrée
set /p INPUT="Chemin de la video source: "

REM Vérifier que le fichier existe
if not exist "%INPUT%" (
    echo.
    echo ERREUR: Fichier non trouve: %INPUT%
    echo.
    pause
    exit /b 1
)

REM Demander le fichier de sortie (optionnel)
set /p OUTPUT="Nom de sortie [highlights.mp4]: "
if "%OUTPUT%"=="" set OUTPUT=highlights.mp4

echo.
echo ========================================
echo Traitement
echo ========================================
echo.
echo Fichier entree: %INPUT%
echo Fichier sortie: %OUTPUT%
echo Config: config_gpu_nvidia.yaml
echo.
echo Demarrage...
echo.

REM Lancer le traitement avec config GPU
python main.py -i "%INPUT%" -o "%OUTPUT%" -c config_gpu_nvidia.yaml

echo.
echo ========================================
echo Termine!
echo ========================================
echo.

if exist "%OUTPUT%" (
    echo Video creee: %OUTPUT%
    echo.
    echo Voulez-vous ouvrir la video? ^(O/N^)
    set /p OPEN="> "
    if /i "%OPEN%"=="O" start "" "%OUTPUT%"
) else (
    echo ERREUR: La video n'a pas ete creee
    echo Verifiez les messages d'erreur ci-dessus
)

echo.
pause
