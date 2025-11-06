"""
Analyseur LLM (LLaVA) pour compréhension sémantique des scènes de gameplay

Ce module utilise LLaVA (LLM + Vision) pour analyser les frames de gameplay
et comprendre réellement ce qui se passe, au lieu de juste mesurer des pics audio/visuels.

Analyse :
- Type d'action (PvP, PvE, Looting, Crafting, Calm)
- Intensité (High, Medium, Low)
- Contexte de séquence (Start, Peak, End)
- Nombre d'ennemis, armes, situation tactique
"""

import logging
import json
import time
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
import numpy as np

try:
    import ollama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    logging.warning("⚠️  Ollama non installé - LLaVA désactivé")


class ActionType(Enum):
    """Types d'actions détectables dans le gameplay."""
    PVP_COMBAT = "pvp_combat"      # Combat joueur vs joueur
    PVE_COMBAT = "pve_combat"      # Combat vs drones/IA
    LOOTING = "looting"            # Récupération items
    CRAFTING = "crafting"          # Crafting à la base
    MOVEMENT = "movement"          # Déplacement simple
    CALM = "calm"                  # Rien d'intéressant


class Intensity(Enum):
    """Intensité de l'action."""
    HIGH = 3      # 1v2+, clutch, moments critiques
    MEDIUM = 2    # 1v1, combat standard
    LOW = 1       # Fin de combat, looting post-kill
    NONE = 0      # Pas d'action


class SequenceContext(Enum):
    """Position dans une séquence d'action."""
    START = "start"      # Début d'engagement
    PEAK = "peak"        # Moment le plus intense
    END = "end"          # Fin/résolution
    STANDALONE = "standalone"  # Moment isolé


@dataclass
class SemanticAnalysis:
    """Résultat de l'analyse sémantique d'une frame."""
    action_type: ActionType
    intensity: Intensity
    sequence_context: SequenceContext
    confidence: float  # 0-1

    # Détails optionnels
    enemy_count: int = 0
    player_health_status: str = ""  # "healthy", "low", "critical"
    weapons_visible: List[str] = None
    raw_description: str = ""

    def to_score(self) -> float:
        """
        Convertit l'analyse en score numérique (0-1).

        Pondération :
        - PvP High = 1.0
        - PvP Medium = 0.8
        - PvE High = 0.7
        - Looting = 0.3
        - Crafting/Calm = 0.1
        """
        base_scores = {
            ActionType.PVP_COMBAT: 1.0,
            ActionType.PVE_COMBAT: 0.7,
            ActionType.LOOTING: 0.3,
            ActionType.CRAFTING: 0.1,
            ActionType.MOVEMENT: 0.2,
            ActionType.CALM: 0.05,
        }

        # Score de base selon le type
        score = base_scores.get(self.action_type, 0.1)

        # Multiplier par l'intensité
        intensity_multiplier = self.intensity.value / 3.0  # 0.33, 0.66, 1.0
        score *= intensity_multiplier

        # Bonus pour moments de peak
        if self.sequence_context == SequenceContext.PEAK:
            score *= 1.2

        # Bonus pour outnumbered (1vX)
        if self.enemy_count >= 2:
            score *= 1.1 + (self.enemy_count - 1) * 0.1  # +10% par ennemi supplémentaire

        # Ajuster par confiance
        score *= self.confidence

        return min(score, 1.0)


