"""
Analyseur vidéo pour détecter les temps forts dans les streams gaming

Ce module implémente un système d'analyse multi-critères pour identifier
automatiquement les moments les plus intéressants d'un stream:

ALGORITHME DE DÉTECTION:
1. Découpage de la vidéo en segments de 5 secondes
2. Pour chaque segment, calcul d'un score basé sur:
   - Intensité audio (pics sonores = kills, réactions)
   - Variations de scène (action rapide = changements visuels fréquents)
   - Transcription vocale (détection de mots-clés comme "wow", "oh", etc.)
3. Normalisation et pondération des scores
4. Sélection des N meilleurs segments selon le score final
5. Filtrage spatial (évite les segments trop rapprochés)
"""

import logging
import numpy as np
import cv2
from pathlib import Path
import pickle
import hashlib
import tempfile
import os
from tqdm import tqdm
from typing import List, Dict, Tuple, Optional

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logging.warning("Whisper non disponible - transcription désactivée")

import librosa
from scipy import signal
from moviepy.editor import VideoFileClip

# Import analyseur LLM pour compréhension sémantique
from src.llm_analyzer import LLMAnalyzer, SemanticAnalysis


class VideoSegment:
    """Représente un segment vidéo avec son score d'intensité."""

    def __init__(self, start_time: float, end_time: float, score: float, metadata: Dict = None):
        self.start_time = start_time
        self.end_time = end_time
        self.score = score
        self.duration = end_time - start_time
        self.metadata = metadata or {}

    def __repr__(self):
        return f"Segment({self.start_time:.1f}s-{self.end_time:.1f}s, score={self.score:.3f})"

    def extend(self, before_seconds: float = 2.0, after_seconds: float = 3.0):
        """Étend le segment pour ajouter du contexte avant/après."""
        self.start_time = max(0, self.start_time - before_seconds)
        self.end_time += after_seconds
        self.duration = self.end_time - self.start_time


