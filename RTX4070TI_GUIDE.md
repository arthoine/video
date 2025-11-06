# 🚀 Guide d'optimisation RTX 4070 Ti

Configuration et utilisation optimale de StreamHighlightAI avec votre **NVIDIA GeForce RTX 4070 Ti**.

---

## 📊 Spécifications RTX 4070 Ti

- **VRAM**: 12 GB GDDR6X
- **CUDA Cores**: 7680
- **Architecture**: Ada Lovelace (4000 series)
- **Encodeur**: NVENC 8th generation
- **Tensor Cores**: Oui (pour Whisper accéléré)
- **Support AV1**: Oui (hardware)

**Cette carte est EXCELLENTE pour l'édition vidéo! 🔥**

---

## ⚡ Performances attendues

### 1h de vidéo → 15 min de highlights

| Étape | Temps |
|-------|-------|
| Analyse Whisper (CUDA) | **45-90 sec** |
| Analyse visuelle | 30 sec |
| Sélection segments | 5 sec |
| Extraction clips | 30 sec |
| **Encodage NVENC** | **3-4 min** |
| **TOTAL** | **~6-8 min** ⚡ |

**Comparé à CPU uniquement**: ~35-50 min → **Gain de 6x!**

---

## 🎯 Configuration recommandée

### Option 1: Config RTX 4070 Ti dédiée (RECOMMANDÉ)

```bash
python main.py -i video.mp4 -c config_rtx4070ti.yaml -o highlights.mp4
```

Cette config est **spécifiquement optimisée** pour ta carte:
- Preset NVENC: `hq` (high quality)
- CQ: 20 (excellente qualité)
- Chunks audio: 120s (tire parti des 12GB VRAM)
- Whisper: `base` sur CUDA

### Option 2: Config générale (par défaut)

```bash
python main.py -i video.mp4 -o highlights.mp4
```

Le `config.yaml` a maintenant `use_gpu: true` par défaut.

### Option 3: Ligne de commande

```bash
python main.py -i video.mp4 --gpu -o highlights.mp4
```

---

## ✅ Vérification GPU

### Avant de lancer l'encodage:

**Double-clic sur:**
```
check_gpu.bat
```

Ou en ligne de commande:
```powershell
python check_gpu.py
```

**Tu DOIS voir:**
```
✅ GPU NVIDIA
✅ PyTorch CUDA
✅ FFmpeg NVENC
✅ Configuration

🎉 TOUT EST BON!
```

Si une croix rouge apparaît, suis les instructions affichées.

---

## 📈 Surveillance GPU en temps réel

**Pendant l'encodage**, ouvre un autre PowerShell:

```powershell
nvidia-smi -l 1
```

### Ce que tu dois voir:

```
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 581.80       Driver Version: 581.80       CUDA Version: 11.8     |
|-------------------------------+----------------------+----------------------+
| GPU  Name        Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util |
|   0  RTX 4070 Ti  70C    P2   220W / 285W |   4500MiB / 12282MiB |   85%    |
+-------------------------------+----------------------+----------------------+
```

**Indicateurs clés:**
- ✅ **GPU-Util**: 80-95% (GPU actif!)
- ✅ **Power**: 200-250W (GPU travaille!)
- ✅ **Temp**: 65-75°C (normal)
- ✅ **Memory**: 3-6 GB utilisés

❌ **Si GPU-Util < 10%**: Le GPU n'est PAS utilisé!

---

## 🎮 Commandes GPU activées (vérification logs)

Quand tu lances l'encodage, tu DOIS voir dans les logs:

```
02:51:25 | INFO     | ✓ CUDA détecté (NVIDIA GeForce RTX 4070 Ti)
...
02:51:25 | INFO     | Chargement du modèle Whisper 'base' sur cuda...
...
03:15:42 | INFO     | 🎮 Utilisation de l'accélération GPU NVIDIA (h264_nvenc)
```

☝️ **Si l'emoji 🎮 n'apparaît PAS** → GPU pas utilisé pour l'encodage!

---

## 📊 Vitesse d'encodage

### Avec GPU (NVENC):
```
t:  10%|███████| 5400/54000 [00:35<05:12, 155it/s]
                                        ↑ 120-180 it/s
```

### Sans GPU (CPU libx264):
```
t:  10%|███| 5400/54000 [08:45<1:18:23, 10.3it/s]
                                     ↑ 7-12 it/s
```

**Si tu vois 7-12 it/s → GPU PAS utilisé!**

---

## 🔧 Paramètres avancés RTX 4070 Ti

### Pour MAXIMUM vitesse (preview):

```yaml
output:
  preset: fast      # Plus rapide que 'hq'
  crf: 23          # Qualité standard
  fps: 30          # 30fps au lieu de 60
  quality: 720p    # 720p au lieu de 1080p
```

**Temps**: ~3-4 minutes au lieu de 6-8 min

### Pour MAXIMUM qualité:

