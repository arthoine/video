#!/usr/bin/env python3
"""
StreamHighlightAI - Point d'entrée principal
Outil d'édition automatique de streams gaming avec IA locale
"""

import argparse
import sys
import logging
from pathlib import Path
import yaml

from src.analyzer import VideoAnalyzer
from src.editor import VideoEditor
from src.utils import setup_logging, validate_file, check_dependencies


def parse_arguments():
    """Parse les arguments de la ligne de commande."""
    parser = argparse.ArgumentParser(
        description="StreamHighlightAI - Édition automatique de streams gaming avec IA locale",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:
  python main.py --input stream.mp4 --duration 15 --output highlights.mp4
  python main.py -i stream.mp4 -d 20 -o highlights.mp4 --quality 1080p
  python main.py -i stream.mp4 --config custom_config.yaml
        """
    )

    # Arguments obligatoires
    parser.add_argument(
        '-i', '--input',
        type=str,
        required=True,
        help='Chemin vers la vidéo source (VOD de stream)'
    )

    parser.add_argument(
        '-o', '--output',
        type=str,
        default='highlights.mp4',
        help='Chemin de sortie pour la vidéo montée (défaut: highlights.mp4)'
    )

    # Arguments optionnels de configuration
    parser.add_argument(
        '-d', '--duration',
        type=int,
        default=15,
        help='Durée cible de la vidéo finale en minutes (défaut: 15)'
    )

    parser.add_argument(
        '-c', '--config',
        type=str,
        default='config.yaml',
        help='Fichier de configuration YAML (défaut: config.yaml)'
    )

    parser.add_argument(
        '--quality',
        type=str,
        choices=['720p', '1080p', '4k'],
        default='1080p',
        help='Qualité de sortie vidéo (défaut: 1080p)'
    )

    parser.add_argument(
        '--audio-threshold',
        type=float,
        help='Seuil de détection d\'intensité audio (remplace la valeur du config)'
    )

    parser.add_argument(
        '--no-whisper',
        action='store_true',
        help='Désactiver la transcription Whisper'
    )

    parser.add_argument(
        '--gpu',
        action='store_true',
        help='Activer l\'accélération GPU (CUDA) si disponible'
    )

    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='Désactiver le cache des analyses'
    )

    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Mode verbeux (affiche plus de logs)'
    )

    parser.add_argument(
        '--intro',
        type=str,
        help='Chemin vers une vidéo d\'intro à ajouter au début'
    )

    parser.add_argument(
        '--outro',
        type=str,
        help='Chemin vers une vidéo d\'outro à ajouter à la fin'
    )

    return parser.parse_args()


def load_config(config_path):
    """Charge le fichier de configuration YAML."""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        logging.info(f"Configuration chargée depuis {config_path}")
        return config
    except FileNotFoundError:
        logging.warning(f"Fichier de configuration {config_path} non trouvé, utilisation des valeurs par défaut")
        return {}
    except yaml.YAMLError as e:
        logging.error(f"Erreur lors du parsing du fichier YAML: {e}")
        sys.exit(1)


def merge_config(config, args):
    """Fusionne la configuration YAML avec les arguments CLI (CLI prioritaire)."""
    # Les arguments CLI écrasent les valeurs du config
    if args.duration:
        config.setdefault('output', {})['target_duration_minutes'] = args.duration

    if args.quality:
        config.setdefault('output', {})['quality'] = args.quality

    if args.audio_threshold is not None:
        config.setdefault('analysis', {})['audio_intensity_threshold'] = args.audio_threshold

    if args.no_whisper:
        config.setdefault('analysis', {})['enable_whisper'] = False

    if args.gpu:
        config.setdefault('performance', {})['use_gpu'] = True

    if args.no_cache:
        config.setdefault('performance', {})['use_cache'] = False

    if args.intro:
        config.setdefault('output', {})['intro_path'] = args.intro

    if args.outro:
        config.setdefault('output', {})['outro_path'] = args.outro

    return config


def main():
    """Fonction principale du programme."""
    # Parse les arguments
    args = parse_arguments()

    # Configure les logs
    log_level = logging.DEBUG if args.verbose else logging.INFO
    setup_logging(log_level)

    logging.info("=" * 60)
    logging.info("StreamHighlightAI - Démarrage")
    logging.info("=" * 60)

    # Vérifie les dépendances système
    logging.info("Vérification des dépendances...")
    if not check_dependencies():
        logging.error("Dépendances manquantes. Voir les logs ci-dessus.")
        sys.exit(1)

    # Valide le fichier d'entrée
    if not validate_file(args.input):
        logging.error(f"Fichier d'entrée invalide ou introuvable: {args.input}")
        sys.exit(1)

    # Charge la configuration
    config = load_config(args.config)
    config = merge_config(config, args)

    # Affiche la configuration finale
    logging.info(f"Vidéo source: {args.input}")
    logging.info(f"Vidéo de sortie: {args.output}")
    logging.info(f"Durée cible: {config.get('output', {}).get('target_duration_minutes', 15)} minutes")
    logging.info(f"Qualité: {config.get('output', {}).get('quality', '1080p')}")

    try:
        # Étape 1: Analyse de la vidéo
        logging.info("\n" + "=" * 60)
        logging.info("ÉTAPE 1/2: ANALYSE DE LA VIDÉO")
        logging.info("=" * 60)

        analyzer = VideoAnalyzer(args.input, config)
        highlights = analyzer.analyze()

        logging.info(f"\n✓ Analyse terminée: {len(highlights)} segments trouvés")

        # Étape 2: Montage de la vidéo
        logging.info("\n" + "=" * 60)
        logging.info("ÉTAPE 2/2: MONTAGE DE LA VIDÉO")
        logging.info("=" * 60)

        editor = VideoEditor(args.input, args.output, config)
        editor.create_highlight_video(highlights)

        logging.info("\n" + "=" * 60)
        logging.info("✓ TRAITEMENT TERMINÉ AVEC SUCCÈS")
        logging.info("=" * 60)
        logging.info(f"Vidéo finale créée: {args.output}")

        # Affiche des statistiques
        output_path = Path(args.output)
        if output_path.exists():
            size_mb = output_path.stat().st_size / (1024 * 1024)
            logging.info(f"Taille du fichier: {size_mb:.2f} MB")

    except KeyboardInterrupt:
        logging.warning("\nTraitement interrompu par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        logging.error(f"\nErreur fatale: {e}", exc_info=args.verbose)
        sys.exit(1)


if __name__ == "__main__":
    main()
