"""Custom exception classes for CodeWise.

This module defines the exception hierarchy for the CodeWise system, providing
clear, actionable error messages with contextual information.
"""

from typing import Any


class CodewiseError(Exception):
    """Base exception for all CodeWise errors.
    
    All custom exceptions in the CodeWise system inherit from this base class,
    allowing for easy catching of all CodeWise-specific errors.
    """
    pass


class GitOperationError(CodewiseError):
    """Raised when Git operations fail.
    
    This exception is raised when any Git operation (fetch, diff, log, blame, etc.)
    fails to execute successfully. It includes contextual information about the
    operation, repository path, and failure details.
    
    Attributes:
        operation: The Git operation that failed (e.g., 'fetch', 'diff', 'log').
        repo_path: The path to the repository where the operation was attempted.
        details: Detailed information about why the operation failed.
    """
    
    def __init__(self, operation: str, repo_path: str, details: str):
        """Initialize GitOperationError with context.
        
        Args:
            operation: The Git operation that failed.
            repo_path: The repository path where the operation was attempted.
            details: Detailed error information.
        """
        self.operation = operation
        self.repo_path = repo_path
        self.details = details
        super().__init__(f"Git {operation} failed for {repo_path}: {details}")


class ConfigurationError(CodewiseError):
    """Raised when configuration is invalid or missing.
    
    This exception is raised when required configuration is missing, invalid,
    or cannot be loaded. It includes information about which configuration
    key caused the error and why.
    
    Attributes:
        config_key: The configuration key that caused the error.
        reason: Explanation of why the configuration is invalid.
    """
    
    def __init__(self, config_key: str, reason: str):
        """Initialize ConfigurationError with context.
        
        Args:
            config_key: The configuration key that is invalid or missing.
            reason: Explanation of the configuration error.
        """
        self.config_key = config_key
        self.reason = reason
        super().__init__(f"Configuration error for '{config_key}': {reason}")


class FileOperationError(CodewiseError):
    """Raised when file operations fail.
    
    This exception is raised when file I/O operations (read, write, create directory)
    fail to execute successfully. It includes contextual information about the
    operation, file path, and failure details.
    
    Attributes:
        operation: The file operation that failed (e.g., 'write', 'read', 'mkdir').
        file_path: The path to the file where the operation was attempted.
        details: Detailed information about why the operation failed.
    """
    
    def __init__(self, operation: str, file_path: str, details: str):
        """Initialize FileOperationError with context.
        
        Args:
            operation: The file operation that failed.
            file_path: The file path where the operation was attempted.
            details: Detailed error information.
        """
        self.operation = operation
        self.file_path = file_path
        self.details = details
        super().__init__(f"File {operation} failed for {file_path}: {details}")


class ValidationError(CodewiseError):
    """Raised when input validation fails.
    
    This exception is raised when user input or data fails validation checks.
    It includes information about which field failed validation, the invalid
    value, and why it was rejected.
    
    Attributes:
        field: The field name that failed validation.
        value: The invalid value that was provided.
        reason: Explanation of why the value is invalid.
    """
    
    def __init__(self, field: str, value: Any, reason: str):
        """Initialize ValidationError with context.
        
        Args:
            field: The field name that failed validation.
            value: The invalid value.
            reason: Explanation of the validation failure.
        """
        self.field = field
        self.value = value
        self.reason = reason
        super().__init__(f"Validation failed for {field}='{value}': {reason}")


class LGPDComplianceError(CodewiseError):
    """Raised when LGPD compliance check fails.
    
    This exception is raised when an AI provider's data collection policy
    fails LGPD (Brazilian General Data Protection Law) compliance verification.
    It includes information about the provider, model, and reasoning for
    non-compliance.
    
    Attributes:
        provider: The AI provider name (e.g., 'GEMINI', 'OPENAI').
        model: The specific model being checked.
        reasoning: Detailed explanation of why the provider is non-compliant.
    """
    
    def __init__(self, provider: str, model: str, reasoning: str):
        """Initialize LGPDComplianceError with context.
        
        Args:
            provider: The AI provider name.
            model: The model being checked.
            reasoning: Explanation of non-compliance.
        """
        self.provider = provider
        self.model = model
        self.reasoning = reasoning
        super().__init__(f"LGPD compliance failed for {provider}/{model}: {reasoning}")


class NotificationError(CodewiseError):
    """Raised when notification delivery fails.
    
    This exception is raised when sending notifications (email, Slack, webhook)
    fails. It includes information about which channel failed and why.
    
    Note: This exception should typically be caught and logged without blocking
    the main workflow, as notification failures are non-critical.
    
    Attributes:
        channel: The notification channel that failed (e.g., 'email', 'slack').
        details: Detailed information about the failure.
    """
    
    def __init__(self, channel: str, details: str):
        """Initialize NotificationError with context.
        
        Args:
            channel: The notification channel that failed.
            details: Detailed error information.
        """
        self.channel = channel
        self.details = details
        super().__init__(f"Notification to {channel} failed: {details}")
