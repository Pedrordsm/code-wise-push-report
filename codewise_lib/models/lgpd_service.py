"""LGPD compliance verification service for CodeWise.

This module handles privacy compliance verification for AI providers, analyzing
their data collection policies against LGPD (Brazilian General Data Protection Law)
requirements. It includes caching to avoid repeated verifications.
"""

import os
import json
from typing import Optional
from pathlib import Path

from .analysis_models import PolicyAnalysis
from .exceptions import LGPDComplianceError, FileOperationError


class LGPDService:
    """Service for LGPD compliance verification.
    
    This class manages LGPD compliance checks for AI providers, including
    policy analysis, result caching, and compliance determination.
    """
    
    def __init__(self, cache_dir: str = ".codewise_cache"):
        """Initialize LGPDService with cache directory.
        
        Args:
            cache_dir: Directory for caching verification results.
                      Defaults to '.codewise_cache' in current directory.
        """
        self.cache_dir = Path(cache_dir)
        self._ensure_cache_directory()
    
    def _ensure_cache_directory(self) -> None:
        """Ensure the cache directory exists.
        
        Raises:
            FileOperationError: If directory creation fails.
        """
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise FileOperationError(
                "mkdir",
                str(self.cache_dir),
                f"Failed to create cache directory: {str(e)}"
            )
    
    def _get_cache_key(self, provider: str, model: str) -> str:
        """Generate cache key for a provider/model combination.
        
        Args:
            provider: The AI provider name.
            model: The model name.
            
        Returns:
            Cache key string.
        """
        return f"{provider.lower()}_{model.lower()}.json"
    
    def get_cached_result(self, provider: str, model: str) -> Optional[PolicyAnalysis]:
        """Retrieve cached verification result if available.
        
        Args:
            provider: The AI provider name.
            model: The model name.
            
        Returns:
            PolicyAnalysis if cached result exists, None otherwise.
        """
        cache_file = self.cache_dir / self._get_cache_key(provider, model)
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return PolicyAnalysis(
                    provider=data['provider'],
                    model=data['model'],
                    compliant=data['compliant'],
                    reasoning=data['reasoning']
                )
        except Exception:
            # If cache is corrupted, return None to trigger re-verification
            return None
    
    def save_verification_result(
        self,
        provider: str,
        model: str,
        compliant: bool,
        reasoning: str
    ) -> None:
        """Save verification result to cache.
        
        Args:
            provider: The AI provider name.
            model: The model name.
            compliant: Whether the provider is LGPD compliant.
            reasoning: Explanation of the compliance determination.
            
        Raises:
            FileOperationError: If saving to cache fails.
        """
        cache_file = self.cache_dir / self._get_cache_key(provider, model)
        
        data = {
            'provider': provider,
            'model': model,
            'compliant': compliant,
            'reasoning': reasoning
        }
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise FileOperationError(
                "write",
                str(cache_file),
                f"Failed to save verification result: {str(e)}"
            )
    
    def analyze_policy(self, provider: str, model: str, crew_result: str) -> PolicyAnalysis:
        """Analyze AI provider policy from crew analysis result.
        
        This method parses the result from the LGPD crew analysis and
        determines compliance status.
        
        Args:
            provider: The AI provider name.
            model: The model name.
            crew_result: The result from LGPD crew execution.
            
        Returns:
            PolicyAnalysis with compliance determination.
            
        Raises:
            LGPDComplianceError: If policy analysis fails or provider is non-compliant.
        """
        try:
            # Parse crew result - expecting first line to be "sim" or "não"
            lines = crew_result.strip().split('\n')
            
            if not lines:
                raise LGPDComplianceError(
                    provider,
                    model,
                    "Empty analysis result from LGPD crew"
                )
            
            # First line should contain the verdict
            verdict = lines[0].strip().lower()
            compliant = verdict == "sim" or "sim" in verdict
            
            # Rest is the reasoning
            reasoning = '\n'.join(lines[1:]).strip() if len(lines) > 1 else "No reasoning provided"
            
            # Create policy analysis
            analysis = PolicyAnalysis(
                provider=provider,
                model=model,
                compliant=compliant,
                reasoning=reasoning
            )
            
            # Cache the result
            self.save_verification_result(provider, model, compliant, reasoning)
            
            # If not compliant, raise error
            if not compliant:
                raise LGPDComplianceError(provider, model, reasoning)
            
            return analysis
            
        except LGPDComplianceError:
            raise
        except Exception as e:
            raise LGPDComplianceError(
                provider,
                model,
                f"Failed to analyze policy: {str(e)}"
            )
    
    def verify_provider_compliance(
        self,
        provider: str,
        model: str,
        force_recheck: bool = False
    ) -> bool:
        """Verify if a provider is LGPD compliant.
        
        This method checks the cache first, and only performs a new
        verification if no cached result exists or force_recheck is True.
        
        Note: This method only checks the cache. To perform a full verification
        with crew analysis, use analyze_policy() instead.
        
        Args:
            provider: The AI provider name.
            model: The model name.
            force_recheck: If True, ignore cache and force new verification.
            
        Returns:
            True if provider is compliant, False otherwise.
        """
        if not force_recheck:
            cached = self.get_cached_result(provider, model)
            if cached is not None:
                return cached.compliant
        
        # No cached result available
        # In a real scenario, this would trigger crew analysis
        # For now, return False to indicate verification needed
        return False
    
    def clear_cache(self, provider: Optional[str] = None, model: Optional[str] = None) -> None:
        """Clear verification cache.
        
        Args:
            provider: Optional provider name to clear specific cache.
            model: Optional model name to clear specific cache.
                  If both provider and model are None, clears all cache.
        """
        if provider and model:
            # Clear specific cache file
            cache_file = self.cache_dir / self._get_cache_key(provider, model)
            if cache_file.exists():
                cache_file.unlink()
        else:
            # Clear all cache files
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
