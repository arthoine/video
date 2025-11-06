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
from src.ffmpeg_encoder import encode_with_ffmpeg_direct


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

        # Paramètres de fusion de segments
        self.merge_consecutive = config.get('editing', {}).get('merge_consecutive_segments', True)
        self.merge_max_gap = config.get('editing', {}).get('merge_max_gap', 10)
        self.merge_min_score = config.get('editing', {}).get('merge_min_score', 0.25)

        # Paramètres d'export
        self.quality = config.get('output', {}).get('quality', '1080p')
        self.fps = config.get('output', {}).get('fps', 60)
        self.codec = config.get('output', {}).get('codec', 'libx264')
        self.audio_codec = config.get('output', {}).get('audio_codec', 'aac')

        # Intro/Outro
        self.intro_path = config.get('output', {}).get('intro_path')
        self.outro_path = config.get('output', {}).get('outro_path')

        # GPU status
        self.use_gpu = config.get('performance', {}).get('use_gpu', False)
        if self.use_gpu:
            self.logger.info("🎮 Mode GPU activé pour l'encodage")
        else:
            self.logger.info("⚠️  Mode CPU (GPU désactivé) - L'encodage sera plus lent")

    def create_highlight_video(self, segments: List[VideoSegment]):
        """
        Crée la vidéo finale de highlights.

        Args:
            segments: Liste de segments triés par score (meilleurs en premier)
        """
        self.logger.info(f"Création de la vidéo de highlights (cible: {self.target_duration/60:.1f} min)")

        # Fusion des segments consécutifs AVANT la sélection
        # Cela permet de capturer des séquences d'action complètes
        if self.merge_consecutive:
            self.logger.info("🔗 Fusion des segments consécutifs activée")
            segments = self._merge_consecutive_segments(segments)

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

        # Export - Utiliser FFmpeg direct si GPU activé (plus fiable)
        use_gpu = self.config.get('performance', {}).get('use_gpu', False)
        use_direct_ffmpeg = use_gpu  # Utiliser FFmpeg direct si GPU pour éviter les problèmes MoviePy

        if use_direct_ffmpeg:
            self.logger.info("🚀 Utilisation de FFmpeg DIRECT (bypass MoviePy pour GPU)")
            self.logger.info(f"Export vers {self.output_path}...")

            # Déterminer les paramètres
            preset = self.config.get('output', {}).get('preset', 'hq')
            cq = str(self.config.get('output', {}).get('crf', 20))

            # Encoder directement avec FFmpeg
            success = encode_with_ffmpeg_direct(
                input_clips=all_clips,
                output_path=str(self.output_path),
                fps=self.fps,
                codec='h264_nvenc',
                preset=preset,
                cq=cq,
                audio_codec=self.audio_codec,
                use_gpu=True
            )

            if not success:
                self.logger.error("❌ Encodage FFmpeg direct a échoué")
                self.logger.info("Tentative avec MoviePy en fallback...")
                # Fallback sur MoviePy
                final_video = concatenate_videoclips(all_clips, method="compose")
                self._export_video(final_video)
                final_video.close()
        else:
            # Méthode classique MoviePy
            self.logger.info("Assemblage de la vidéo finale...")
            final_video = concatenate_videoclips(all_clips, method="compose")

            self.logger.info(f"Export vers {self.output_path}...")
            self._export_video(final_video)

            final_video.close()

        # Nettoyage
        video.close()
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

    def _merge_consecutive_segments(self, segments: List[VideoSegment]) -> List[VideoSegment]:
        """
        Fusionne les segments consécutifs ou proches pour capturer des séquences complètes.

        Algorithme:
        1. Trier par temps de début
        2. Pour chaque segment, vérifier si le suivant est proche (< merge_max_gap)
        3. Si oui et que le score est bon (> merge_min_score), fusionner
        4. Continuer jusqu'à ce qu'on trouve un gap trop grand ou un segment faible

        Cela permet de capturer des actions complètes comme:
        début du combat → 1v3 → looting
        """
        if not segments or not self.merge_consecutive:
            return segments

        # Trier par temps de début
        sorted_segments = sorted(segments, key=lambda s: s.start_time)
        merged = []

        i = 0
        while i < len(sorted_segments):
            current = sorted_segments[i]

            # Chercher tous les segments fusionnables avec celui-ci
            j = i + 1
            while j < len(sorted_segments):
                next_seg = sorted_segments[j]
                gap = next_seg.start_time - current.end_time

                # Conditions de fusion:
                # 1. Gap assez petit (< merge_max_gap)
                # 2. Score du segment suivant suffisant (> merge_min_score)
                if gap <= self.merge_max_gap and next_seg.score >= self.merge_min_score:
                    # Fusionner: étendre current jusqu'à la fin de next_seg
                    old_duration = current.duration
                    current.end_time = next_seg.end_time
                    current.duration = current.end_time - current.start_time
                    # Score moyen pondéré
                    current.score = (current.score * old_duration + next_seg.score * next_seg.duration) / current.duration
                    self.logger.debug(
                        f"Fusion: {current.start_time:.1f}s + {next_seg.start_time:.1f}s "
                        f"(gap={gap:.1f}s) → segment de {current.duration:.1f}s"
                    )
                    j += 1
                else:
                    break

            merged.append(current)
            i = j

        self.logger.info(
            f"Fusion: {len(sorted_segments)} segments → {len(merged)} segments fusionnés "
            f"(gain moyen: {len(sorted_segments)/max(len(merged),1):.1f}x)"
        )

        return merged

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
        # Lecture des paramètres depuis la config
        preset = self.config.get('output', {}).get('preset', 'medium')
        crf = str(self.config.get('output', {}).get('crf', 18))
        num_threads = self.config.get('performance', {}).get('num_threads', 0)

        # Détermination du codec (GPU ou CPU)
        codec = self.codec
        use_gpu = self.config.get('performance', {}).get('use_gpu', False)

        if use_gpu and self.codec == 'libx264':
            codec = 'h264_nvenc'  # NVIDIA
            # NVENC utilise des presets différents: fast, medium, slow, hq, bd, ll, llhq
            if preset not in ['fast', 'medium', 'slow', 'hq', 'bd', 'll', 'llhq', 'lossless']:
                preset = 'hq'  # High quality par défaut pour GPU

            # Vérifier le GPU
            try:
                import torch
                if torch.cuda.is_available():
                    gpu_name = torch.cuda.get_device_name(0)
                    self.logger.info(f"🎮 Utilisation de l'accélération GPU NVIDIA: {gpu_name}")
                    self.logger.info(f"   Codec: h264_nvenc | Preset: {preset} | CQ: {crf}")
                else:
                    self.logger.warning("⚠️  GPU demandé mais CUDA non disponible, fallback sur CPU")
                    codec = self.codec  # Revenir au codec CPU
            except ImportError:
                self.logger.warning("⚠️  PyTorch non disponible, impossible de vérifier le GPU")
                # On garde h264_nvenc et on laisse FFmpeg gérer

        # Paramètres FFmpeg optimisés
        # IMPORTANT: On doit mettre -c:v dans ffmpeg_params car MoviePy peut ignorer le paramètre codec=
        ffmpeg_params = []

        # FORCER le codec vidéo dans ffmpeg_params (MoviePy peut ignorer codec=)
        if codec == 'h264_nvenc':
            self.logger.info("=" * 70)
            self.logger.info("🎮 ENCODAGE GPU ACTIVÉ")
            self.logger.info("=" * 70)
            ffmpeg_params.extend(['-c:v', 'h264_nvenc'])  # FORCER h264_nvenc
            ffmpeg_params.extend(['-preset', preset])
            ffmpeg_params.extend(['-cq', crf])  # Constant Quality pour NVENC
            self.logger.info(f"Commande FFmpeg (GPU):")
            self.logger.info(f"  -c:v h264_nvenc -preset {preset} -cq {crf}")
        else:
            self.logger.info("⚠️  ENCODAGE CPU (pas de GPU)")
            ffmpeg_params.extend(['-c:v', codec])  # libx264 ou autre
            ffmpeg_params.extend(['-preset', preset])
            ffmpeg_params.extend(['-crf', crf])  # CRF pour x264
            self.logger.info(f"Commande FFmpeg (CPU):")
            self.logger.info(f"  -c:v {codec} -preset {preset} -crf {crf}")

        # Paramètres communs
        ffmpeg_params.extend([
            '-pix_fmt', 'yuv420p',  # Compatibilité maximale
            '-c:a', self.audio_codec,
            '-b:a', '192k',  # Bitrate audio
            '-ar', '48000',  # Sampling rate audio (standard YouTube)
            '-movflags', '+faststart',  # Optimisation streaming
        ])

        # Ajout du threading (pour CPU uniquement)
        if num_threads > 0 and codec != 'h264_nvenc':
            ffmpeg_params.extend(['-threads', str(num_threads)])

        self.logger.info(f"Paramètres FFmpeg complets:")
        self.logger.info(f"  {' '.join(ffmpeg_params)}")
        self.logger.info("=" * 70)

        # Export avec barre de progression
        # IMPORTANT: Ne PAS passer codec= car on le met déjà dans ffmpeg_params
        video.write_videofile(
            str(self.output_path),
            fps=self.fps,
            audio_codec=self.audio_codec,
            threads=num_threads if num_threads > 0 else None,
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
