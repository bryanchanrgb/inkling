"""Configuration management for the application."""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Manages application configuration."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize configuration from YAML file."""
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config.yaml"
        
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self.load()
    
    def load(self) -> None:
        """Load configuration from YAML file."""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                self._config = yaml.safe_load(f) or {}
        else:
            self._config = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation."""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            if value is None:
                return default
        return value
    
    def get_ai_provider(self) -> str:
        """Get the configured AI provider."""
        return self.get('ai.provider', 'openai')
    
    def get_ai_config(self) -> Dict[str, Any]:
        """Get AI provider configuration."""
        provider = self.get_ai_provider()
        config = self.get(f'ai.{provider}', {})
        
        # Override with environment variables if available
        if provider == 'openai':
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                config['api_key'] = api_key
        elif provider == 'anthropic':
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if api_key:
                config['api_key'] = api_key
        elif provider == 'openrouter':
            api_key = os.getenv('OPENROUTER_API_KEY')
            if api_key:
                config['api_key'] = api_key
        
        return config
    
    def get_neo4j_config(self) -> Dict[str, Any]:
        """Get Neo4j configuration."""
        config = self.get('neo4j', {})
        # Username and password are loaded from environment variables in knowledge_graph.py
        return config
    
    def get_storage_config(self) -> Dict[str, Any]:
        """Get storage configuration."""
        return self.get('storage', {})
    
    def get_app_config(self) -> Dict[str, Any]:
        """Get application settings."""
        return self.get('app', {})


# Global configuration instance
_config_instance: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance

