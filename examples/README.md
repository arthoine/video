# Exemples de configurations

Ce dossier contient des configurations pré-configurées pour différents cas d'usage.

## 📁 Configurations disponibles

### 🎯 config_fps_intense.yaml
**Optimisé pour**: Jeux FPS intenses (Valorant, CS:GO, Call of Duty, Apex Legends)

**Caractéristiques**:
- Segments courts (4s) pour précision maximale
- Priorité sur l'audio (55%) et le visuel (40%)
- Détection sensible des changements rapides
- Transitions courtes et dynamiques
- Export 1080p 60fps

**Utilisation**:
```bash
python main.py -i valorant_stream.mp4 -c examples/config_fps_intense.yaml
```

---

### 💬 config_talk_show.yaml
**Optimisé pour**: Streams discussion/talk/podcast

**Caractéristiques**:
- Segments longs (8s) pour capturer le dialogue
- Priorité sur la transcription Whisper (50%)
- Modèle Whisper medium pour meilleure précision
- Transitions douces
- 30fps suffisant (pas besoin de 60fps)

**Utilisation**:
```bash
python main.py -i podcast_stream.mp4 -c examples/config_talk_show.yaml
```

---

### ⭐ config_max_quality.yaml
**Optimisé pour**: Contenu premium/professionnel pour YouTube

**Caractéristiques**:
- Qualité maximale: 4K, CRF 16, preset slower
- Segments très précis (3s)
- Audio 320kbps
- Modèle Whisper medium/large
- **⚠️ Traitement 2-4x plus lent**

**Utilisation**:
```bash
python main.py -i best_stream.mp4 -c examples/config_max_quality.yaml --gpu
```

**Recommandations**:
- GPU NVIDIA obligatoire
- Au moins 16 GB de RAM
- Espace disque suffisant (fichier 2-3x plus gros)

---

### ⚡ config_fast_preview.yaml
**Optimisé pour**: Test rapide et preview

**Caractéristiques**:
- Whisper désactivé
- Segments longs (10s)
- Qualité réduite: 720p 30fps
- Preset veryfast
- Pas de transitions
- **⚡ Traitement 3-4x plus rapide**

**Utilisation**:
```bash
python main.py -i stream.mp4 -c examples/config_fast_preview.yaml
```

**Cas d'usage**:
1. Tester l'algorithme sur une nouvelle vidéo
2. Ajuster les seuils de détection
3. Vérifier que les bons moments sont capturés
4. Une fois satisfait → utiliser une config qualité

---

## 🎨 Personnalisation

Vous pouvez créer vos propres configurations en copiant un exemple:

```bash
cp examples/config_fps_intense.yaml config_custom.yaml
# Éditer config_custom.yaml selon vos besoins
python main.py -i stream.mp4 -c config_custom.yaml
```

### Paramètres clés à ajuster

#### Pour plus de segments détectés:
```yaml
analysis:
  audio_intensity_threshold: 0.5  # Plus bas = plus sensible
  min_score_threshold: 0.2
```

#### Pour moins de segments (meilleure qualité):
```yaml
analysis:
  audio_intensity_threshold: 0.8  # Plus haut = plus sélectif
  min_score_threshold: 0.4
```

#### Pour traitement plus rapide:
```yaml
analysis:
  enable_whisper: false
  segment_duration_seconds: 10

output:
  preset: fast
  quality: 720p
```

#### Pour meilleure qualité:
```yaml
output:
  preset: slower
  crf: 16
  quality: 4k
```

---

## 📊 Comparaison des configurations

| Config | Vitesse | Qualité | Précision | Cas d'usage |
|--------|---------|---------|-----------|-------------|
| **fast_preview** | ⚡⚡⚡⚡⚡ | ⭐⭐ | ⭐⭐⭐ | Tests rapides |
| **fps_intense** | ⚡⚡⚡ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | FPS compétitifs |
| **talk_show** | ⚡⚡ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Discussions |
| **max_quality** | ⚡ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Upload YouTube premium |

---

## 💡 Conseils

### Workflow recommandé

1. **Test rapide** avec `config_fast_preview.yaml`
   - Vérifier que l'algorithme fonctionne bien
   - Ajuster les seuils si nécessaire

2. **Traitement final** avec config adaptée
   - FPS: `config_fps_intense.yaml`
   - Talk: `config_talk_show.yaml`
   - Premium: `config_max_quality.yaml`

### Ajustement des seuils

Si vous obtenez **trop de segments**:
- Augmenter `audio_intensity_threshold` (0.7 → 0.8)
- Augmenter `min_score_threshold` (0.3 → 0.4)
- Augmenter `min_gap_between_segments` (30 → 40)

Si vous obtenez **pas assez de segments**:
- Diminuer `audio_intensity_threshold` (0.7 → 0.6)
- Diminuer `min_score_threshold` (0.3 → 0.2)
- Activer Whisper si désactivé

---

## 🎮 Configurations par jeu

### Valorant / CS:GO / Rainbow Six
→ `config_fps_intense.yaml`

### Apex Legends / Fortnite (BR)
→ `config_fps_intense.yaml` avec `max_segment_duration: 40`

### League of Legends / Dota 2
→ Config custom avec segments plus longs:
```yaml
analysis:
  segment_duration_seconds: 8
editing:
  max_segment_duration: 45
```

### Minecraft / Sandbox
→ `config_talk_show.yaml` avec ajustements:
```yaml
analysis:
  score_weights:
    audio: 0.4
    visual: 0.3
    transcription: 0.3
```

### Speedruns
→ Config custom focus visuel:
```yaml
analysis:
  score_weights:
    audio: 0.3
    visual: 0.6
    transcription: 0.1
```

---

## ❓ Questions fréquentes

**Q: Quelle config pour débuter?**
R: Utilisez `config.yaml` (par défaut) qui offre un bon équilibre.

**Q: Ma vidéo prend trop de temps à traiter**
R: Utilisez `config_fast_preview.yaml` ou désactivez Whisper avec `--no-whisper`.

**Q: Les segments détectés ne sont pas bons**
R: Ajustez `audio_intensity_threshold` dans votre config ou créez une config custom.

**Q: Puis-je combiner plusieurs configs?**
R: Non directement, mais vous pouvez créer une nouvelle config en copiant les parties qui vous intéressent.

---

**Besoin d'aide?** Consultez le [README principal](../README.md) ou ouvrez une issue sur GitHub.
