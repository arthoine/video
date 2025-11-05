"""
Fonctions utilitaires pour StreamHighlightAI

Contient des helpers pour:
- Configuration du logging
- Validation des fichiers
- Vérification des dépendances
- Formatage des durées
- Gestion des erreurs
"""

import logging
import sys
import subprocess
from pathlib import Path
from typing import Optional
import shutil


def setup_logging(level: int = logging.INFO):
    """
    Configure le système de logging avec un format personnalisé.

    Args:
        level: Niveau de logging (logging.DEBUG, INFO, WARNING, ERROR)
    """
    # Format avec couleurs pour terminal
    log_format = '%(asctime)s | %(levelname)-8s | %(message)s'
    date_format = '%H:%M:%S'

    # Configuration du logger racine
    logging.basicConfig(
        level=level,
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    # Réduction du bruit des librairies tierces
    logging.getLogger('moviepy').setLevel(logging.WARNING)
    logging.getLogger('PIL').setLevel(logging.WARNING)
    logging.getLogger('matplotlib').setLevel(logging.WARNING)


def validate_file(file_path: str) -> bool:
    """
    Valide qu'un fichier existe et est accessible.

    Args:
        file_path: Chemin vers le fichier

    Returns:
        True si le fichier est valide, False sinon
    """
    path = Path(file_path)

    if not path.exists():
        logging.error(f"Fichier introuvable: {file_path}")
        return False

    if not path.is_file():
        logging.error(f"Le chemin n'est pas un fichier: {file_path}")
        return False

    if path.stat().st_size == 0:
        logging.error(f"Le fichier est vide: {file_path}")
        return False

    # Vérification des extensions vidéo supportées
    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm'}
    if path.suffix.lower() not in video_extensions:
        logging.warning(f"Extension non standard détectée: {path.suffix}")
        logging.warning("Extensions supportées: " + ", ".join(video_extensions))

    return True


def check_dependencies() -> bool:
    """
    Vérifie que toutes les dépendances système sont installées.

    Returns:
        True si toutes les dépendances sont présentes, False sinon
    """
    all_ok = True

    # Vérification de FFmpeg
    if not check_ffmpeg():
        logging.error("❌ FFmpeg n'est pas installé ou introuvable dans PATH")
        logging.error("   Installation: https://ffmpeg.org/download.html")
        all_ok = False
    else:
        logging.info("✓ FFmpeg détecté")

    # Vérification de FFprobe (souvent inclus avec FFmpeg)
    if not shutil.which('ffprobe'):
        logging.warning("⚠ FFprobe non détecté (optionnel mais recommandé)")
    else:
        logging.info("✓ FFprobe détecté")

    # Vérification des modules Python critiques
    required_modules = [
        ('cv2', 'opencv-python'),
        ('numpy', 'numpy'),
        ('moviepy', 'moviepy'),
        ('librosa', 'librosa'),
        ('yaml', 'pyyaml'),
        ('tqdm', 'tqdm'),
    ]

    for module_name, package_name in required_modules:
        try:
            __import__(module_name)
            logging.info(f"✓ Module Python '{package_name}' détecté")
        except ImportError:
            logging.error(f"❌ Module Python '{package_name}' manquant")
            logging.error(f"   Installation: pip install {package_name}")
            all_ok = False

    # Vérification optionnelle de Whisper
    try:
        __import__('whisper')
        logging.info("✓ Module Python 'openai-whisper' détecté")
    except ImportError:
        logging.warning("⚠ Module 'openai-whisper' non installé (transcription désactivée)")
        logging.warning("   Installation: pip install openai-whisper")

    # Vérification CUDA (optionnel)
    try:
        import torch
        if torch.cuda.is_available():
            logging.info(f"✓ CUDA détecté ({torch.cuda.get_device_name(0)})")
        else:
            logging.info("ℹ CUDA non disponible (utilisation du CPU)")
    except ImportError:
        logging.info("ℹ PyTorch non installé (CUDA non disponible)")

    return all_ok


def check_ffmpeg() -> bool:
    """
    Vérifie que FFmpeg est installé et accessible.

    Returns:
        True si FFmpeg est disponible, False sinon
    """
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def format_duration(seconds: float) -> str:
    """
    Formate une durée en secondes vers un format lisible.

    Args:
        seconds: Durée en secondes

    Returns:
        Chaîne formatée (ex: "1h 23m 45s" ou "5m 30s")

    Examples:
        >>> format_duration(3665)
        '1h 1m 5s'
        >>> format_duration(125)
        '2m 5s'
        >>> format_duration(45)
        '45s'
    """
    if seconds < 60:
        return f"{int(seconds)}s"

    minutes = int(seconds // 60)
    secs = int(seconds % 60)

    if minutes < 60:
        return f"{minutes}m {secs}s"

    hours = minutes // 60
    minutes = minutes % 60
    return f"{hours}h {minutes}m {secs}s"


def format_filesize(size_bytes: int) -> str:
    """
    Formate une taille de fichier en octets vers un format lisible.

    Args:
        size_bytes: Taille en octets

    Returns:
        Chaîne formatée (ex: "1.5 GB" ou "234.5 MB")

    Examples:
        >>> format_filesize(1536000000)
        '1.43 GB'
        >>> format_filesize(2048000)
        '1.95 MB'
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def get_video_info(video_path: str) -> Optional[dict]:
    """
    Récupère les informations d'une vidéo via FFprobe.

    Args:
        video_path: Chemin vers la vidéo

    Returns:
        Dictionnaire avec les infos (durée, résolution, fps, codec)
        ou None en cas d'erreur
    """
    try:
        result = subprocess.run(
            [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                video_path
            ],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode != 0:
            return None

        import json
        data = json.loads(result.stdout)

        # Extraction des infos vidéo
        video_stream = next(
            (s for s in data.get('streams', []) if s.get('codec_type') == 'video'),
            None
        )

        if not video_stream:
            return None

        return {
            'duration': float(data.get('format', {}).get('duration', 0)),
            'width': video_stream.get('width'),
            'height': video_stream.get('height'),
            'fps': eval(video_stream.get('r_frame_rate', '0/1')),
            'codec': video_stream.get('codec_name'),
            'bitrate': int(data.get('format', {}).get('bit_rate', 0)),
            'size': int(data.get('format', {}).get('size', 0))
        }

    except Exception as e:
        logging.error(f"Erreur lors de la lecture des infos vidéo: {e}")
        return None


def estimate_processing_time(video_duration_seconds: float, use_whisper: bool = True) -> str:
    """
    Estime le temps de traitement approximatif.

    Args:
        video_duration_seconds: Durée de la vidéo en secondes
        use_whisper: Si la transcription Whisper est activée

    Returns:
        Estimation du temps de traitement (ex: "~15-20 minutes")
    """
    # Facteurs approximatifs (dépendent du hardware)
    # Analyse: ~0.3x la durée vidéo
    # Whisper: ~0.2x la durée vidéo (avec GPU) ou ~0.5x (CPU)
    # Montage: ~0.1x la durée vidéo

    video_minutes = video_duration_seconds / 60

    analysis_factor = 0.3
    whisper_factor = 0.2 if use_whisper else 0
    editing_factor = 0.1

    total_factor = analysis_factor + whisper_factor + editing_factor
    estimated_minutes = video_minutes * total_factor

    # Ajout d'une marge
    min_estimate = int(estimated_minutes * 0.8)
    max_estimate = int(estimated_minutes * 1.2)

    if min_estimate < 1:
        return "< 1 minute"
    elif min_estimate == max_estimate:
        return f"~{min_estimate} minutes"
    else:
        return f"~{min_estimate}-{max_estimate} minutes"


def create_output_directory(output_path: str):
    """
    Crée le répertoire de sortie si nécessaire.

    Args:
        output_path: Chemin du fichier de sortie
    """
    output_dir = Path(output_path).parent
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
        logging.info(f"Répertoire de sortie créé: {output_dir}")


class ProgressTracker:
    """Gestionnaire de progression pour les tâches longues."""

    def __init__(self, total_steps: int, description: str = "Traitement"):
        self.total_steps = total_steps
        self.current_step = 0
        self.description = description
        self.logger = logging.getLogger(__name__)

    def update(self, step: int = 1, message: str = ""):
        """Met à jour la progression."""
        self.current_step += step
        percentage = (self.current_step / self.total_steps) * 100

        log_message = f"{self.description}: {percentage:.1f}%"
        if message:
            log_message += f" - {message}"

        self.logger.info(log_message)

    def finish(self, message: str = "Terminé"):
        """Marque la progression comme terminée."""
        self.logger.info(f"{self.description}: 100% - {message}")
