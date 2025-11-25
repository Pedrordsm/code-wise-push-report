"""Data models for CodeWise analysis results and configuration.

This module defines the core data structures used throughout the CodeWise system,
including analysis results, configuration models, and notification data.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class AnalysisResult:
    """Analysis result containing all code quality assessments.
    
    This dataclass holds the complete output from a code analysis session,
    including architecture review, heuristics analysis, SOLID principles
    evaluation, design patterns assessment, summary, and mentoring suggestions.
    
    Attributes:
        architecture: Architecture analysis and recommendations.
        heuristics: Code heuristics and best practices evaluation.
        solid: SOLID principles compliance assessment.
        patterns: Design patterns identification and suggestions.
        summary: Executive summary of the analysis.
        mentoring: Personalized mentoring suggestions for improvement.
    """
    architecture: str
    heuristics: str
    solid: str
    patterns: str
    summary: str
    mentoring: str


@dataclass
class PolicyAnalysis:
    """LGPD policy analysis result for an AI provider.
    
    This dataclass holds the result of analyzing an AI provider's data
    collection policy for LGPD compliance.
    
    Attributes:
        provider: The AI provider name (e.g., 'GEMINI', 'OPENAI').
        model: The specific model being analyzed.
        compliant: Whether the provider is LGPD compliant.
        reasoning: Detailed explanation of the compliance determination.
    """
    provider: str
    model: str
    compliant: bool
    reasoning: str


@dataclass
class PerformanceScore:
    """Developer performance score from code analysis.
    
    This dataclass represents a performance score assigned to a developer
    based on code quality analysis, including justification and timestamp.
    
    Attributes:
        developer: The developer's name or identifier.
        score: Numerical score (typically 0-10).
        justification: Detailed explanation of the score.
        timestamp: When the score was generated.
    """
    developer: str
    score: int
    justification: str
    timestamp: datetime


@dataclass
class CommitInfo:
    """Information about a single Git commit.
    
    This dataclass holds metadata about a commit, including hash, author,
    date, and commit message.
    
    Attributes:
        hash: The commit SHA hash.
        author: The commit author's name.
        date: The commit date as a string.
        message: The commit message.
    """
    hash: str
    author: str
    date: str
    message: str


@dataclass
class DiffInfo:
    """Information about code changes in a diff.
    
    This dataclass holds information about code changes, including which
    files were modified and the diff content.
    
    Attributes:
        files_changed: List of file paths that were modified.
        additions: Number of lines added.
        deletions: Number of lines deleted.
        diff_content: The full diff content as a string.
    """
    files_changed: List[str]
    additions: int
    deletions: int
    diff_content: str


@dataclass
class AppConfig:
    """Application configuration loaded from environment.
    
    This dataclass holds the main application configuration, including
    AI provider settings, API keys, and notification preferences.
    
    Attributes:
        ai_provider: The AI provider to use (e.g., 'GEMINI', 'OPENAI').
        ai_model: The specific model to use.
        api_keys: Dictionary mapping provider names to API keys.
        notification_channels: List of enabled notification channels.
        notification_config: Additional notification configuration.
    """
    ai_provider: str
    ai_model: str
    api_keys: Dict[str, str]
    notification_channels: List[str]
    notification_config: Dict[str, Any]


@dataclass
class NotificationConfig:
    """Configuration for notification channels.
    
    This dataclass holds configuration for various notification channels
    including email, Slack, and webhooks.
    
    Attributes:
        enabled: Whether notifications are enabled.
        email_recipients: List of email addresses to notify.
        slack_webhook: Slack webhook URL (if configured).
        webhook_url: Generic webhook URL (if configured).
        smtp_config: SMTP server configuration for email (if configured).
    """
    enabled: bool
    email_recipients: List[str]
    slack_webhook: Optional[str]
    webhook_url: Optional[str]
    smtp_config: Optional[Dict[str, str]]
