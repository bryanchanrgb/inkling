"""AI service with support for multiple providers."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from anthropic import Anthropic
from openai import OpenAI

from .config import get_config


class AIProvider(ABC):
    """Abstract base class for AI providers."""
    
    @abstractmethod
    def call_model(
        self,
        system_message: str,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """Call the AI model with a system message and user message.
        
        Args:
            system_message: System message/instruction for the model
            user_message: User message/prompt
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens in response (optional)
            
        Returns:
            Response text from the model
        """
        pass


class OpenAIProvider(AIProvider):
    """OpenAI provider implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize OpenAI provider."""
        api_key = config.get('api_key')
        if not api_key:
            raise ValueError("OpenAI API key not found. Set OPENAI_API_KEY environment variable.")
        self.client = OpenAI(api_key=api_key)
        self.model = config.get('model', 'gpt-5-mini')
    
    def call_model(
        self,
        system_message: str,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """Call the OpenAI model."""
        kwargs = {
            'model': self.model,
            'messages': [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            'temperature': temperature,
        }
        if max_tokens is not None:
            kwargs['max_tokens'] = max_tokens
        
        response = self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content


class AnthropicProvider(AIProvider):
    """Anthropic (Claude) provider implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Anthropic provider."""
        api_key = config.get('api_key')
        if not api_key:
            raise ValueError("Anthropic API key not found. Set ANTHROPIC_API_KEY environment variable.")
        self.client = Anthropic(api_key=api_key)
        self.model = config.get('model', 'claude-3-sonnet-20240229')
    
    def call_model(
        self,
        system_message: str,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """Call the Anthropic model."""
        kwargs = {
            'model': self.model,
            'system': system_message,
            'messages': [
                {"role": "user", "content": user_message}
            ],
            'temperature': temperature,
        }
        if max_tokens is not None:
            kwargs['max_tokens'] = max_tokens
        
        response = self.client.messages.create(**kwargs)
        return response.content[0].text


class OpenRouterProvider(AIProvider):
    """OpenRouter provider implementation."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize OpenRouter provider."""
        api_key = config.get('api_key')
        if not api_key:
            raise ValueError("OpenRouter API key not found. Set OPENROUTER_API_KEY environment variable.")
        # OpenRouter uses OpenAI-compatible API
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        self.model = config.get('model', 'openai/gpt-5-mini')
    
    def call_model(
        self,
        system_message: str,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """Call the OpenRouter model."""
        kwargs = {
            'model': self.model,
            'messages': [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            'temperature': temperature,
        }
        if max_tokens is not None:
            kwargs['max_tokens'] = max_tokens
        
        response = self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content


class LocalProvider(AIProvider):
    """Local provider implementation (e.g., Ollama)."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize local provider."""
        from openai import OpenAI as LocalOpenAI
        
        base_url = config.get('base_url', 'http://localhost:11434/v1')
        if not base_url.endswith('/v1'):
            base_url = f"{base_url}/v1"
        
        self.client = LocalOpenAI(base_url=base_url, api_key='ollama')
        self.model = config.get('model', 'llama2')
    
    def call_model(
        self,
        system_message: str,
        user_message: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """Call the local model."""
        kwargs = {
            'model': self.model,
            'messages': [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            'temperature': temperature,
        }
        if max_tokens is not None:
            kwargs['max_tokens'] = max_tokens
        
        response = self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content


def get_ai_service() -> AIProvider:
    """Get the configured AI service provider."""
    config = get_config()
    provider_name = config.get_ai_provider()
    ai_config = config.get_ai_config()
    
    if provider_name == 'openai':
        return OpenAIProvider(ai_config)
    elif provider_name == 'anthropic':
        return AnthropicProvider(ai_config)
    elif provider_name == 'openrouter':
        return OpenRouterProvider(ai_config)
    elif provider_name == 'local':
        return LocalProvider(ai_config)
    else:
        raise ValueError(f"Unknown AI provider: {provider_name}")
