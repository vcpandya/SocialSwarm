"""
Settings Manager — persists user configuration to a JSON file.
Settings override .env values at runtime by patching Config class attributes.
"""

import json
import os
import threading
from typing import Dict, Any, Optional, List, Tuple

from ..config import Config
from ..utils.logger import get_logger

logger = get_logger('mirofish.settings')

SETTINGS_FILE = os.path.join(os.path.dirname(__file__), '../../data/settings.json')

# Map from settings JSON paths to Config class attributes
_CONFIG_MAP = {
    'llm.api_key': ('LLM_API_KEY', str),
    'llm.base_url': ('LLM_BASE_URL', str),
    'llm.model_name': ('LLM_MODEL_NAME', str),
    'zep.api_key': ('ZEP_API_KEY', str),
    'simulation.max_rounds': ('OASIS_DEFAULT_MAX_ROUNDS', int),
    'simulation.chunk_size': ('DEFAULT_CHUNK_SIZE', int),
    'simulation.chunk_overlap': ('DEFAULT_CHUNK_OVERLAP', int),
    'report_agent.max_tool_calls': ('REPORT_AGENT_MAX_TOOL_CALLS', int),
    'report_agent.max_reflection_rounds': ('REPORT_AGENT_MAX_REFLECTION_ROUNDS', int),
    'report_agent.temperature': ('REPORT_AGENT_TEMPERATURE', float),
}

# Boost LLM keys go to os.environ (read by subprocess scripts)
_ENV_MAP = {
    'boost_llm.api_key': 'LLM_BOOST_API_KEY',
    'boost_llm.base_url': 'LLM_BOOST_BASE_URL',
    'boost_llm.model_name': 'LLM_BOOST_MODEL_NAME',
}

_lock = threading.Lock()


class SettingsManager:
    """Manages application settings stored in a JSON file."""

    @staticmethod
    def load() -> Dict[str, Any]:
        """Load settings from disk. Returns empty dict if file doesn't exist."""
        if not os.path.exists(SETTINGS_FILE):
            return {}
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load settings: {e}")
            return {}

    @staticmethod
    def save(settings: Dict[str, Any]) -> None:
        """Save settings to disk."""
        with _lock:
            os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
        logger.info("Settings saved to disk")

    @staticmethod
    def apply_to_config() -> None:
        """Load settings and patch Config class attributes + os.environ."""
        settings = SettingsManager.load()
        if not settings:
            return

        for json_path, (attr_name, type_fn) in _CONFIG_MAP.items():
            group, key = json_path.split('.')
            value = settings.get(group, {}).get(key)
            if value is not None and value != '':
                try:
                    setattr(Config, attr_name, type_fn(value))
                except (ValueError, TypeError):
                    pass

        for json_path, env_var in _ENV_MAP.items():
            group, key = json_path.split('.')
            value = settings.get(group, {}).get(key)
            if value is not None and value != '':
                os.environ[env_var] = str(value)

        logger.info("Settings applied to runtime config")

    @staticmethod
    def get_current() -> Dict[str, Any]:
        """Return the merged current config with masked API keys."""
        def mask(val):
            if not val or len(str(val)) < 8:
                return '****' if val else ''
            s = str(val)
            return '****' + s[-4:]

        return {
            'llm': {
                'api_key': mask(Config.LLM_API_KEY),
                'base_url': Config.LLM_BASE_URL or '',
                'model_name': Config.LLM_MODEL_NAME or '',
            },
            'zep': {
                'api_key': mask(Config.ZEP_API_KEY),
            },
            'boost_llm': {
                'api_key': mask(os.environ.get('LLM_BOOST_API_KEY', '')),
                'base_url': os.environ.get('LLM_BOOST_BASE_URL', ''),
                'model_name': os.environ.get('LLM_BOOST_MODEL_NAME', ''),
            },
            'simulation': {
                'max_rounds': Config.OASIS_DEFAULT_MAX_ROUNDS,
                'chunk_size': Config.DEFAULT_CHUNK_SIZE,
                'chunk_overlap': Config.DEFAULT_CHUNK_OVERLAP,
            },
            'report_agent': {
                'max_tool_calls': Config.REPORT_AGENT_MAX_TOOL_CALLS,
                'max_reflection_rounds': Config.REPORT_AGENT_MAX_REFLECTION_ROUNDS,
                'temperature': Config.REPORT_AGENT_TEMPERATURE,
            },
            'app': {
                'language': SettingsManager.load().get('app', {}).get('language', 'en'),
            },
        }

    @staticmethod
    def get_status() -> Dict[str, Any]:
        """Check if required configuration is present."""
        missing = []
        if not Config.LLM_API_KEY:
            missing.append('llm.api_key')
        if not Config.ZEP_API_KEY:
            missing.append('zep.api_key')
        return {
            'configured': len(missing) == 0,
            'missing': missing,
        }

    @staticmethod
    def merge_and_save(updates: Dict[str, Any]) -> Dict[str, Any]:
        """Merge partial updates into existing settings and save."""
        current = SettingsManager.load()
        for group, values in updates.items():
            if not isinstance(values, dict):
                continue
            if group not in current:
                current[group] = {}
            for key, val in values.items():
                # Skip masked values (user didn't change the API key)
                if isinstance(val, str) and val.startswith('****'):
                    continue
                current[group][key] = val
        SettingsManager.save(current)
        SettingsManager.apply_to_config()
        return current

    @staticmethod
    def validate_llm(api_key: str, base_url: str, model_name: str) -> Tuple[bool, str]:
        """Test LLM connection with a minimal API call."""
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key, base_url=base_url)
            response = client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=1,
            )
            return True, "Connection successful"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def validate_zep(api_key: str) -> Tuple[bool, str]:
        """Test Zep connection."""
        try:
            from zep_cloud.client import Zep
            client = Zep(api_key=api_key)
            # A lightweight call — list graphs with limit 1
            client.graph.search(query="test", user_id="__validation_test__", limit=1)
            return True, "Connection successful"
        except Exception as e:
            error_str = str(e)
            # A 404 for user not found is actually fine — it means auth worked
            if '404' in error_str or 'not found' in error_str.lower():
                return True, "Connection successful"
            return False, error_str