class VideoAnalyzer:
    """Analyseur principal pour détecter les temps forts."""

    def __init__(self, video_path: str, config: Dict):
        self.video_path = Path(video_path)
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Paramètres d'analyse
        self.segment_duration = config.get('analysis', {}).get('segment_duration_seconds', 5)
        self.audio_threshold = config.get('analysis', {}).get('audio_intensity_threshold', 0.7)
        self.scene_threshold = config.get('analysis', {}).get('scene_change_threshold', 30.0)
        self.use_whisper = config.get('analysis', {}).get('enable_whisper', True)
        self.use_cache = config.get('performance', {}).get('use_cache', True)
        self.use_gpu = config.get('performance', {}).get('use_gpu', False)

        # Log GPU status
        if self.use_gpu:
            self.logger.info("🎮 Mode GPU activé pour l'analyse")
        else:
            self.logger.info("⚠️  Mode CPU (GPU désactivé) - Le traitement sera plus lent")

        # Chargement du modèle Whisper si activé
        self.whisper_model = None
        if self.use_whisper and WHISPER_AVAILABLE:
            self._load_whisper_model()

        # Initialisation analyseur LLM (LLaVA) pour compréhension sémantique
        self.llm_analyzer = LLMAnalyzer(config)
        if self.llm_analyzer.enabled:
            self.logger.info("🧠 Analyseur sémantique LLaVA activé")

    def _load_whisper_model(self):
        """Charge le modèle Whisper pour la transcription audio."""
        try:
            model_size = self.config.get('analysis', {}).get('whisper_model', 'base')
            device = 'cuda' if self.use_gpu else 'cpu'

            if device == 'cuda':
                # Vérifier que CUDA est vraiment disponible
                try:
                    import torch
                    if not torch.cuda.is_available():
                        self.logger.warning("⚠️  GPU demandé mais CUDA non disponible, utilisation du CPU")
                        device = 'cpu'
                    else:
                        gpu_name = torch.cuda.get_device_name(0)
                        self.logger.info(f"🎮 Chargement Whisper '{model_size}' sur GPU: {gpu_name}")
                except ImportError:
                    self.logger.warning("⚠️  PyTorch non disponible, utilisation du CPU pour Whisper")
                    device = 'cpu'

            if device == 'cpu':
                self.logger.info(f"Chargement du modèle Whisper '{model_size}' sur CPU...")

            self.whisper_model = whisper.load_model(model_size, device=device)
            self.logger.info("✓ Modèle Whisper chargé")
        except Exception as e:
            self.logger.warning(f"Impossible de charger Whisper: {e}")
            self.whisper_model = None

    def _get_cache_path(self) -> Path:
        """Génère un chemin de cache unique basé sur le fichier et la config."""
        # Hash du fichier + config pour invalidation automatique
        file_hash = hashlib.md5(str(self.video_path).encode()).hexdigest()[:8]
        config_hash = hashlib.md5(str(self.config).encode()).hexdigest()[:8]
        cache_dir = Path('.cache')
        cache_dir.mkdir(exist_ok=True)
        return cache_dir / f"analysis_{file_hash}_{config_hash}.pkl"

    def _load_from_cache(self) -> List[VideoSegment]:
        """Tente de charger l'analyse depuis le cache."""
        if not self.use_cache:
            return None

        cache_path = self._get_cache_path()
        if cache_path.exists():
            try:
                with open(cache_path, 'rb') as f:
                    segments = pickle.load(f)
                self.logger.info(f"✓ Analyse chargée depuis le cache ({len(segments)} segments)")
                return segments
            except Exception as e:
                self.logger.warning(f"Erreur lors du chargement du cache: {e}")
        return None

    def _save_to_cache(self, segments: List[VideoSegment]):
        """Sauvegarde l'analyse dans le cache."""
        if not self.use_cache:
            return

        cache_path = self._get_cache_path()
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(segments, f)
            self.logger.info(f"✓ Analyse sauvegardée dans le cache")
        except Exception as e:
            self.logger.warning(f"Erreur lors de la sauvegarde du cache: {e}")

    def analyze(self) -> List[VideoSegment]:
        """
        Analyse complète de la vidéo pour détecter les temps forts.

        Returns:
            Liste de VideoSegment triés par score décroissant
        """
        # Vérifie le cache
        cached_segments = self._load_from_cache()
        if cached_segments:
            return cached_segments

        self.logger.info("Début de l'analyse vidéo...")

        # Chargement de la vidéo
        video = VideoFileClip(str(self.video_path))
        duration = video.duration
        self.logger.info(f"Vidéo: {duration/60:.1f} minutes ({duration:.0f}s)")

        # Découpage en segments
        segments = self._create_segments(duration)
        self.logger.info(f"Analyse de {len(segments)} segments de {self.segment_duration}s")

        # Détection mode LLaVA pur (100% semantic)
        llava_weights = self.config.get('analysis', {}).get('score_weights_llava', {})
        semantic_weight = llava_weights.get('semantic', 0.5)
        llava_pure_mode = self.llm_analyzer.enabled and semantic_weight >= 0.99

        # Analyse sémantique avec LLaVA (si activé)
        semantic_analyses = None
        if self.llm_analyzer.enabled:
            self.logger.info("🧠 Analyse sémantique LLaVA...")
            semantic_analyses = self._analyze_semantic(video, segments)

        # Mode LLaVA pur : skip audio/visual/transcription
        if llava_pure_mode:
            self.logger.info("🎯 MODE LLAVA PUR activé (semantic=100%)")
            self.logger.info("   ⏩ Audio/Visual/Transcription DÉSACTIVÉS (économie de temps)")
            audio_scores = np.zeros(len(segments))
            visual_scores = np.zeros(len(segments))
            transcription_scores = None
        else:
            # Analyse audio
            self.logger.info("Analyse audio (intensité et pics sonores)...")
            audio_scores = self._analyze_audio(video)

            # Analyse visuelle
            self.logger.info("Analyse visuelle (changements de scène)...")
            visual_scores = self._analyze_visual(video)

            # Transcription audio (optionnel)
            transcription_scores = None
            if self.whisper_model:
                self.logger.info("Transcription audio avec Whisper...")
                transcription_scores = self._analyze_transcription(video)

        # Combinaison des scores
        self.logger.info("Calcul des scores finaux...")
        final_segments = self._combine_scores(segments, audio_scores, visual_scores,
                                              transcription_scores, semantic_analyses)

        # Tri par score décroissant
        final_segments.sort(key=lambda s: s.score, reverse=True)

        # Sauvegarde dans le cache
        self._save_to_cache(final_segments)

        video.close()
        return final_segments

    def _create_segments(self, duration: float) -> List[VideoSegment]:
        """Découpe la vidéo en segments réguliers."""
        segments = []
        current_time = 0

        while current_time < duration:
            end_time = min(current_time + self.segment_duration, duration)
            segments.append(VideoSegment(current_time, end_time, 0.0))
            current_time = end_time

        return segments

    def _analyze_audio(self, video: VideoFileClip) -> np.ndarray:
        """
        Analyse l'intensité audio pour détecter les pics sonores.

        Principe: Les moments forts (kills, réactions) génèrent des pics d'intensité audio.
        """
        self.logger.info("Extraction de l'audio...")

        # Vérifier que la vidéo a de l'audio
        if video.audio is None:
            self.logger.warning("La vidéo n'a pas de piste audio, scores audio = 0")
            num_segments = int(video.duration / self.segment_duration) + 1
            return np.zeros(num_segments)

        try:
            # MÉTHODE 1: Essayer avec librosa directement (plus robuste que MoviePy)
            # librosa utilise FFmpeg en backend et gère mieux les codecs problématiques
            self.logger.info("🔧 Extraction audio avec librosa (méthode robuste)...")

            # librosa peut lire directement depuis le fichier vidéo
            audio_array, sample_rate = librosa.load(
                str(self.video_path),
                sr=22050,      # Sample rate
                mono=True,     # Convertir en mono automatiquement
                dtype=np.float32
            )

            self.logger.info(f"✓ Audio extrait: {len(audio_array)} samples à {sample_rate}Hz")

        except Exception as librosa_error:
            self.logger.warning(f"Librosa a échoué: {librosa_error}")
            self.logger.info("Tentative avec MoviePy en fallback...")

            try:
                # MÉTHODE 2 (fallback): MoviePy
                audio_array = video.audio.to_soundarray(fps=22050)

                # Vérifications
                if audio_array is None or len(audio_array) == 0:
                    raise ValueError("MoviePy a retourné un audio vide")

                # Convertir en numpy array si nécessaire
                if not isinstance(audio_array, np.ndarray):
                    audio_array = np.array(audio_array, dtype=np.float32)

                # Conversion mono si stéréo
                if len(audio_array.shape) > 1:
                    if audio_array.shape[1] > 1:
                        audio_array = audio_array.mean(axis=1, dtype=np.float32)
                    else:
                        audio_array = audio_array.flatten()

                self.logger.info(f"✓ Audio extrait via MoviePy (fallback)")

            except Exception as moviepy_error:
                self.logger.error(f"❌ MoviePy a aussi échoué: {moviepy_error}")
                self.logger.error("❌ IMPOSSIBLE D'EXTRAIRE L'AUDIO - Les deux méthodes ont échoué")
                self.logger.warning("⚠️  Analyse audio désactivée - Vérifiez le codec audio de votre vidéo")
                self.logger.warning("💡 Essayez de ré-encoder: ffmpeg -i input.mp4 -c:v copy -c:a aac output.mp4")
                num_segments = int(video.duration / self.segment_duration) + 1
                return np.zeros(num_segments)

        # Calcul de l'énergie RMS par segment
        segment_scores = []
        sample_rate = 22050
        samples_per_segment = int(self.segment_duration * sample_rate)

        for i in tqdm(range(0, len(audio_array), samples_per_segment), desc="Audio"):
            segment_audio = audio_array[i:i + samples_per_segment]

            if len(segment_audio) == 0:
                segment_scores.append(0.0)
                continue

            # RMS (Root Mean Square) - mesure de l'intensité sonore
            rms = np.sqrt(np.mean(segment_audio ** 2))

            # Détection des pics (variations soudaines = cris, explosions)
            peaks, _ = signal.find_peaks(np.abs(segment_audio), height=np.percentile(np.abs(segment_audio), 95))
            peak_density = len(peaks) / len(segment_audio)

            # Score combiné: intensité + densité de pics
            score = rms * 0.7 + peak_density * 0.3
            segment_scores.append(score)

        # Normalisation
        scores = np.array(segment_scores)
        if scores.max() > 0:
            scores = scores / scores.max()

        return scores

    def _analyze_visual(self, video: VideoFileClip) -> np.ndarray:
        """
        Analyse les changements de scène pour détecter l'action rapide.

        Principe: Une action intense génère des changements visuels fréquents.
        """
        segment_scores = []
        fps = video.fps
        frames_per_segment = int(self.segment_duration * fps)

        # Échantillonnage: on analyse 1 frame toutes les 0.5s pour économiser du temps
        sample_interval = int(fps * 0.5)

        prev_frame = None
        current_segment_diffs = []
        frame_count = 0

        for frame in tqdm(video.iter_frames(), desc="Visuel", total=int(video.duration * fps)):
            # Réduction de résolution pour accélérer
            small_frame = cv2.resize(frame, (160, 90))
            gray_frame = cv2.cvtColor(small_frame, cv2.COLOR_RGB2GRAY)

            if prev_frame is not None and frame_count % sample_interval == 0:
                # Différence entre frames successives
                diff = cv2.absdiff(gray_frame, prev_frame)
                diff_score = np.mean(diff)
                current_segment_diffs.append(diff_score)

            prev_frame = gray_frame.copy()
            frame_count += 1

            # Calcul du score par segment
            if frame_count % frames_per_segment == 0:
                if current_segment_diffs:
                    segment_score = np.mean(current_segment_diffs)
                    segment_scores.append(segment_score)
                else:
                    segment_scores.append(0.0)
                current_segment_diffs = []

        # Dernier segment partiel
        if current_segment_diffs:
            segment_scores.append(np.mean(current_segment_diffs))

        # Normalisation
        scores = np.array(segment_scores)
        if scores.max() > 0:
            scores = scores / scores.max()

        return scores

    def _analyze_transcription(self, video: VideoFileClip) -> np.ndarray:
        """
        Transcrit l'audio et détecte les réactions vocales fortes.

        Principe: Les mots-clés comme "wow", "oh", "nice", etc. indiquent des moments forts.
        """
        if not self.whisper_model:
            return None

        # Vérifier que la vidéo a de l'audio
        if video.audio is None:
            self.logger.warning("Pas d'audio disponible pour transcription")
            return None

        # Créer un fichier temporaire compatible multi-plateforme (Windows/Linux/Mac)
        temp_fd, temp_audio = tempfile.mkstemp(suffix='.wav', prefix='streamhighlight_')
        os.close(temp_fd)  # Fermer le file descriptor, on utilise juste le chemin

        try:
            # Extraction de l'audio temporaire
            self.logger.info(f"Export audio temporaire vers {temp_audio}...")
            video.audio.write_audiofile(temp_audio, fps=16000, verbose=False, logger=None)

            # Transcription avec Whisper
            self.logger.info("Transcription avec Whisper en cours...")
            result = self.whisper_model.transcribe(temp_audio, language='fr')

            # Mots-clés d'excitation (français + anglais)
            keywords = [
                'wow', 'oh', 'ah', 'putain', 'bordel', 'merde', 'ouais', 'yes',
                'nice', 'gg', 'lol', 'wtf', 'omg', 'incroyable', 'dingue',
                'mdr', 'chaud', 'easy', 'gg wp', 'ace', 'clutch'
            ]

            # Attribution des scores par segment
            segment_count = int(video.duration / self.segment_duration) + 1
            segment_scores = np.zeros(segment_count)

            for segment in result['segments']:
                text = segment['text'].lower()
                start_time = segment['start']
                segment_idx = int(start_time / self.segment_duration)

                # Compte les mots-clés
                keyword_count = sum(1 for keyword in keywords if keyword in text)
                if keyword_count > 0:
                    segment_scores[segment_idx] += keyword_count

            # Normalisation
            if segment_scores.max() > 0:
                segment_scores = segment_scores / segment_scores.max()

            self.logger.info(f"✓ Transcription terminée: {len(result['segments'])} segments transcrits")
            return segment_scores

        except Exception as e:
            self.logger.error(f"Erreur lors de la transcription: {e}")
            return None

        finally:
            # Nettoyage: supprimer le fichier temporaire
            try:
                if os.path.exists(temp_audio):
                    os.remove(temp_audio)
                    self.logger.debug(f"Fichier temporaire supprimé: {temp_audio}")
            except Exception as e:
                self.logger.warning(f"Impossible de supprimer le fichier temporaire: {e}")

    def _analyze_semantic(self, video: VideoFileClip,
                         segments: List[VideoSegment]) -> Optional[List[SemanticAnalysis]]:
        """
        Analyse sémantique des frames avec LLaVA pour comprendre le contexte.

        Au lieu de simplement mesurer des pics audio/visuels, cette méthode
        utilise un LLM vision pour COMPRENDRE ce qui se passe:
        - PvP combat vs PvE vs looting vs crafting
        - Intensité réelle de l'action
        - Position dans la séquence (start/peak/end)

        Args:
            video: Vidéo à analyser
            segments: Liste des segments à analyser

        Returns:
            Liste de SemanticAnalysis (ou None si LLaVA désactivé)
        """
        if not self.llm_analyzer.enabled:
            return None

        self.logger.info("🧠 Analyse sémantique avec LLaVA...")
        self.logger.info(f"   Extraction de {len(segments)} frames représentatives...")

        # Créer dossier temporaire pour les frames
        temp_dir = tempfile.mkdtemp(prefix='streamhighlight_frames_')
        frame_paths = []
        segment_indices = []

        try:
            # Extraire 1 frame au milieu de chaque segment
            for i, segment in enumerate(tqdm(segments, desc="Frames")):
                # Frame au milieu du segment
                frame_time = segment.start_time + (segment.duration / 2.0)

                # Extraire la frame
                frame = video.get_frame(frame_time)

                # Sauvegarder la frame
                frame_path = os.path.join(temp_dir, f"frame_{i:05d}.jpg")
                import PIL.Image
                PIL.Image.fromarray(frame).save(frame_path, quality=85)

                frame_paths.append(frame_path)
                segment_indices.append(i)

            # Analyser les frames avec LLaVA en batch
            semantic_analyses = self.llm_analyzer.analyze_frames_batch(
                frame_paths,
                segment_indices
            )

            # Log résumé
            if semantic_analyses:
                action_counts = {}
                for analysis in semantic_analyses:
                    if analysis:
                        action_type = analysis.action_type.value
                        action_counts[action_type] = action_counts.get(action_type, 0) + 1

                self.logger.info("📊 Résumé analyse sémantique:")
                for action, count in sorted(action_counts.items(), key=lambda x: x[1], reverse=True):
                    self.logger.info(f"   {action}: {count} segments")

            return semantic_analyses

        except Exception as e:
            self.logger.error(f"Erreur analyse sémantique: {e}")
            return None

        finally:
            # Nettoyage: supprimer les frames temporaires
            try:
                import shutil
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                    self.logger.debug(f"Frames temporaires supprimées: {temp_dir}")
            except Exception as e:
                self.logger.warning(f"Impossible de supprimer les frames temporaires: {e}")

    def _combine_scores(self, segments: List[VideoSegment], audio_scores: np.ndarray,
                       visual_scores: np.ndarray, transcription_scores: np.ndarray = None,
                       semantic_analyses: List[SemanticAnalysis] = None) -> List[VideoSegment]:
        """
        Combine les différents scores avec pondération.

        Pondération par défaut (sans LLaVA):
        - Audio: 50% (le plus important pour les FPS)
        - Visuel: 35% (action rapide)
        - Transcription: 15% (si disponible)

        Avec LLaVA activé:
        - Sémantique (LLaVA): 50% (compréhension contexte)
        - Audio: 25% (pics sonores)
        - Visuel: 20% (changements scène)
        - Transcription: 5% (mots-clés)
        """
        # Poids adaptés si LLaVA est activé
        if semantic_analyses is not None:
            weights = self.config.get('analysis', {}).get('score_weights_llava', {
                'semantic': 0.50,
                'audio': 0.25,
                'visual': 0.20,
                'transcription': 0.05
            })
            self.logger.info("🧠 Pondération avec LLaVA: semantic=50%, audio=25%, visual=20%, transcription=5%")
        else:
            weights = self.config.get('analysis', {}).get('score_weights', {
                'audio': 0.5,
                'visual': 0.35,
                'transcription': 0.15
            })

        # Détecter si l'audio est désactivé (tous les scores à 0)
        audio_disabled = np.all(audio_scores == 0)
        if audio_disabled:
            self.logger.warning("⚠️  Audio non disponible - Pondération ajustée:")
            self.logger.warning(f"   Visuel: {weights['visual']} → 60%")
            self.logger.warning(f"   Transcription: {weights['transcription']} → 40%")

        for i, segment in enumerate(segments):
            score = 0.0

            # Sémantique (LLaVA) - PRIORITAIRE si disponible
            if semantic_analyses is not None and i < len(semantic_analyses):
                analysis = semantic_analyses[i]
                if analysis:
                    semantic_score = analysis.to_score()
                    score += semantic_score * weights.get('semantic', 0.5)
                    segment.metadata['semantic_score'] = semantic_score
                    segment.metadata['action_type'] = analysis.action_type.value
                    segment.metadata['intensity'] = analysis.intensity.name
                    segment.metadata['enemy_count'] = analysis.enemy_count
                else:
                    segment.metadata['semantic_score'] = 0

            # Audio
            if i < len(audio_scores) and not audio_disabled:
                score += audio_scores[i] * weights['audio']

            # Visuel
            if i < len(visual_scores):
                if audio_disabled and semantic_analyses is None:
                    # Si pas d'audio et pas de LLaVA, donner plus de poids au visuel
                    score += visual_scores[i] * 0.6
                else:
                    score += visual_scores[i] * weights.get('visual', 0.35)

            # Transcription
            if transcription_scores is not None and i < len(transcription_scores):
                if audio_disabled and semantic_analyses is None:
                    # Si pas d'audio et pas de LLaVA, donner plus de poids à la transcription
                    score += transcription_scores[i] * 0.4
                else:
                    score += transcription_scores[i] * weights.get('transcription', 0.15)
            elif transcription_scores is None and not audio_disabled and semantic_analyses is None:
                # Redistribuer le poids de transcription sur audio/visuel (seulement si pas de LLaVA)
                redistrib = weights.get('transcription', 0.15) / (weights.get('audio', 0.5) + weights.get('visual', 0.35))
                if i < len(audio_scores):
                    score += audio_scores[i] * weights.get('audio', 0.5) * redistrib
                if i < len(visual_scores):
                    score += visual_scores[i] * weights.get('visual', 0.35) * redistrib

            segment.score = score
            segment.metadata['audio_score'] = audio_scores[i] if i < len(audio_scores) else 0
            segment.metadata['visual_score'] = visual_scores[i] if i < len(visual_scores) else 0

        # Filtrage des segments statiques (craft/base) basé sur score visuel
        min_visual_threshold = self.config.get('advanced', {}).get('min_visual_score', 0.0)
        if min_visual_threshold > 0:
            before_count = len(segments)
            segments = [s for s in segments if s.metadata.get('visual_score', 0) >= min_visual_threshold]
            filtered = before_count - len(segments)
            if filtered > 0:
                self.logger.info(f"🎯 Filtre statique: {filtered} segments retirés (visual_score < {min_visual_threshold})")

        return segments
