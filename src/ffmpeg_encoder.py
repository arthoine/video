"""
Encodeur FFmpeg direct - Bypass MoviePy pour utiliser vraiment h264_nvenc

MoviePy peut ignorer le codec h264_nvenc et utiliser libx264 à la place.
Ce module utilise FFmpeg directement pour garantir l'utilisation du GPU.
"""

import subprocess
import logging
from pathlib import Path
from typing import List
from tqdm import tqdm
import tempfile
import os

logger = logging.getLogger(__name__)


def encode_with_ffmpeg_direct(
    input_clips: List,
    output_path: str,
    fps: int,
    codec: str,
    preset: str,
    cq: str,
    audio_codec: str = 'aac',
    use_gpu: bool = True
) -> bool:
    """
    Encode la vidéo finale en utilisant FFmpeg directement (bypass MoviePy).

    Args:
        input_clips: Liste de clips MoviePy
        output_path: Chemin de sortie
        fps: Framerate
        codec: Codec vidéo (libx264 ou h264_nvenc)
        preset: Preset d'encodage
        cq: Constant quality
        audio_codec: Codec audio
        use_gpu: Utiliser le GPU si True

    Returns:
        True si succès, False sinon
    """

    logger.info("=" * 70)
    logger.info("🚀 ENCODAGE FFMPEG DIRECT (Bypass MoviePy)")
    logger.info("=" * 70)

    # Étape 1: Exporter les clips en fichiers temporaires
    temp_dir = tempfile.mkdtemp(prefix="streamhighlight_")
    temp_files = []

    try:
        logger.info(f"Export temporaire des {len(input_clips)} clips...")

        for i, clip in enumerate(tqdm(input_clips, desc="Export clips")):
            temp_file = os.path.join(temp_dir, f"clip_{i:04d}.mp4")

            # Export avec MoviePy (rapide, pas de ré-encodage)
            clip.write_videofile(
                temp_file,
                codec='libx264',  # Codec temporaire rapide
                preset='ultrafast',  # Très rapide
                audio_codec=audio_codec,
                verbose=False,
                logger=None
            )

            temp_files.append(temp_file)

        logger.info(f"✓ {len(temp_files)} clips exportés")

        # Étape 2: Créer fichier de concaténation pour FFmpeg
        concat_file = os.path.join(temp_dir, "concat.txt")
        with open(concat_file, 'w') as f:
            for temp_file in temp_files:
                # FFmpeg concat demande des chemins absolus ou relatifs escapés
                abs_path = os.path.abspath(temp_file).replace('\\', '/')
                f.write(f"file '{abs_path}'\n")

        logger.info(f"✓ Fichier de concaténation créé")

        # Étape 3: Encoder avec FFmpeg directement
        logger.info("=" * 70)

        if use_gpu and codec == 'h264_nvenc':
            logger.info("🎮 ENCODAGE GPU AVEC h264_nvenc")
            actual_codec = 'h264_nvenc'
            codec_params = ['-cq', cq]  # NVENC utilise -cq
        else:
            logger.info("⚠️  ENCODAGE CPU AVEC libx264")
            actual_codec = 'libx264'
            codec_params = ['-crf', cq]  # x264 utilise -crf

        ffmpeg_cmd = [
            'ffmpeg',
            '-f', 'concat',
            '-safe', '0',
            '-i', concat_file,
            '-c:v', actual_codec,
            '-preset', preset,
        ] + codec_params + [
            '-pix_fmt', 'yuv420p',
            '-r', str(fps),
            '-c:a', audio_codec,
            '-b:a', '192k',
            '-ar', '48000',
            '-movflags', '+faststart',
            '-y',  # Overwrite
            output_path
        ]

        logger.info("Commande FFmpeg:")
        logger.info(f"  {' '.join(ffmpeg_cmd)}")
        logger.info("=" * 70)

        # Exécuter FFmpeg
        logger.info("Encodage en cours...")
        result = subprocess.run(
            ffmpeg_cmd,
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            logger.info("✅ ENCODAGE RÉUSSI!")
            logger.info(f"   Fichier créé: {output_path}")

            # Vérifier la taille
            if os.path.exists(output_path):
                size_mb = os.path.getsize(output_path) / (1024 * 1024)
                logger.info(f"   Taille: {size_mb:.1f} MB")

            return True
        else:
            logger.error("❌ ENCODAGE ÉCHOUÉ")
            logger.error(f"Erreur FFmpeg:\n{result.stderr}")
            return False

    except Exception as e:
        logger.error(f"❌ Erreur: {e}")
        return False

    finally:
        # Nettoyage
        try:
            logger.info("Nettoyage des fichiers temporaires...")
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            if os.path.exists(concat_file):
                os.remove(concat_file)
            os.rmdir(temp_dir)
            logger.info("✓ Nettoyage terminé")
        except Exception as e:
            logger.warning(f"Erreur lors du nettoyage: {e}")
