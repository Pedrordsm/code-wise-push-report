"""Model layer for CodeWise.

This package contains all data structures, business logic, and data access operations
following the MVC architectural pattern.
"""

from .exceptions import (
    CodewiseError,
    GitOperationError,
    ConfigurationError,
    FileOperationError,
    ValidationError,
    LGPDComplianceError,
    NotificationError,
)

__all__ = [
    "CodewiseError",
    "GitOperationError",
    "ConfigurationError",
    "FileOperationError",
    "ValidationError",
    "LGPDComplianceError",
    "NotificationError",
]