```yaml
output:
  preset: bd       # Blu-ray quality
  crf: 18         # Qualité exceptionnelle
  fps: 60
  quality: 1080p
```

**Temps**: ~8-10 minutes (qualité Netflix/Blu-ray)

### Pour 4K (ta 4070 Ti peut!):

```yaml
output:
  quality: 4k
  preset: hq
  crf: 20
  fps: 60
```

**Temps**: ~12-15 minutes (si source en 4K)

---

## 🐛 Dépannage RTX 4070 Ti

### Problème: GPU à 4% au lieu de 80%

**Cause**: h264_nvenc pas utilisé (fallback sur CPU)

**Solutions**:
1. Vérifie les logs pour l'emoji 🎮
2. Lance `check_gpu.bat` pour diagnostic
3. Vérifie FFmpeg: `ffmpeg -encoders | findstr nvenc`
4. Mets à jour drivers NVIDIA

### Problème: "CUDA not available" avec PyTorch

**Solution**:
```powershell
pip uninstall torch torchvision torchaudio
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

Puis teste:
```powershell
python -c "import torch; print(torch.cuda.is_available())"
```

Doit afficher: `True`

### Problème: Whisper lent malgré GPU

**Vérification**:
- Les logs doivent dire: `Chargement du modèle Whisper 'base' sur cuda`
- Si c'est `cpu` → PyTorch CUDA pas installé

**Solution**: Réinstalle PyTorch avec CUDA (voir ci-dessus)

### Problème: Encodage encore lent (15-20 min)

**Vérifications**:
1. `nvidia-smi` montre GPU utilisé?
2. Logs montrent emoji 🎮?
3. Vitesse it/s > 100?

Si NON à l'un → Le GPU n'est pas utilisé, relance `check_gpu.bat`

---

## 💡 Astuces RTX 4070 Ti

### 1. Batch processing (plusieurs vidéos)

Ta 4070 Ti a 12GB VRAM, tu peux traiter plusieurs vidéos en parallèle:

```powershell
# Terminal 1
python main.py -i video1.mp4 -c config_rtx4070ti.yaml -o highlights1.mp4

# Terminal 2 (simultané!)
python main.py -i video2.mp4 -c config_rtx4070ti.yaml -o highlights2.mp4
```

La carte peut gérer 2-3 encodages simultanés!

### 2. Monitoring avancé

Pour voir les stats détaillées:
```powershell
nvidia-smi dmon -s pucvmet
```

### 3. Overclocking (optionnel)

Si tu veux encore plus de perf, utilise MSI Afterburner:
- +100 MHz core clock
- +500 MHz memory clock
- Power limit: 110%

**Gain**: ~5-10% de vitesse supplémentaire

### 4. Refroidissement

Pour maintenir les perfs:
- Assure une bonne ventilation du boîtier
- Courbe de ventilateur GPU agressive (70% à 70°C)
- La 4070 Ti est efficace (285W max)

---

## 📦 Scripts rapides

### Script batch pour traitement automatique:

Créé `process_all.bat`:
```batch
@echo off
for %%f in (*.mp4) do (
    echo Traitement de %%f...
    python main.py -i "%%f" -c config_rtx4070ti.yaml -o "highlights_%%f"
)
echo Tous les fichiers traites!
pause
```

Place dans ton dossier de vidéos et double-clic!

---

## 🎯 Résumé RTX 4070 Ti

| Aspect | Performance |
|--------|-------------|
| **Whisper** | 15x plus rapide que CPU |
| **Encodage** | 7x plus rapide que CPU |
| **Temps total** (1h→15min) | **6-8 minutes** |
| **Qualité** | Identique à CPU |
| **VRAM utilisée** | 3-6 GB / 12 GB |
| **Power** | 200-250W |
| **Température** | 65-75°C |

**Ta 4070 Ti est parfaite pour ce workflow!** 🚀

---

## 📚 Configurations disponibles

| Fichier | Usage | Temps (1h→15min) |
|---------|-------|------------------|
| `config_rtx4070ti.yaml` | **Optimal pour ta carte** | ~6-8 min |
| `config_gpu_nvidia.yaml` | GPU générique | ~8-10 min |
| `config.yaml` | Par défaut (GPU actif) | ~10-12 min |
| `config_fast_preview.yaml` | Preview rapide | ~3-4 min |
| `config_max_quality.yaml` | Qualité maximale | ~12-15 min |

---

## 🆘 Support

Si quelque chose ne va pas:

1. Lance `check_gpu.bat` → Capture d'écran
2. Lance ton encodage → Copie les logs
3. Lance `nvidia-smi` → Capture d'écran
4. Envoie tout pour diagnostic

**Ta RTX 4070 Ti devrait exploser les temps de traitement! Si ce n'est pas le cas, c'est qu'il y a un problème de config à régler.** 🔥

---

*Guide optimisé pour RTX 4070 Ti | 12GB VRAM | Ada Lovelace Architecture*
