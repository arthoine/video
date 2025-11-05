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
from tqdm import tqdm
from typing import List, Dict, Tuple

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    logging.warning("Whisper non disponible - transcription désactivée")

import librosa
from scipy import signal
from moviepy.editor import VideoFileClip


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

        # Chargement du modèle Whisper si activé
        self.whisper_model = None
        if self.use_whisper and WHISPER_AVAILABLE:
            self._load_whisper_model()

    def _load_whisper_model(self):
        """Charge le modèle Whisper pour la transcription audio."""
        try:
            model_size = self.config.get('analysis', {}).get('whisper_model', 'base')
            device = 'cuda' if self.use_gpu else 'cpu'
            self.logger.info(f"Chargement du modèle Whisper '{model_size}' sur {device}...")
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
        final_segments = self._combine_scores(segments, audio_scores, visual_scores, transcription_scores)

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
        audio_array = video.audio.to_soundarray(fps=22050)

        # Conversion mono si stéréo
        if len(audio_array.shape) > 1:
            audio_array = np.mean(audio_array, axis=1)

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

        # Extraction de l'audio temporaire
        temp_audio = '/tmp/temp_audio.wav'
        video.audio.write_audiofile(temp_audio, fps=16000, verbose=False, logger=None)

        try:
            # Transcription
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

            return segment_scores

        except Exception as e:
            self.logger.error(f"Erreur lors de la transcription: {e}")
            return None

    def _combine_scores(self, segments: List[VideoSegment], audio_scores: np.ndarray,
                       visual_scores: np.ndarray, transcription_scores: np.ndarray = None) -> List[VideoSegment]:
        """
        Combine les différents scores avec pondération.

        Pondération par défaut:
        - Audio: 50% (le plus important pour les FPS)
        - Visuel: 35% (action rapide)
        - Transcription: 15% (si disponible)
        """
        weights = self.config.get('analysis', {}).get('score_weights', {
            'audio': 0.5,
            'visual': 0.35,
            'transcription': 0.15
        })

        for i, segment in enumerate(segments):
            score = 0.0

            # Audio
            if i < len(audio_scores):
                score += audio_scores[i] * weights['audio']

            # Visuel
            if i < len(visual_scores):
                score += visual_scores[i] * weights['visual']

            # Transcription
            if transcription_scores is not None and i < len(transcription_scores):
                score += transcription_scores[i] * weights['transcription']
            elif transcription_scores is None:
                # Redistribuer le poids de transcription sur audio/visuel
                redistrib = weights['transcription'] / (weights['audio'] + weights['visual'])
                if i < len(audio_scores):
                    score += audio_scores[i] * weights['audio'] * redistrib
                if i < len(visual_scores):
                    score += visual_scores[i] * weights['visual'] * redistrib

            segment.score = score
            segment.metadata['audio_score'] = audio_scores[i] if i < len(audio_scores) else 0
            segment.metadata['visual_score'] = visual_scores[i] if i < len(visual_scores) else 0

        return segments
