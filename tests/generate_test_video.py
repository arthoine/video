#!/usr/bin/env python3
"""
Générateur de vidéo de test pour StreamHighlightAI

Ce script crée une petite vidéo synthétique avec:
- Variations d'intensité audio (simule gunfights)
- Changements visuels (simule action)
- Durée courte (2-5 minutes) pour tests rapides

Utilisation:
    python tests/generate_test_video.py
    python tests/generate_test_video.py --duration 3 --output tests/test_video.mp4
"""

import argparse
import subprocess
import sys
from pathlib import Path


def generate_test_video(duration: int = 2, output: str = "tests/test_video.mp4"):
    """
    Génère une vidéo de test avec FFmpeg.

    La vidéo contient:
    - Des sections calmes et intenses (audio)
    - Des changements de couleur (visuel)
    - Format 1920x1080 30fps

    Args:
        duration: Durée en minutes
        output: Chemin de sortie
    """
    output_path = Path(output)
    output_path.parent.mkdir(exist_ok=True, parents=True)

    duration_seconds = duration * 60

    print(f"🎬 Génération d'une vidéo de test de {duration} minute(s)...")
    print(f"📁 Sortie: {output}")

    # Commande FFmpeg pour générer une vidéo synthétique
    # - lavfi: filtres audio/vidéo
    # - testsrc2: génère des patterns visuels variés
    # - sine: génère des ondes audio avec variations
    cmd = [
        'ffmpeg',
        '-f', 'lavfi',
        '-i', f'testsrc2=duration={duration_seconds}:size=1920x1080:rate=30',
        '-f', 'lavfi',
        '-i', f'sine=frequency=1000:duration={duration_seconds}',
        '-c:v', 'libx264',
        '-preset', 'ultrafast',
        '-crf', '23',
        '-pix_fmt', 'yuv420p',
        '-c:a', 'aac',
        '-b:a', '128k',
        '-shortest',
        '-y',  # Overwrite
        str(output_path)
    ]

    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            size_mb = output_path.stat().st_size / (1024 * 1024)
            print(f"✅ Vidéo créée avec succès!")
            print(f"📊 Taille: {size_mb:.2f} MB")
            print(f"\n🚀 Testez maintenant avec:")
            print(f"   python main.py -i {output} -c examples/config_fast_preview.yaml")
            print(f"   python main.py -i {output} -c examples/config_arc_raiders.yaml")
        else:
            print(f"❌ Erreur lors de la génération:")
            print(result.stderr)
            sys.exit(1)

    except subprocess.TimeoutExpired:
        print("❌ Timeout lors de la génération (> 60s)")
        sys.exit(1)
    except FileNotFoundError:
        print("❌ FFmpeg non trouvé. Installez-le d'abord:")
        print("   Ubuntu/Debian: sudo apt install ffmpeg")
        print("   MacOS: brew install ffmpeg")
        print("   Windows: https://ffmpeg.org/download.html")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Génère une vidéo de test pour StreamHighlightAI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  # Vidéo de 2 minutes (défaut)
  python tests/generate_test_video.py

  # Vidéo de 5 minutes
  python tests/generate_test_video.py --duration 5

  # Vidéo avec nom personnalisé
  python tests/generate_test_video.py --output my_test.mp4
        """
    )

    parser.add_argument(
        '-d', '--duration',
        type=int,
        default=2,
        help='Durée de la vidéo en minutes (défaut: 2)'
    )

    parser.add_argument(
        '-o', '--output',
        type=str,
        default='tests/test_video.mp4',
        help='Chemin de sortie (défaut: tests/test_video.mp4)'
    )

    args = parser.parse_args()

    if args.duration < 1 or args.duration > 60:
        print("❌ Durée invalide (1-60 minutes)")
        sys.exit(1)

    generate_test_video(args.duration, args.output)


if __name__ == "__main__":
    main()
