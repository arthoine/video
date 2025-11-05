# 🎮 StreamHighlightAI

**Outil d'édition automatique de streams gaming avec IA locale**

Transformez automatiquement vos VODs de 4 heures en vidéos YouTube de 10-25 minutes avec les meilleurs moments, le tout traité localement sans API cloud.

![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-stable-brightgreen.svg)

---

## 📋 Table des matières

- [Fonctionnalités](#-fonctionnalités)
- [Démo](#-démo)
- [Installation](#-installation)
- [Utilisation rapide](#-utilisation-rapide)
- [Configuration](#-configuration)
- [Comment ça marche](#-comment-ça-marche)
- [Optimisations](#-optimisations)
- [Exemples](#-exemples)
- [Dépannage](#-dépannage)
- [Contribution](#-contribution)
- [Licence](#-licence)

---

## ✨ Fonctionnalités

### 🎯 Analyse intelligente
- **Détection audio**: Identifie les pics sonores (kills, réactions, explosions)
- **Analyse visuelle**: Détecte les changements de scène rapides (action intense)
- **Transcription IA**: Utilise Whisper (local) pour détecter les réactions vocales
- **Score multi-critères**: Combine plusieurs métriques pour un classement optimal

### ✂️ Montage automatique
- **Sélection intelligente**: Algorithme qui choisit les N meilleurs segments
- **Filtrage spatial**: Évite les clips trop rapprochés (30s min entre segments)
- **Contexte ajouté**: 2-3 secondes avant/après chaque moment clé
- **Transitions fluides**: Crossfade, cut, ou transitions personnalisées

### 🚀 Performance
- **100% local**: Aucune API cloud, aucune limite d'utilisation
- **Support GPU**: Accélération CUDA pour Whisper et l'export vidéo
- **Cache intelligent**: Réutilise les analyses précédentes
- **Traitement par chunks**: Gère les vidéos de plusieurs heures sans problème de RAM

### 📺 Export optimisé
- **Format YouTube**: 1080p 60fps, codec H.264, audio AAC
- **Qualité personnalisable**: 720p / 1080p / 4K
- **Intro/Outro**: Support optionnel de séquences d'intro et outro
- **Métadonnées**: Préserve les informations du stream original

---

## 🎬 Démo

**Avant**: VOD de stream de 4 heures (5.2 GB)
```
[========================================] 4h 12m 34s
```

**Après**: Highlights de 15 minutes (234 MB)
```
[====] 15m 02s
  ↓
✓ Détection: 47 segments trouvés
✓ Sélection: 12 meilleurs segments
✓ Montage: Transitions + Intro/Outro
```

**Résultat**: Vidéo prête pour upload YouTube avec uniquement les moments forts!

---

## 📦 Installation

### Prérequis

- **Python**: 3.8 ou supérieur
- **FFmpeg**: Obligatoire (installation système)
- **GPU** (optionnel): NVIDIA avec CUDA pour accélération

### Installation rapide

#### 1. Cloner le repository

```bash
git clone https://github.com/votre-username/StreamHighlightAI.git
cd StreamHighlightAI
```

#### 2. Installer FFmpeg

**Ubuntu/Debian**:
```bash
sudo apt update
sudo apt install ffmpeg
```

**MacOS**:
```bash
brew install ffmpeg
```

**Windows**:
Téléchargez depuis [ffmpeg.org](https://ffmpeg.org/download.html) et ajoutez au PATH

#### 3. Installer les dépendances Python

**Sans GPU (CPU uniquement)**:
```bash
pip install -r requirements.txt
```

**Avec GPU NVIDIA (CUDA)**:
```bash
pip install -r requirements.txt
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

#### 4. Vérifier l'installation

```bash
python main.py --help
```

Si tout fonctionne, vous devriez voir le menu d'aide.

---

## 🚀 Utilisation rapide

### Commande de base

```bash
python main.py --input stream.mp4 --output highlights.mp4
```

### Avec durée personnalisée

```bash
python main.py -i stream.mp4 -d 20 -o highlights.mp4
```

### Avec toutes les options

```bash
python main.py \
  --input stream.mp4 \
  --output highlights.mp4 \
  --duration 15 \
  --quality 1080p \
  --gpu \
  --intro intro.mp4 \
  --outro outro.mp4
```

### Arguments disponibles

| Argument | Court | Description | Défaut |
|----------|-------|-------------|--------|
| `--input` | `-i` | Vidéo source (obligatoire) | - |
| `--output` | `-o` | Vidéo de sortie | `highlights.mp4` |
| `--duration` | `-d` | Durée cible en minutes | `15` |
| `--quality` | - | Qualité (720p/1080p/4k) | `1080p` |
| `--config` | `-c` | Fichier de config YAML | `config.yaml` |
| `--gpu` | - | Activer accélération GPU | `false` |
| `--no-whisper` | - | Désactiver transcription | `false` |
| `--no-cache` | - | Désactiver le cache | `false` |
| `--verbose` | `-v` | Mode verbeux | `false` |
| `--intro` | - | Vidéo d'intro | - |
| `--outro` | - | Vidéo d'outro | - |

---

## ⚙️ Configuration

### Fichier config.yaml

Le fichier `config.yaml` contient tous les paramètres personnalisables. Exemples de configurations:

#### Configuration rapide (traitement accéléré)

```yaml
analysis:
  segment_duration_seconds: 10  # Segments plus longs
  enable_whisper: false  # Désactiver transcription

performance:
  use_gpu: true
  use_cache: true
```

#### Configuration précise (meilleure détection)

```yaml
analysis:
  segment_duration_seconds: 3  # Segments plus courts
  audio_intensity_threshold: 0.6  # Plus sensible
  enable_whisper: true
  whisper_model: medium  # Modèle plus précis

editing:
  min_gap_between_segments: 45  # Plus d'espace entre clips
```

#### Configuration qualité maximale (pour YouTube)

```yaml
output:
  quality: 4k
  fps: 60
  preset: slow  # Meilleure compression
  crf: 16  # Qualité élevée
```

Voir `config.yaml` pour la liste complète des paramètres.

### Configurations personnalisées

Créez plusieurs fichiers de config pour différents cas d'usage:

```bash
# Stream FPS intense
python main.py -i stream.mp4 -c config_fps.yaml

# Stream calme (discussions)
python main.py -i stream.mp4 -c config_talk.yaml
```

Exemples disponibles dans le dossier `examples/`.

---

## 🧠 Comment ça marche

### Algorithme de détection en 5 étapes

#### 1. Découpage en segments
La vidéo est découpée en segments de 5 secondes (configurable).

```
Vidéo (4h)  →  [Seg1][Seg2][Seg3]...[Seg2880]
```

#### 2. Analyse multi-critères

Pour chaque segment, calcul de 3 scores:

**A. Score Audio (50%)**
- Mesure l'intensité sonore (RMS)
- Détecte les pics soudains (explosions, cris)
- Calcule la densité des variations

```python
score_audio = (intensité_RMS * 0.7) + (densité_pics * 0.3)
```

**B. Score Visuel (35%)**
- Compare les frames successives
- Détecte les changements rapides (action intense)
- Utilise la différence de pixels

```python
score_visuel = moyenne(diff_entre_frames)
```

**C. Score Transcription (15%)**
- Transcrit l'audio avec Whisper
- Détecte les mots-clés d'excitation: "wow", "oh", "nice", etc.
- Compte les occurrences par segment

```python
score_transcription = nombre_mots_clés / segment
```

#### 3. Calcul du score final

```python
score_final = (audio * 0.5) + (visuel * 0.35) + (transcription * 0.15)
```

Normalisation entre 0 et 1 pour chaque critère.

#### 4. Sélection intelligente

**Algorithme de sélection spatiale**:
```
1. Trier tous les segments par score décroissant
2. Prendre le meilleur segment
3. Exclure tous les segments à moins de 30 secondes
4. Répéter jusqu'à atteindre la durée cible
```

Cet algorithme garantit une distribution équitable des highlights dans la vidéo.

#### 5. Extension et montage

- Ajout de 2s avant et 3s après chaque segment (contexte)
- Tri chronologique
- Ajout de transitions (crossfade 0.5s)
- Export optimisé pour YouTube

### Exemple visuel

```
Timeline originale (4h):
[----silence----][ACTION!][----silence----][ACTION!][----silence----]
                    ↓                         ↓
Score:          0.2 0.9 0.3             0.1 0.8 0.2

Segments sélectionnés:
                [==Clip 1==]            [==Clip 2==]

Vidéo finale (15min):
[Intro][==Clip 1==][transition][==Clip 2==][...][Outro]
```

---

## ⚡ Optimisations

### Performance selon le hardware

| Configuration | Vidéo 4h | Whisper | Estimation |
|---------------|----------|---------|------------|
| **CPU seul** | ✓ | Base | ~45-60 min |
| **CPU + GPU** | ✓ | Base | ~25-35 min |
| **CPU + GPU** | ✓ | Medium | ~35-45 min |
| **Sans Whisper** | ✓ | - | ~15-20 min |

### Conseils d'optimisation

#### Pour traiter plus vite
```bash
python main.py -i stream.mp4 --no-whisper --gpu
```

#### Pour meilleure qualité
```bash
python main.py -i stream.mp4 --config config_quality.yaml --gpu
```

#### Pour économiser la RAM
```yaml
performance:
  audio_chunk_size: 30  # Plus petit = moins de RAM
```

### Cache intelligent

Le système met en cache les analyses:
```
.cache/
  └── analysis_abc123_def456.pkl  # Hash de la vidéo + config
```

Réexécuter avec la même vidéo/config = instantané!

Pour forcer une nouvelle analyse:
```bash
python main.py -i stream.mp4 --no-cache
```

---

## 📚 Exemples

### Exemple 1: Stream FPS classique

```bash
python main.py \
  --input valorant_stream.mp4 \
  --duration 15 \
  --quality 1080p \
  --output valorant_highlights.mp4
```

**Résultat**: 15 min de highlights avec kills, clutches, et réactions

### Exemple 2: Stream long avec intro/outro

```bash
python main.py \
  --input stream_8h.mp4 \
  --duration 25 \
  --intro branding_intro.mp4 \
  --outro subscribe_outro.mp4 \
  --gpu \
  --output best_of_stream.mp4
```

**Résultat**: 25 min avec intro/outro, traitement accéléré par GPU

### Exemple 3: Configuration personnalisée

```bash
python main.py \
  --input csgo_tournament.mp4 \
  --config examples/config_esport.yaml \
  --output tournament_highlights.mp4
```

**Résultat**: Highlights optimisés pour contenu esport

### Exemple 4: Traitement par lot

```bash
# Script bash pour traiter plusieurs VODs
for vod in vods/*.mp4; do
  output="highlights/$(basename "$vod" .mp4)_highlights.mp4"
  python main.py -i "$vod" -o "$output" -d 15
done
```

---

## 🔧 Dépannage

### Problème: "FFmpeg not found"

**Solution**:
```bash
# Vérifier l'installation
ffmpeg -version

# Si non installé, installer selon votre OS
# Ubuntu: sudo apt install ffmpeg
# MacOS: brew install ffmpeg
# Windows: télécharger depuis ffmpeg.org
```

### Problème: "Out of memory"

**Solutions**:
1. Réduire la taille des chunks:
   ```yaml
   performance:
     audio_chunk_size: 30
   ```

2. Désactiver Whisper:
   ```bash
   python main.py -i stream.mp4 --no-whisper
   ```

3. Fermer les autres applications

### Problème: "CUDA not available"

**Solutions**:
1. Vérifier l'installation CUDA:
   ```python
   import torch
   print(torch.cuda.is_available())
   ```

2. Installer PyTorch avec support CUDA:
   ```bash
   pip install torch --index-url https://download.pytorch.org/whl/cu118
   ```

3. Continuer sans GPU (plus lent mais fonctionnel):
   ```bash
   python main.py -i stream.mp4  # Sans --gpu
   ```

### Problème: "Whisper model not found"

**Solution**:
```bash
# Téléchargement manuel du modèle
python -c "import whisper; whisper.load_model('base')"
```

### Problème: Segments détectés de mauvaise qualité

**Solutions**:
1. Ajuster les seuils:
   ```yaml
   analysis:
     audio_intensity_threshold: 0.6  # Plus bas = plus sensible
   ```

2. Activer Whisper si désactivé

3. Augmenter la pondération audio:
   ```yaml
   analysis:
     score_weights:
       audio: 0.6
       visual: 0.3
       transcription: 0.1
   ```

### Problème: Export vidéo trop lent

**Solutions**:
1. Utiliser un preset plus rapide:
   ```yaml
   output:
     preset: fast  # ou veryfast
   ```

2. Activer le GPU:
   ```yaml
   output:
     codec: h264_nvenc  # NVIDIA
   ```

3. Réduire la qualité temporairement:
   ```yaml
   output:
     quality: 720p
     crf: 23
   ```

---

## 🤝 Contribution

Les contributions sont les bienvenues! Voici comment contribuer:

### Signaler un bug

1. Vérifier que le bug n'est pas déjà signalé dans les [Issues](https://github.com/votre-username/StreamHighlightAI/issues)
2. Créer une nouvelle issue avec:
   - Description détaillée
   - Étapes pour reproduire
   - Configuration système
   - Logs d'erreur

### Proposer une fonctionnalité

1. Créer une issue avec le tag `enhancement`
2. Décrire la fonctionnalité et son utilité
3. Discuter de l'implémentation

### Soumettre du code

1. Fork le projet
2. Créer une branche: `git checkout -b feature/amazing-feature`
3. Commit: `git commit -m 'Add amazing feature'`
4. Push: `git push origin feature/amazing-feature`
5. Ouvrir une Pull Request

### Standards de code

- Suivre PEP 8
- Ajouter des docstrings
- Tester avant de soumettre
- Commenter les parties complexes

---

## 📊 Roadmap

### Version 1.1 (en cours)
- [ ] Interface graphique (GUI)
- [ ] Support de plus de formats vidéo
- [ ] Détection de visage (focus sur le streamer)
- [ ] Templates de montage prédéfinis

### Version 1.2 (planifiée)
- [ ] Support multi-langues pour Whisper
- [ ] Détection d'événements spécifiques par jeu
- [ ] Export direct vers YouTube/Twitch
- [ ] Génération automatique de titres/descriptions

### Version 2.0 (future)
- [ ] Analyse de sentiment avancée
- [ ] Détection de moments drôles vs moments épiques
- [ ] Support streaming en temps réel
- [ ] Clustering de moments similaires

---

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

```
MIT License

Copyright (c) 2024 StreamHighlightAI Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software...
```

---

## 🙏 Remerciements

- [Whisper](https://github.com/openai/whisper) par OpenAI pour la transcription audio
- [MoviePy](https://github.com/Zulko/moviepy) pour le montage vidéo
- [FFmpeg](https://ffmpeg.org/) pour le traitement multimédia
- [Librosa](https://librosa.org/) pour l'analyse audio
- La communauté open-source pour tous les outils utilisés

---

## 📞 Contact & Support

- **Issues**: [GitHub Issues](https://github.com/votre-username/StreamHighlightAI/issues)
- **Discussions**: [GitHub Discussions](https://github.com/votre-username/StreamHighlightAI/discussions)
- **Email**: streamhighlightai@example.com
- **Discord**: [Rejoindre la communauté](#)

---

## ⭐ Star History

Si ce projet vous aide, n'oubliez pas de lui donner une étoile!

[![Star History Chart](https://api.star-history.com/svg?repos=votre-username/StreamHighlightAI&type=Date)](https://star-history.com/#votre-username/StreamHighlightAI&Date)

---

**Fait avec ❤️ pour la communauté gaming**
