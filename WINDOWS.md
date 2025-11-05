# 🪟 StreamHighlightAI - Guide d'installation Windows

Guide complet pour installer et utiliser StreamHighlightAI sur Windows 10/11.

---

## 📋 Table des matières

1. [Prérequis](#prérequis)
2. [Installation Python](#1-installation-de-python)
3. [Installation FFmpeg](#2-installation-de-ffmpeg)
4. [Installation StreamHighlightAI](#3-installation-de-streamhighlightai)
5. [Utilisation](#4-utilisation)
6. [Scripts automatiques](#5-scripts-automatiques-bat)
7. [Dépannage Windows](#6-dépannage-windows)

---

## Prérequis

- **Windows 10 ou 11** (64-bit)
- **10 GB d'espace disque libre**
- **8 GB de RAM minimum** (16 GB recommandé)
- **Connexion Internet** (pour téléchargements)
- **GPU NVIDIA** (optionnel mais recommandé pour accélération)

---

## 1. Installation de Python

### Méthode 1: Microsoft Store (RECOMMANDÉ)

1. Ouvrir le **Microsoft Store**
2. Rechercher "Python 3.11"
3. Cliquer sur **Installer**
4. Attendre la fin de l'installation

### Méthode 2: Site officiel

1. Aller sur [python.org/downloads](https://www.python.org/downloads/)
2. Télécharger **Python 3.11.x** (version 64-bit)
3. Lancer l'installeur
4. ⚠️ **IMPORTANT**: Cocher "Add Python to PATH"
5. Cliquer sur "Install Now"

### Vérification

Ouvrir **PowerShell** ou **Invite de commandes** et taper:

```powershell
python --version
```

Vous devriez voir: `Python 3.11.x`

Si erreur "python n'est pas reconnu":
- Redémarrer l'ordinateur
- Ou ajouter Python au PATH manuellement (voir section Dépannage)

---

## 2. Installation de FFmpeg

FFmpeg est **OBLIGATOIRE** pour StreamHighlightAI. Trois méthodes possibles:

### Méthode 1: Winget (Windows 11 / Windows 10 22H2+)

Ouvrir **PowerShell** en tant qu'administrateur et taper:

```powershell
winget install ffmpeg
```

### Méthode 2: Chocolatey

1. Installer Chocolatey (si pas déjà fait):
   - Ouvrir **PowerShell** en tant qu'administrateur
   - Exécuter:
     ```powershell
     Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
     ```

2. Installer FFmpeg:
   ```powershell
   choco install ffmpeg
   ```

### Méthode 3: Installation manuelle (toutes versions Windows)

1. **Télécharger FFmpeg**:
   - Aller sur [ffmpeg.org/download.html](https://ffmpeg.org/download.html)
   - Cliquer sur "Windows builds from gyan.dev"
   - Télécharger **ffmpeg-release-essentials.zip**

2. **Extraire l'archive**:
   - Faire clic-droit > Extraire tout
   - Extraire dans `C:\ffmpeg`

3. **Ajouter FFmpeg au PATH**:
   - Appuyer sur `Windows + R`
   - Taper `sysdm.cpl` et appuyer sur Entrée
   - Aller dans l'onglet "Avancé"
   - Cliquer sur "Variables d'environnement"
   - Dans "Variables système", sélectionner "Path"
   - Cliquer sur "Modifier"
   - Cliquer sur "Nouveau"
   - Ajouter: `C:\ffmpeg\bin`
   - Cliquer sur OK partout
   - **Redémarrer l'ordinateur**

### Vérification FFmpeg

Ouvrir une **nouvelle** fenêtre PowerShell et taper:

```powershell
ffmpeg -version
```

Vous devriez voir la version de FFmpeg.

---

## 3. Installation de StreamHighlightAI

### Étape 1: Télécharger le projet

**Option A: Avec Git**
```powershell
git clone https://github.com/votre-username/StreamHighlightAI.git
cd StreamHighlightAI
```

**Option B: Sans Git (téléchargement ZIP)**
1. Aller sur le repository GitHub
2. Cliquer sur "Code" > "Download ZIP"
3. Extraire le ZIP dans un dossier (ex: `C:\StreamHighlightAI`)
4. Ouvrir PowerShell dans ce dossier:
   - Dans l'explorateur, faire **Shift + Clic-droit** dans le dossier
   - Choisir "Ouvrir PowerShell ici" ou "Ouvrir la fenêtre de commandes ici"

### Étape 2: Créer un environnement virtuel (recommandé)

```powershell
python -m venv venv
```

### Étape 3: Activer l'environnement virtuel

```powershell
.\venv\Scripts\Activate.ps1
```

Si vous obtenez une erreur "impossible d'exécuter des scripts":
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
Puis réessayer.

Vous devriez voir `(venv)` au début de la ligne.

### Étape 4: Installer les dépendances

**Sans GPU (CPU uniquement)**:
```powershell
pip install -r requirements.txt
```

**Avec GPU NVIDIA (recommandé si vous avez une carte NVIDIA)**:
```powershell
pip install -r requirements.txt
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

⏱️ Cette étape prend 5-10 minutes.

### Étape 5: Vérification

```powershell
python main.py --help
```

Vous devriez voir le menu d'aide.

---

## 4. Utilisation

### Commandes de base

**Important**: Toujours utiliser des guillemets pour les chemins avec espaces!

```powershell
# Exemple basique
python main.py -i "C:\Videos\stream.mp4" -o "C:\Videos\highlights.mp4"

# Avec configuration Arc Raiders
python main.py -i "C:\Videos\arc_raiders.mp4" -c examples\config_arc_raiders.yaml

# Avec GPU activé
python main.py -i "C:\Videos\stream.mp4" --gpu

# Test rapide (5 minutes de traitement)
python main.py -i "C:\Videos\stream.mp4" -c examples\config_fast_preview.yaml
```

### Générer une vidéo de test

```powershell
# Créer une petite vidéo de test (2 minutes)
python tests\generate_test_video.py

# Tester l'analyse avec la vidéo de test
python main.py -i tests\test_video.mp4 -c examples\config_fast_preview.yaml
```

---

## 5. Scripts automatiques (.bat)

Pour simplifier l'utilisation, créez des fichiers `.bat`:

### run_arc_raiders.bat

Créer un fichier `run_arc_raiders.bat` avec:

```batch
@echo off
echo ========================================
echo StreamHighlightAI - Arc Raiders
echo ========================================
echo.

REM Activer l'environnement virtuel
call venv\Scripts\activate.bat

REM Demander le fichier d'entrée
set /p INPUT="Entrez le chemin de votre vidéo: "

REM Lancer le traitement
python main.py -i "%INPUT%" -c examples\config_arc_raiders.yaml --gpu -o highlights_arc_raiders.mp4

echo.
echo ========================================
echo Traitement terminé !
echo Vidéo créée: highlights_arc_raiders.mp4
echo ========================================
pause
```

**Utilisation**: Double-cliquer sur `run_arc_raiders.bat`

### test_rapide.bat

```batch
@echo off
echo ========================================
echo Test rapide StreamHighlightAI
echo ========================================
echo.

call venv\Scripts\activate.bat

echo Génération d'une vidéo de test...
python tests\generate_test_video.py -d 2

echo.
echo Analyse de la vidéo de test...
python main.py -i tests\test_video.mp4 -c examples\config_fast_preview.yaml

echo.
echo Terminé ! Vérifiez le fichier highlights.mp4
pause
```

---

## 6. Dépannage Windows

### Problème: "python n'est pas reconnu"

**Solution 1**: Redémarrer l'ordinateur après installation Python

**Solution 2**: Ajouter Python au PATH manuellement
1. Trouver où Python est installé (généralement `C:\Users\VotreName\AppData\Local\Programs\Python\Python311`)
2. Suivre la procédure de la section FFmpeg pour ajouter au PATH
3. Ajouter ces deux chemins:
   - `C:\Users\VotreName\AppData\Local\Programs\Python\Python311`
   - `C:\Users\VotreName\AppData\Local\Programs\Python\Python311\Scripts`

### Problème: "ffmpeg n'est pas reconnu"

**Solution**: Voir section "Installation FFmpeg" et vérifier que le PATH est correct.

Tester dans une **nouvelle** fenêtre PowerShell après modification du PATH.

### Problème: "Impossible d'exécuter des scripts"

**Erreur complète**:
```
.\venv\Scripts\Activate.ps1 : Impossible de charger le fichier...
```

**Solution**:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Problème: "Out of memory" ou crash

**Solutions**:
1. Fermer toutes les autres applications
2. Utiliser une config rapide:
   ```powershell
   python main.py -i video.mp4 -c examples\config_fast_preview.yaml
   ```
3. Désactiver Whisper:
   ```powershell
   python main.py -i video.mp4 --no-whisper
   ```

### Problème: "CUDA not available" malgré GPU NVIDIA

**Solutions**:

1. **Vérifier les drivers NVIDIA**:
   - Ouvrir "GeForce Experience"
   - Mettre à jour les drivers

2. **Réinstaller PyTorch avec CUDA**:
   ```powershell
   pip uninstall torch torchvision torchaudio
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
   ```

3. **Vérifier CUDA**:
   ```powershell
   python -c "import torch; print(f'CUDA disponible: {torch.cuda.is_available()}')"
   ```

### Problème: Traitement très lent

**Raisons possibles**:
- Pas de GPU (utilisation CPU uniquement) → Normal, 3-4x plus lent
- Whisper activé → Désactiver avec `--no-whisper` pour tests
- Antivirus qui scanne → Ajouter une exception pour le dossier StreamHighlightAI

**Optimisations**:
1. Utiliser `config_fast_preview.yaml` pour tests
2. Activer GPU si vous avez une carte NVIDIA
3. Fermer les applications en arrière-plan

### Problème: "ModuleNotFoundError: No module named 'moviepy.editor'"

**Erreur**:
```
ModuleNotFoundError: No module named 'moviepy.editor'
```

**Solution**:
```powershell
# Réinstaller moviepy et ses dépendances
pip install --upgrade decorator proglog pillow
pip install --upgrade moviepy

# Si le problème persiste:
pip uninstall moviepy
pip install moviepy==1.0.3
```

**Vérification**:
```powershell
python -c "from moviepy.editor import VideoFileClip; print('OK')"
```

### Problème: Chemins avec espaces

**Mauvais**:
```powershell
python main.py -i C:\Mes Videos\stream.mp4
```

**Bon**:
```powershell
python main.py -i "C:\Mes Videos\stream.mp4"
```

Toujours utiliser des **guillemets** pour les chemins avec espaces!

### Problème: Encodage de caractères (accents)

Si vous voyez des caractères bizarres dans les logs:

```powershell
chcp 65001
python main.py -i video.mp4
```

---

## 7. Désinstallation

### Supprimer l'environnement virtuel

```powershell
# Désactiver d'abord
deactivate

# Supprimer le dossier venv
Remove-Item -Recurse -Force venv
```

### Désinstaller FFmpeg

**Winget**:
```powershell
winget uninstall ffmpeg
```

**Chocolatey**:
```powershell
choco uninstall ffmpeg
```

**Manuel**: Supprimer le dossier `C:\ffmpeg` et retirer du PATH

---

## 8. Conseils Windows

### Raccourcis utiles

- `Shift + Clic-droit` dans un dossier → "Ouvrir PowerShell ici"
- `Windows + R` → Exécuter une commande
- `Ctrl + C` dans PowerShell → Arrêter le processus

### Performances

- **SSD recommandé** pour stocker les vidéos (traitement plus rapide)
- **16 GB RAM** minimum pour vidéos de 4h+
- **GPU NVIDIA** réduit le temps de traitement de 3-4x

### Organisation

Structure recommandée:
```
C:\StreamHighlightAI\
├── venv\
├── src\
├── examples\
├── tests\
├── main.py
└── MES_VIDEOS\
    ├── streams\        (vidéos sources)
    └── highlights\     (vidéos créées)
```

---

## 9. Workflow recommandé Windows

### Premier test

1. Ouvrir PowerShell dans le dossier StreamHighlightAI
2. Activer l'environnement:
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```
3. Générer une vidéo de test:
   ```powershell
   python tests\generate_test_video.py
   ```
4. Tester rapidement:
   ```powershell
   python main.py -i tests\test_video.mp4 -c examples\config_fast_preview.yaml
   ```
5. Vérifier le résultat: `highlights.mp4`

### Traitement d'un vrai stream

1. Copier votre VOD dans un dossier accessible
2. Test rapide pour vérifier les seuils:
   ```powershell
   python main.py -i "C:\Videos\stream.mp4" -c examples\config_fast_preview.yaml
   ```
3. Si les segments détectés sont bons → Traitement final:
   ```powershell
   python main.py -i "C:\Videos\stream.mp4" -c examples\config_arc_raiders.yaml --gpu
   ```

---

## 10. Support

### Problèmes courants Windows

La plupart des problèmes Windows sont liés à:
1. **PATH incorrecte** (Python ou FFmpeg)
2. **Chemins avec espaces** non quotés
3. **Politique d'exécution** PowerShell
4. **Antivirus** qui bloque

### Obtenir de l'aide

- **GitHub Issues**: [github.com/votre-username/StreamHighlightAI/issues](https://github.com)
- **Documentation**: Voir README.md principal
- **Discord**: Rejoindre la communauté

### Informations utiles pour le debug

Avant de demander de l'aide, fournir:
```powershell
python --version
ffmpeg -version
python -c "import torch; print(torch.cuda.is_available())"
```

---

**Bon montage! 🎮✂️**

*Guide testé sur Windows 10 (22H2) et Windows 11*