class LLMAnalyzer:
    """Analyseur LLM pour compréhension sémantique des frames."""

    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)

        # Config LLaVA
        self.enabled = config.get('llava', {}).get('enabled', False)
        self.model = config.get('llava', {}).get('model', 'llava:7b')
        self.batch_size = config.get('llava', {}).get('batch_size', 5)
        self.temperature = config.get('llava', {}).get('temperature', 0.3)

        # Vérifier disponibilité
        if self.enabled and not OLLAMA_AVAILABLE:
            self.logger.error("❌ LLaVA activé mais Ollama non installé!")
            self.logger.error("   Installation: https://ollama.ai")
            self.enabled = False

        if self.enabled:
            self._verify_model()

    def _verify_model(self):
        """Vérifie que le modèle LLaVA est disponible."""
        try:
            models = ollama.list()
            available = any(self.model in m['name'] for m in models.get('models', []))

            if not available:
                self.logger.warning(f"⚠️  Modèle {self.model} non trouvé")
                self.logger.info(f"   Téléchargement automatique...")
                ollama.pull(self.model)
                self.logger.info(f"✓ Modèle {self.model} téléchargé")
            else:
                self.logger.info(f"✓ Modèle {self.model} disponible")

        except Exception as e:
            self.logger.error(f"❌ Erreur vérification modèle: {e}")
            self.enabled = False

    def analyze_frame(self, frame_path: str, segment_index: int) -> Optional[SemanticAnalysis]:
        """
        Analyse une frame avec LLaVA pour comprendre le contexte.

        Args:
            frame_path: Chemin vers l'image de la frame
            segment_index: Index du segment (pour contexte séquentiel)

        Returns:
            SemanticAnalysis ou None si erreur
        """
        if not self.enabled:
            return None

        try:
            # Prompt optimisé pour FPS gameplay
            prompt = self._build_prompt()

            # Appel LLaVA
            response = ollama.chat(
                model=self.model,
                messages=[{
                    'role': 'user',
                    'content': prompt,
                    'images': [frame_path]
                }],
                options={
                    'temperature': self.temperature,
                }
            )

            # Parser la réponse
            analysis = self._parse_response(response['message']['content'])

            return analysis

        except Exception as e:
            self.logger.error(f"Erreur analyse LLaVA segment {segment_index}: {e}")
            return None

    def analyze_frames_batch(self, frame_paths: List[str],
                            segment_indices: List[int]) -> List[Optional[SemanticAnalysis]]:
        """
        Analyse plusieurs frames en batch pour optimiser les performances.

        Args:
            frame_paths: Liste des chemins vers les frames
            segment_indices: Liste des indices de segments

        Returns:
            Liste de SemanticAnalysis (ou None si erreur)
        """
        if not self.enabled:
            return [None] * len(frame_paths)

        results = []
        total = len(frame_paths)

        self.logger.info(f"🧠 Analyse LLaVA de {total} frames...")
        start_time = time.time()

        # Traiter par batches
        for i in range(0, total, self.batch_size):
            batch_paths = frame_paths[i:i + self.batch_size]
            batch_indices = segment_indices[i:i + self.batch_size]

            # Analyser chaque frame du batch
            for frame_path, idx in zip(batch_paths, batch_indices):
                analysis = self.analyze_frame(frame_path, idx)
                results.append(analysis)

            # Log progression
            progress = min(i + self.batch_size, total)
            elapsed = time.time() - start_time
            fps = progress / elapsed if elapsed > 0 else 0
            self.logger.info(f"   {progress}/{total} frames ({fps:.1f} frames/s)")

        elapsed = time.time() - start_time
        self.logger.info(f"✓ Analyse LLaVA terminée en {elapsed/60:.1f} min")

        return results

    def _build_prompt(self) -> str:
        """Construit le prompt optimisé pour l'analyse de gameplay FPS."""
        return """Analyze this FPS gameplay frame and provide a structured analysis.

Focus on:
1. **Action Type**: What is happening?
   - PvP Combat: Player fighting other players
   - PvE Combat: Player fighting AI/drones/NPCs
   - Looting: Player collecting items/resources
   - Crafting: Player at base/workbench crafting
   - Movement: Player just moving/running
   - Calm: Nothing interesting happening

2. **Intensity**: How intense is the action?
   - High: Multiple enemies (1v2+), clutch situation, critical moment
   - Medium: Standard 1v1 combat, regular engagement
   - Low: Combat ending, looting after kill, low threat
   - None: No action

3. **Sequence Context**: Where in the action sequence?
   - Start: Beginning of engagement/combat
   - Peak: Most intense moment of the sequence
   - End: Finishing/resolution of action
   - Standalone: Isolated moment

4. **Details**:
   - Number of visible enemies
   - Player health status (healthy/low/critical) if visible
   - Weapons visible

Respond in JSON format:
{
    "action_type": "pvp_combat|pve_combat|looting|crafting|movement|calm",
    "intensity": "high|medium|low|none",
    "sequence_context": "start|peak|end|standalone",
    "confidence": 0.0-1.0,
    "enemy_count": 0-10,
    "player_health": "healthy|low|critical|unknown",
    "weapons_visible": ["weapon1", "weapon2"],
    "description": "Brief description of what's happening"
}"""

    def _parse_response(self, response: str) -> SemanticAnalysis:
        """
        Parse la réponse JSON de LLaVA en SemanticAnalysis.

        Args:
            response: Réponse texte de LLaVA

        Returns:
            SemanticAnalysis
        """
        try:
            # Extraire le JSON de la réponse
            # LLaVA peut ajouter du texte avant/après, on cherche le JSON
            start = response.find('{')
            end = response.rfind('}') + 1

            if start == -1 or end == 0:
                raise ValueError("Pas de JSON trouvé dans la réponse")

            json_str = response[start:end]
            data = json.loads(json_str)

            # Mapper vers les enums
            action_type = ActionType[data['action_type'].upper()]

            intensity_map = {
                'high': Intensity.HIGH,
                'medium': Intensity.MEDIUM,
                'low': Intensity.LOW,
                'none': Intensity.NONE,
            }
            intensity = intensity_map.get(data['intensity'].lower(), Intensity.NONE)

            context_map = {
                'start': SequenceContext.START,
                'peak': SequenceContext.PEAK,
                'end': SequenceContext.END,
                'standalone': SequenceContext.STANDALONE,
            }
            sequence_context = context_map.get(data['sequence_context'].lower(),
                                              SequenceContext.STANDALONE)

            return SemanticAnalysis(
                action_type=action_type,
                intensity=intensity,
                sequence_context=sequence_context,
                confidence=float(data.get('confidence', 0.8)),
                enemy_count=int(data.get('enemy_count', 0)),
                player_health_status=data.get('player_health', 'unknown'),
                weapons_visible=data.get('weapons_visible', []),
                raw_description=data.get('description', ''),
            )

        except Exception as e:
            self.logger.warning(f"Erreur parsing réponse LLaVA: {e}")
            self.logger.debug(f"Réponse brute: {response}")

            # Retour par défaut conservateur
            return SemanticAnalysis(
                action_type=ActionType.CALM,
                intensity=Intensity.NONE,
                sequence_context=SequenceContext.STANDALONE,
                confidence=0.0,
                raw_description=response,
            )
