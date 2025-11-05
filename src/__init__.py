"""
StreamHighlightAI - Package principal
Outil d'édition automatique de streams gaming avec IA locale
"""

__version__ = "1.0.0"
__author__ = "StreamHighlightAI Contributors"

from src.analyzer import VideoAnalyzer, VideoSegment
from src.editor import VideoEditor
from src.utils import setup_logging, validate_file, check_dependencies

__all__ = [
    'VideoAnalyzer',
    'VideoSegment',
    'VideoEditor',
    'setup_logging',
    'validate_file',
    'check_dependencies'
]
