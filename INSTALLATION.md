# 🚀 Installation Complète - StreamHighlightAI

Guide d'installation **étape par étape** pour Windows avec GPU NVIDIA (RTX 4070 Ti).

---

## 📋 TABLE DES MATIÈRES

1. [Prérequis système](#-prérequis-système)
2. [Installation Python](#-étape-1--installation-python)
3. [Clonage du projet](#-étape-2--clonage-du-projet)
4. [Environnement virtuel](#-étape-3--environnement-virtuel)
5. [Dépendances Python](#-étape-4--dépendances-python)
6. [FFmpeg](#-étape-5--ffmpeg)
7. [Support GPU (CUDA)](#-étape-6--support-gpu-cuda)
8. [LLaVA (optionnel)](#-étape-7--llava-optionnel)
9. [Vérification](#-étape-8--vérification)
10. [Premier test](#-étape-9--premier-test)
11. [Dépannage](#-dépannage)

---

## 🖥️ Prérequis système

### **Configuration minimale**
- Windows 10/11
- 8 GB RAM
- 20 GB espace disque libre
- Python 3.8+

### **Configuration recommandée** (pour GPU)
- Windows 10/11
- 16 GB RAM
- GPU NVIDIA (RTX 2060+) avec 8+ GB VRAM
- 50 GB espace disque libre
- Python 3.10

### **Votre config (RTX 4070 Ti) = PARFAITE ! 🔥**

---

## 🐍 ÉTAPE 1 : Installation Python

### Vérifier si Python est installé

```powershell
python --version
```

Si vous voyez `Python 3.10.x` ou `3.11.x` → **OK, passez à l'étape 2**

### Si Python n'est pas installé

**Option A : Installeur officiel** (recommandé)

1. Aller sur https://www.python.org/downloads/
2. Télécharger **Python 3.10** ou **3.11** (pas 3.12, compatibilité PyTorch)
3. **IMPORTANT** : Cocher "Add Python to PATH" pendant l'installation
4. Installer

**Option B : Via winget**

```powershell
winget install Python.Python.3.10
```

### Vérifier l'installation

```powershell
python --version
pip --version
```

Devrait afficher :
```
Python 3.10.x
pip 23.x.x
```

---

## 📦 ÉTAPE 2 : Clonage du projet

### Si vous avez déjà le projet

```powershell
cd J:\claude_code_video\video
```

### Si vous devez cloner depuis GitHub

```powershell
# Aller dans votre dossier de travail
cd J:\claude_code_video

# Cloner le repo
git clone https://github.com/arthoine/video.git
cd video
```

---

## 🔧 ÉTAPE 3 : Environnement virtuel

Créer un environnement Python isolé :

```powershell
# Dans le dossier du projet (J:\claude_code_video\video)
python -m venv venv
```

Activer l'environnement :

```powershell
.\venv\Scripts\Activate.ps1
```

Vous devriez voir `(venv)` au début de votre ligne de commande :
```
(venv) PS J:\claude_code_video\video>
```

**⚠️ Si erreur "Execution Policy"** :
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
Puis réessayer l'activation.

---

## 📚 ÉTAPE 4 : Dépendances Python

### Mettre à jour pip

```powershell
python -m pip install --upgrade pip
```

### Installer les dépendances de base

```powershell
pip install -r requirements.txt
```

Si pas de `requirements.txt`, installer manuellement :

```powershell
# Core
pip install numpy opencv-python moviepy pillow tqdm pyyaml

# Audio
pip install librosa soundfile audioread

# ML
pip install openai-whisper

# LLaVA
pip install ollama
```

**Temps estimé :** 5-10 minutes

---

## 🎬 ÉTAPE 5 : FFmpeg

FFmpeg est requis pour l'encodage vidéo GPU.

### Vérifier si FFmpeg est installé

```powershell
ffmpeg -version
```

Si ça affiche une version → **OK, passez à l'étape 6**

### Si FFmpeg n'est pas installé

**Option A : Via winget** (le plus simple)

```powershell
winget install Gyan.FFmpeg
```

**Option B : Installation manuelle**

1. Aller sur https://www.gyan.dev/ffmpeg/builds/
2. Télécharger **ffmpeg-git-full.7z**
3. Extraire dans `C:\ffmpeg`
4. Ajouter `C:\ffmpeg\bin` au PATH :
   - Ouvrir "Modifier les variables d'environnement système"
   - Variables d'environnement → PATH → Modifier
   - Nouveau → `C:\ffmpeg\bin`
   - OK

### Vérifier l'installation

**Fermer et rouvrir PowerShell**, puis :

```powershell
ffmpeg -version
ffprobe -version
```

Devrait afficher les versions.

---

## 🎮 ÉTAPE 6 : Support GPU (CUDA)

Pour utiliser votre RTX 4070 Ti avec Whisper et l'encodage NVENC.

### 6.1 : Vérifier les drivers NVIDIA

```powershell
nvidia-smi
```

Devrait afficher :
```
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 5xx.xx       Driver Version: 5xx.xx       CUDA Version: 12.x  |
|-------------------------------+----------------------+----------------------+
|   0  NVIDIA GeForce RTX 4070 Ti ...
```

Si erreur → Installer/mettre à jour les drivers : https://www.nvidia.com/Download/index.aspx

### 6.2 : Installer PyTorch avec CUDA

**Désinstaller PyTorch CPU** (si installé) :
```powershell
pip uninstall torch torchvision torchaudio
```

**Installer PyTorch GPU** :
```powershell
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

**Taille :** ~2.5 GB
**Temps :** 5-10 minutes

### 6.3 : Vérifier CUDA

```powershell
python -c "import torch; print(f'CUDA disponible: {torch.cuda.is_available()}'); print(f'GPU: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"None\"}')"
```

Devrait afficher :
```
CUDA disponible: True
GPU: NVIDIA GeForce RTX 4070 Ti
```

---

## 🧠 ÉTAPE 7 : LLaVA (optionnel mais recommandé)

Pour l'analyse sémantique intelligente.

### 7.1 : Installer Ollama

**Option A : Via winget**
```powershell
winget install Ollama.Ollama
```

**Option B : Téléchargement manuel**
https://ollama.ai/download

### 7.2 : Télécharger LLaVA

```powershell
ollama pull llava:7b
```

**Taille :** ~4.7 GB
**Temps :** 5-15 minutes selon connexion

### 7.3 : Installer package Python

```powershell
pip install ollama
```

### 7.4 : Tester LLaVA

```powershell
ollama run llava:7b
```

Si ça démarre, tapez `/bye` pour quitter.

**✅ LLaVA installé !**

---

## ✅ ÉTAPE 8 : Vérification

Exécuter le script de vérification :

```powershell
python main.py --help
```

Devrait afficher l'aide du programme.

### Vérification manuelle complète

```powershell
python check_gpu.py
```

Devrait afficher :
```
✓ FFmpeg détecté
✓ FFprobe détecté
✓ CUDA disponible (NVIDIA GeForce RTX 4070 Ti)
✓ Whisper disponible
✓ OpenCV disponible
✓ MoviePy disponible
✓ Librosa disponible
✓ Ollama disponible
✓ LLaVA disponible (llava:7b)

🎉 Configuration complète !
```

---

## 🎬 ÉTAPE 9 : Premier test

### Test rapide (sans LLaVA)

```powershell
# Analyser une vidéo
python main.py -i "J:\votre_video.mp4" -o highlights.mp4
```

**Temps estimé :** ~15 minutes pour 60 min de vidéo

### Test complet (avec LLaVA)

```powershell
# Analyser avec compréhension sémantique
python main.py -i "J:\votre_video.mp4" -c config_rtx4070ti.yaml -o highlights_llava.mp4
```

**Temps estimé :** ~22 minutes pour 60 min de vidéo

---

## 🔍 Logs attendus

### Démarrage
```
============================================================
StreamHighlightAI - Démarrage
============================================================
✓ FFmpeg détecté
✓ FFprobe détecté
✓ CUDA détecté (NVIDIA GeForce RTX 4070 Ti)
Configuration chargée depuis config_rtx4070ti.yaml
```

### Analyse
```
🎮 Mode GPU activé pour l'analyse
🎮 Chargement Whisper 'base' sur GPU
✓ Modèle Whisper chargé
Vidéo: 60.3 minutes (3619s)
Analyse de 724 segments de 5s
```

### LLaVA (si activé)
```
🧠 Analyseur sémantique LLaVA activé
🧠 Analyse sémantique avec LLaVA...
Frames: 100%|████████████████| 724/724
📊 Résumé analyse sémantique:
   pvp_combat: 234 segments
   crafting: 45 segments
```

### Montage
```
🔗 Fusion des segments consécutifs activée
Fusion: 724 segments → 200 segments fusionnés
✓ 28 segments sélectionnés
🚀 Utilisation de FFmpeg DIRECT (bypass MoviePy)
🎮 ENCODAGE GPU AVEC h264_nvenc
```

### Fin
```
✅ ENCODAGE RÉUSSI!
   Fichier créé: highlights.mp4
   Taille: 2228.7 MB
✓ TRAITEMENT TERMINÉ AVEC SUCCÈS
```

---

## 🐛 Dépannage

### ❌ "Python command not found"

**Solution :** Python pas dans le PATH
```powershell
# Trouver où Python est installé
where python

# Si pas trouvé, réinstaller Python avec "Add to PATH" coché
```

### ❌ "CUDA not available" (torch.cuda.is_available() = False)

**Solutions :**

1. **Vérifier drivers NVIDIA**
   ```powershell
   nvidia-smi
   ```
   Si erreur → Mettre à jour : https://www.nvidia.com/Download/index.aspx

2. **Réinstaller PyTorch GPU**
   ```powershell
   pip uninstall torch torchvision torchaudio
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
   ```

3. **Vérifier compatibilité CUDA**
   ```powershell
   python -c "import torch; print(torch.version.cuda)"
   ```
   Doit afficher `12.1` ou similaire

### ❌ "FFmpeg not found"

**Solution :** FFmpeg pas dans le PATH

```powershell
# Tester
ffmpeg -version

# Si erreur, ajouter au PATH (voir Étape 5)
# Puis REDÉMARRER PowerShell
```

### ❌ "Ollama connection refused"

**Solution :** Service Ollama non démarré

```powershell
# Vérifier si Ollama tourne
Get-Process ollama

# Si absent, lancer manuellement
ollama serve
```

Ou redémarrer Windows (Ollama démarre auto normalement).

### ❌ Warning "PySoundFile failed"

**Impact :** Extraction audio 2x plus lente (mais fonctionne)

**Solution optionnelle :**
```powershell
pip uninstall soundfile -y
pip install soundfile
```

### ❌ "Out of memory" (CUDA)

**Solutions :**

1. **Réduire batch LLaVA**
   ```yaml
   llava:
     batch_size: 3  # Au lieu de 5
   ```

2. **Fermer autres applications GPU** (navigateur, jeux, etc.)

3. **Vérifier VRAM disponible**
   ```powershell
   nvidia-smi
   ```

### ❌ Analyse très lente

**Vérifications :**

1. **GPU utilisé ?**
   ```powershell
   nvidia-smi
   # GPU-Util doit être > 50% pendant l'analyse
   ```

2. **Config GPU activée ?**
   ```yaml
   performance:
     use_gpu: true  # Vérifier dans config
   ```

3. **PyTorch GPU installé ?**
   ```powershell
   python -c "import torch; print(torch.cuda.is_available())"
   # Doit être True
   ```

---

## 📊 Résumé des temps (RTX 4070 Ti)

| Étape | Temps installation | Temps première utilisation (60 min vidéo) |
|-------|-------------------|-------------------------------------------|
| Python + venv | 5 min | - |
| Dépendances pip | 5-10 min | - |
| FFmpeg | 2 min | - |
| PyTorch CUDA | 10 min | - |
| LLaVA | 10-15 min | - |
| **TOTAL INSTALL** | **~35-45 min** | - |
| Analyse (sans LLaVA) | - | ~15 min |
| Analyse (avec LLaVA) | - | ~22 min |

---

## 📂 Structure du projet

```
video/
├── main.py                 # Point d'entrée
├── src/
│   ├── analyzer.py        # Analyse vidéo
│   ├── editor.py          # Montage
│   ├── ffmpeg_encoder.py  # Encodage GPU
│   ├── llm_analyzer.py    # LLaVA (sémantique)
│   └── utils.py
├── config.yaml            # Config par défaut
├── config_rtx4070ti.yaml  # Config optimisée GPU
├── requirements.txt
├── INSTALLATION.md        # Ce fichier
├── INSTALL_LLAVA.md       # Guide LLaVA détaillé
└── venv/                  # Environnement Python
```

---

## 🚀 Commandes essentielles

```powershell
# Activer l'environnement virtuel
.\venv\Scripts\Activate.ps1

# Analyser une vidéo (sans LLaVA)
python main.py -i video.mp4 -o highlights.mp4

# Analyser avec LLaVA (compréhension sémantique)
python main.py -i video.mp4 -c config_rtx4070ti.yaml -o highlights.mp4

# Analyser avec durée cible personnalisée
python main.py -i video.mp4 -o highlights.mp4 -d 10  # 10 minutes

# Vérifier GPU
python check_gpu.py

# Aide
python main.py --help
```

---

## 📖 Documentation complète

- **Guide LLaVA détaillé** : `INSTALL_LLAVA.md`
- **Configurations exemples** : `examples/`
- **Guide optimisation GPU** : `GPU_OPTIMIZATION.md`
- **Guide RTX 4070 Ti** : `RTX4070TI_GUIDE.md`

---

## ❓ Besoin d'aide ?

1. Consulter le **[Dépannage](#-dépannage)** ci-dessus
2. Vérifier les logs d'erreur
3. Ouvrir une issue : https://github.com/arthoine/video/issues

---

## ✅ Checklist finale

Avant de lancer votre première analyse, vérifiez :

- [ ] Python 3.10+ installé
- [ ] Environnement virtuel activé (`(venv)` visible)
- [ ] `pip install -r requirements.txt` terminé
- [ ] `ffmpeg -version` fonctionne
- [ ] `nvidia-smi` affiche votre GPU
- [ ] `torch.cuda.is_available()` = True
- [ ] (Optionnel) `ollama list` affiche `llava:7b`
- [ ] `python main.py --help` affiche l'aide

**Si tous cochés → Vous êtes prêt ! 🎉**

```powershell
python main.py -i "J:\cliptwitch_fixed.mp4" -c config_rtx4070ti.yaml -o highlights.mp4
```

**Let's go ! 🚀🔥**
