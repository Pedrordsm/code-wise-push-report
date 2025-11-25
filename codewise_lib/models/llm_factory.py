"""LLM factory for creating AI provider instances.

This module provides a factory pattern for creating and configuring LLM instances
from various AI providers (Gemini, OpenAI, Groq, Cohere). It handles provider
validation, API key checking, and instance creation.
"""

import os
from typing import List
from crewai import LLM

from .exceptions import ConfigurationError


class LLMFactory:
    """Factory class for creating LLM instances.
    
    This class provides methods to create LLM instances for different AI providers,
    validate configuration, and manage provider-specific settings. It uses the
    factory pattern to encapsulate provider-specific logic.
    """
    
    # Supported providers and their configuration
    SUPPORTED_PROVIDERS = {
        "GEMINI": {
            "env_key": "GEMINI_API_KEY",
            "model_prefix": "gemini/"
        },
        "OPENAI": {
            "env_key": "OPENAI_API_KEY",
            "model_prefix": "openai/"
        },
        "GROQ": {
            "env_key": "GROQ_API_KEY",
            "model_prefix": "groq/"
        },
        "COHERE": {
            "env_key": "COHERE_API_KEY",
            "model_prefix": "cohere_chat/"
        }
    }
    
    def __init__(self, temperature: float = 0.7):
        """Initialize LLMFactory with default settings.
        
        Args:
            temperature: The temperature setting for LLM responses (0.0-1.0).
                        Higher values make output more random. Defaults to 0.7.
        """
        self.temperature = temperature
    
    def create_llm(self, provider: str, model: str) -> LLM:
        """Create an LLM instance for the specified provider and model.
        
        This method validates the provider, checks for required API keys,
        and creates an appropriately configured LLM instance.
        
        Args:
            provider: The AI provider name (e.g., 'GEMINI', 'OPENAI', 'GROQ', 'COHERE').
            model: The specific model to use (e.g., 'gemini-pro', 'gpt-4').
            
        Returns:
            A configured LLM instance ready for use.
            
        Raises:
            ConfigurationError: If the provider is unsupported, API key is missing,
                              or LLM initialization fails.
        """
        # Validate provider
        provider_upper = provider.upper()
        if provider_upper not in self.SUPPORTED_PROVIDERS:
            raise ConfigurationError(
                "ai_provider",
                f"Unsupported provider '{provider}'. Supported providers: {', '.join(self.SUPPORTED_PROVIDERS.keys())}"
            )
        
        # Get provider configuration
        provider_config = self.SUPPORTED_PROVIDERS[provider_upper]
        env_key = provider_config["env_key"]
        model_prefix = provider_config["model_prefix"]
        
        # Validate API key
        if not os.getenv(env_key):
            raise ConfigurationError(
                env_key,
                f"Environment variable '{env_key}' is not set. Please configure your API key."
            )
        
        # Create LLM instance
        try:
            full_model_name = f"{model_prefix}{model}"
            return LLM(
                model=full_model_name,
                temperature=self.temperature
            )
        except Exception as e:
            raise ConfigurationError(
                "llm_initialization",
                f"Failed to initialize LLM for {provider}/{model}: {str(e)}"
            )
    
    def validate_configuration(self, provider: str) -> bool:
        """Validate that a provider is properly configured.
        
        Checks if the provider is supported and has the required API key set.
        
        Args:
            provider: The AI provider name to validate.
            
        Returns:
            True if the provider is valid and configured.
            
        Raises:
            ConfigurationError: If validation fails.
        """
        provider_upper = provider.upper()
        
        # Check if provider is supported
        if provider_upper not in self.SUPPORTED_PROVIDERS:
            raise ConfigurationError(
                "ai_provider",
                f"Unsupported provider '{provider}'. Supported providers: {', '.join(self.SUPPORTED_PROVIDERS.keys())}"
            )
        
        # Check if API key is set
        env_key = self.SUPPORTED_PROVIDERS[provider_upper]["env_key"]
        if not os.getenv(env_key):
            raise ConfigurationError(
                env_key,
                f"Environment variable '{env_key}' is not set"
            )
        
        return True
    
    @staticmethod
    def get_supported_providers() -> List[str]:
        """Get list of supported AI providers.
        
        Returns:
            List of supported provider names.
        """
        return list(LLMFactory.SUPPORTED_PROVIDERS.keys())
    
    @staticmethod
    def get_provider_env_key(provider: str) -> str:
        """Get the environment variable key for a provider's API key.
        
        Args:
            provider: The AI provider name.
            
        Returns:
            The environment variable name for the provider's API key.
            
        Raises:
            ConfigurationError: If the provider is not supported.
        """
        provider_upper = provider.upper()
        if provider_upper not in LLMFactory.SUPPORTED_PROVIDERS:
            raise ConfigurationError(
                "ai_provider",
                f"Unsupported provider '{provider}'"
            )
        
        return LLMFactory.SUPPORTED_PROVIDERS[provider_upper]["env_key"]
