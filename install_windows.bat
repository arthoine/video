@echo off
REM ========================================
REM StreamHighlightAI - Installation Windows
REM Script d'installation automatique
REM ========================================

echo.
echo ========================================
echo  StreamHighlightAI - Installation
echo ========================================
echo.

REM Vérifier Python
echo Verification de Python...
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [X] Python n'est pas installe ou pas dans le PATH
    echo.
    echo Veuillez installer Python 3.8+ depuis:
    echo   - Microsoft Store (rechercher "Python 3.11")
    echo   - Ou python.org/downloads
    echo.
    echo IMPORTANT: Cocher "Add Python to PATH" lors de l'installation
    echo.
    pause
    exit /b 1
)
echo [OK] Python detecte
python --version

REM Vérifier FFmpeg
echo.
echo Verification de FFmpeg...
ffmpeg -version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [X] FFmpeg n'est pas installe ou pas dans le PATH
    echo.
    echo Installation FFmpeg:
    echo   1. Avec Winget (Windows 11): winget install ffmpeg
    echo   2. Avec Chocolatey: choco install ffmpeg
    echo   3. Manuel: Voir WINDOWS.md section "Installation FFmpeg"
    echo.
    echo Appuyez sur une touche pour continuer quand meme...
    pause
) else (
    echo [OK] FFmpeg detecte
)

REM Créer l'environnement virtuel
echo.
echo ========================================
echo Creation de l'environnement virtuel...
echo ========================================
echo.

if exist "venv\" (
    echo Un environnement virtuel existe deja.
    echo Voulez-vous le recreer ? (O/N)
    set /p RECREATE="Choix: "
    if /i "%RECREATE%"=="O" (
        echo Suppression de l'ancien environnement...
        rmdir /s /q venv
    ) else (
        goto :activate_env
    )
)

python -m venv venv

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERREUR lors de la creation de l'environnement virtuel
    pause
    exit /b 1
)

echo [OK] Environnement virtuel cree

:activate_env
REM Activer l'environnement
echo.
echo Activation de l'environnement virtuel...
call venv\Scripts\activate.bat

REM Mettre à jour pip
echo.
echo Mise a jour de pip...
python -m pip install --upgrade pip

REM Installer les dépendances
echo.
echo ========================================
echo Installation des dependances Python...
echo ========================================
echo.
echo Cela peut prendre 5-10 minutes...
echo.

pip install -r requirements.txt

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERREUR lors de l'installation des dependances
    pause
    exit /b 1
)

echo.
echo [OK] Dependances installees

REM Vérifier si GPU NVIDIA disponible
echo.
echo ========================================
echo Detection GPU...
echo ========================================
echo.

python -c "import torch; print('CUDA disponible:', torch.cuda.is_available())" 2>nul

echo.
echo Voulez-vous installer le support GPU NVIDIA ? (O/N)
echo (Seulement si vous avez une carte graphique NVIDIA)
set /p GPU="Choix: "

if /i "%GPU%"=="O" (
    echo.
    echo Installation PyTorch avec support CUDA...
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

    if %ERRORLEVEL% EQU 0 (
        echo [OK] Support GPU installe
        python -c "import torch; print('CUDA disponible:', torch.cuda.is_available())"
    ) else (
        echo [X] Erreur lors de l'installation du support GPU
        echo Le programme fonctionnera quand meme (sur CPU)
    )
)

REM Créer le dossier tests
echo.
echo Creation des dossiers...
if not exist "tests\" mkdir tests

REM Test final
echo.
echo ========================================
echo Test de l'installation...
echo ========================================
echo.

python main.py --help >nul 2>&1

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo  INSTALLATION REUSSIE !
    echo ========================================
    echo.
    echo StreamHighlightAI est pret a l'emploi.
    echo.
    echo Prochaines etapes:
    echo.
    echo 1. Test rapide:
    echo    Double-cliquer sur: test_rapide.bat
    echo.
    echo 2. Traiter votre premiere video Arc Raiders:
    echo    Double-cliquer sur: run_arc_raiders.bat
    echo.
    echo 3. Ligne de commande manuelle:
    echo    venv\Scripts\activate.bat
    echo    python main.py -i "votre_video.mp4" -c examples\config_arc_raiders.yaml
    echo.
    echo Documentation complete: WINDOWS.md
    echo.
) else (
    echo.
    echo ========================================
    echo  ERREUR LORS DU TEST
    echo ========================================
    echo.
    echo L'installation semble incomplete.
    echo Consultez WINDOWS.md pour le depannage.
)

echo.
pause
