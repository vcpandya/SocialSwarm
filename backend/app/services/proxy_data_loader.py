"""
Proxy Dataset Loader
Loads few-shot example data for improving LLM prompt quality.
Provides persona examples, initial post templates, and sentiment calibration data.
"""

import json
import os
from typing import Dict, Any, List, Optional

from ..utils.logger import get_logger

logger = get_logger('mirofish.proxy_data')

# Data directory path
DATA_DIR = os.path.join(os.path.dirname(__file__), '../../data/proxy_datasets')


class ProxyDataLoader:
    """Loads and provides proxy datasets for LLM prompting"""

    _instance = None
    _data = {}

    @classmethod
    def get_instance(cls) -> 'ProxyDataLoader':
        """Singleton access"""
        if cls._instance is None:
            cls._instance = cls()
            cls._instance._load_all()
        return cls._instance

    def _load_all(self):
        """Load all proxy datasets"""
        self._data = {}
        files = {
            'personas': 'persona_examples.json',
            'initial_posts': 'initial_posts_examples.json',
            'sentiment': 'sentiment_calibration.json',
        }
        for key, filename in files.items():
            path = os.path.join(DATA_DIR, filename)
            try:
                if os.path.exists(path):
                    with open(path, 'r', encoding='utf-8') as f:
                        self._data[key] = json.load(f)
                    logger.info(f"Loaded proxy dataset: {filename}")
                else:
                    logger.warning(f"Proxy dataset not found: {path}")
                    self._data[key] = {}
            except Exception as e:
                logger.error(f"Failed to load proxy dataset {filename}: {e}")
                self._data[key] = {}

    def get_persona_examples(self, entity_type: str = None, region: str = None, limit: int = 2) -> List[Dict]:
        """Get example personas, optionally filtered by entity type and region"""
        personas = self._data.get('personas', {})
        examples = personas.get('individual_personas', []) + personas.get('institutional_personas', [])

        if entity_type:
            examples = [e for e in examples if e.get('entity_type', '').lower() == entity_type.lower()]
        if region:
            examples = [e for e in examples if e.get('region', '').lower() == region.lower()]

        return [e.get('example', e) for e in examples[:limit]]

    def get_initial_post_examples(self, scenario: str = None, limit: int = 4) -> List[Dict]:
        """Get example initial posts for a scenario"""
        posts_data = self._data.get('initial_posts', {})
        by_scenario = posts_data.get('by_scenario', {})

        if scenario and scenario in by_scenario:
            return by_scenario[scenario][:limit]

        # Return mix from all scenarios
        all_posts = []
        for posts in by_scenario.values():
            all_posts.extend(posts[:2])
        return all_posts[:limit]

    def get_sentiment_calibration(self, limit: int = 5) -> List[Dict]:
        """Get sentiment calibration examples for few-shot prompting"""
        cal_data = self._data.get('sentiment', {})
        return cal_data.get('calibration_examples', [])[:limit]

    def format_persona_examples_for_prompt(self, entity_type: str = None, region: str = None) -> str:
        """Format persona examples as text suitable for LLM prompt injection"""
        examples = self.get_persona_examples(entity_type, region)
        if not examples:
            return ""

        text = "\n\n### Reference Persona Examples (for style and depth guidance):\n"
        for i, ex in enumerate(examples, 1):
            text += f"\n**Example {i}** ({ex.get('profession', 'Unknown')}):\n"
            text += f"- Bio: {ex.get('bio', '')}\n"
            text += f"- Persona excerpt: {ex.get('persona', '')[:300]}...\n"

        return text

    def format_sentiment_examples_for_prompt(self, limit: int = 4) -> str:
        """Format sentiment calibration examples for prompt injection"""
        examples = self.get_sentiment_calibration(limit)
        if not examples:
            return ""

        text = "\n\n### Calibration Examples:\n"
        for ex in examples:
            text += f'\nPost: "{ex["content"][:100]}"\n'
            text += f'→ sentiment: {ex["sentiment"]}, emotions: {json.dumps(ex.get("emotions", {}))}\n'
            text += f'→ topics: {ex.get("topics", [])}, stance: {ex.get("stance", {})}\n'

        return text
