"""
Éditeur vidéo pour assembler les highlights détectés

Ce module gère le montage automatique de la vidéo finale:
- Sélection intelligente des meilleurs segments
- Filtrage spatial (évite les segments trop rapprochés)
- Extension des segments pour le contexte
- Ajout de transitions
- Export optimisé pour YouTube
"""

import logging
from pathlib import Path
from typing import List, Dict
from tqdm import tqdm

from moviepy.editor import (
    VideoFileClip, concatenate_videoclips,
    CompositeVideoClip, transfx
)

from src.analyzer import VideoSegment


class VideoEditor:
    """Éditeur pour créer la vidéo finale de highlights."""

    def __init__(self, input_path: str, output_path: str, config: Dict):
        self.input_path = Path(input_path)
        self.output_path = Path(output_path)
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Paramètres de montage
        self.target_duration = config.get('output', {}).get('target_duration_minutes', 15) * 60
        self.min_gap = config.get('editing', {}).get('min_gap_between_segments', 30)
        self.context_before = config.get('editing', {}).get('context_before_seconds', 2)
        self.context_after = config.get('editing', {}).get('context_after_seconds', 3)
        self.min_segment_duration = config.get('editing', {}).get('min_segment_duration', 5)
        self.max_segment_duration = config.get('editing', {}).get('max_segment_duration', 30)

        # Paramètres d'export
        self.quality = config.get('output', {}).get('quality', '1080p')
        self.fps = config.get('output', {}).get('fps', 60)
        self.codec = config.get('output', {}).get('codec', 'libx264')
        self.audio_codec = config.get('output', {}).get('audio_codec', 'aac')

        # Intro/Outro
        self.intro_path = config.get('output', {}).get('intro_path')
        self.outro_path = config.get('output', {}).get('outro_path')

    def create_highlight_video(self, segments: List[VideoSegment]):
        """
        Crée la vidéo finale de highlights.

        Args:
            segments: Liste de segments triés par score (meilleurs en premier)
        """
        self.logger.info(f"Création de la vidéo de highlights (cible: {self.target_duration/60:.1f} min)")

        # Sélection des meilleurs segments
        selected_segments = self._select_best_segments(segments)
        self.logger.info(f"✓ {len(selected_segments)} segments sélectionnés")

        # Extension des segments pour le contexte
        self._extend_segments(selected_segments)

        # Tri chronologique
        selected_segments.sort(key=lambda s: s.start_time)

        # Chargement de la vidéo source
        self.logger.info("Chargement de la vidéo source...")
        video = VideoFileClip(str(self.input_path))

        # Extraction des clips
        self.logger.info("Extraction des clips...")
        clips = self._extract_clips(video, selected_segments)

        # Ajout de l'intro/outro
        all_clips = []

        if self.intro_path:
            all_clips.append(self._load_intro_outro(self.intro_path, "intro"))

        all_clips.extend(clips)

        if self.outro_path:
            all_clips.append(self._load_intro_outro(self.outro_path, "outro"))

        # Assemblage des clips
        self.logger.info("Assemblage de la vidéo finale...")
        final_video = concatenate_videoclips(all_clips, method="compose")

        # Export
        self.logger.info(f"Export vers {self.output_path}...")
        self._export_video(final_video)

        # Nettoyage
        video.close()
        final_video.close()
        for clip in clips:
            clip.close()

        self.logger.info("✓ Vidéo créée avec succès!")

    def _select_best_segments(self, segments: List[VideoSegment]) -> List[VideoSegment]:
        """
        Sélectionne les meilleurs segments en respectant les contraintes.

        Algorithme:
        1. Trier par score décroissant
        2. Prendre le meilleur segment
        3. Exclure tous les segments à moins de min_gap secondes
        4. Répéter jusqu'à atteindre la durée cible
        """
        selected = []
        total_duration = 0
        excluded_ranges = []

        for segment in segments:
            # Vérifie si le segment est dans une zone exclue
            is_excluded = False
            for excluded_start, excluded_end in excluded_ranges:
                if not (segment.end_time < excluded_start or segment.start_time > excluded_end):
                    is_excluded = True
                    break

            if is_excluded:
                continue

            # Vérifie les contraintes de durée
            segment_duration = segment.duration
            if segment_duration < self.min_segment_duration:
                continue
            if segment_duration > self.max_segment_duration:
                # Tronquer le segment
                segment.end_time = segment.start_time + self.max_segment_duration
                segment.duration = self.max_segment_duration

            # Ajoute le segment
            selected.append(segment)
            total_duration += segment.duration

            # Ajoute la zone d'exclusion
            excluded_ranges.append((
                segment.start_time - self.min_gap,
                segment.end_time + self.min_gap
            ))

            # Vérifie si on a atteint la durée cible
            if total_duration >= self.target_duration:
                break

        self.logger.info(f"Durée totale des segments: {total_duration/60:.1f} min")
        return selected

    def _extend_segments(self, segments: List[VideoSegment]):
        """Étend chaque segment pour ajouter du contexte avant/après."""
        for segment in segments:
            segment.extend(self.context_before, self.context_after)

    def _extract_clips(self, video: VideoFileClip, segments: List[VideoSegment]) -> List[VideoFileClip]:
        """Extrait les clips vidéo correspondant aux segments."""
        clips = []
        transition_duration = self.config.get('editing', {}).get('transition_duration', 0.5)
        use_transitions = self.config.get('editing', {}).get('use_transitions', True)

        for i, segment in enumerate(tqdm(segments, desc="Extraction")):
            # Extraction du clip
            clip = video.subclip(segment.start_time, segment.end_time)

            # Ajout de transitions (fade in/out) sauf pour le premier et dernier
            if use_transitions:
                if i > 0:
                    clip = clip.crossfadein(transition_duration)
                if i < len(segments) - 1:
                    clip = clip.crossfadeout(transition_duration)

            clips.append(clip)

        return clips

    def _load_intro_outro(self, path: str, name: str) -> VideoFileClip:
        """Charge une vidéo d'intro ou d'outro."""
        try:
            self.logger.info(f"Chargement de {name}: {path}")
            clip = VideoFileClip(path)

            # Ajuste la résolution si nécessaire
            target_height = self._get_target_height()
            if clip.h != target_height:
                clip = clip.resize(height=target_height)

            return clip
        except Exception as e:
            self.logger.error(f"Erreur lors du chargement de {name}: {e}")
            return None

    def _get_target_height(self) -> int:
        """Retourne la hauteur cible selon la qualité."""
        quality_map = {
            '720p': 720,
            '1080p': 1080,
            '4k': 2160
        }
        return quality_map.get(self.quality, 1080)

    def _export_video(self, video: VideoFileClip):
        """Exporte la vidéo finale avec les paramètres optimisés."""
        # Paramètres FFmpeg optimisés pour YouTube
        ffmpeg_params = [
            '-c:v', self.codec,
            '-preset', 'medium',  # Balance entre vitesse et qualité
            '-crf', '18',  # Qualité (18 = haute qualité, 23 = défaut)
            '-pix_fmt', 'yuv420p',  # Compatibilité maximale
            '-c:a', self.audio_codec,
            '-b:a', '192k',  # Bitrate audio
            '-ar', '48000',  # Sampling rate audio (standard YouTube)
            '-movflags', '+faststart',  # Optimisation streaming
        ]

        # Ajout de l'accélération GPU si disponible
        if self.config.get('performance', {}).get('use_gpu', False):
            # Détection du codec GPU approprié
            if self.codec == 'libx264':
                ffmpeg_params[1] = 'h264_nvenc'  # NVIDIA
            self.logger.info("Utilisation de l'accélération GPU pour l'export")

        # Export avec barre de progression
        video.write_videofile(
            str(self.output_path),
            fps=self.fps,
            codec=self.codec,
            audio_codec=self.audio_codec,
            ffmpeg_params=ffmpeg_params,
            verbose=False,
            logger='bar'
        )


class TransitionEffect:
    """Effets de transition personnalisés."""

    @staticmethod
    def smooth_cut(clip1: VideoFileClip, clip2: VideoFileClip, duration: float = 0.3):
        """
        Transition cut avec fade rapide.
        Plus rapide et dynamique qu'un crossfade pour du contenu gaming.
        """
        clip1 = clip1.crossfadeout(duration)
        clip2 = clip2.crossfadein(duration)
        return concatenate_videoclips([clip1, clip2], method="compose")

    @staticmethod
    def flash_transition(clip1: VideoFileClip, clip2: VideoFileClip):
        """
        Transition flash blanc (effet "impact").
        Utile pour les moments très intenses.
        """
        # Note: Implémentation simplifiée - nécessite plus de travail pour un vrai flash
        return concatenate_videoclips([
            clip1.crossfadeout(0.1),
            clip2.crossfadein(0.1)
        ], method="compose")
