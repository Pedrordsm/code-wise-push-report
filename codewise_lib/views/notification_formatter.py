"""Notification formatting service for CodeWise.

This module handles formatting of performance score notifications for different
channels (email, Slack, webhooks), ensuring consistent and appropriate formatting
for each delivery method.
"""

from typing import Dict, Tuple
from datetime import datetime

from ..models.analysis_models import PerformanceScore


class NotificationFormatter:
    """Formatter for notification messages.
    
    This class provides methods to format performance score notifications
    for various channels, ensuring each channel receives appropriately
    formatted content.
    """
    
    @staticmethod
    def format_email_notification(score: PerformanceScore) -> Tuple[str, str]:
        """Format a performance score for email notification.
        
        Creates both subject and body text for an email notification.
        
        Args:
            score: The PerformanceScore to format.
            
        Returns:
            Tuple of (subject, body) strings for the email.
        """
        # Create subject
        subject = f"CodeWise: Performance Score for {score.developer} - {score.score}/10"
        
        # Create body
        body = f"""
CodeWise Performance Report
{'=' * 50}

Developer: {score.developer}
Score: {score.score}/10
Timestamp: {score.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

{'=' * 50}

Justification:
{score.justification}

{'=' * 50}

Score Interpretation:
- 9-10: Excellent - Code is exemplary, well-tested, and documented
- 5-8:  Good - Code is functional but has room for improvement
- 0-4:  Needs Improvement - Significant issues found

{'=' * 50}

This is an automated message from CodeWise.
For questions or concerns, please contact your team lead.
"""
        
        return (subject, body)
    
    @staticmethod
    def format_slack_notification(score: PerformanceScore) -> Dict:
        """Format a performance score for Slack notification.
        
        Creates a Slack message payload with rich formatting using attachments.
        
        Args:
            score: The PerformanceScore to format.
            
        Returns:
            Dictionary containing Slack message payload.
        """
        # Determine color based on score
        if score.score >= 9:
            color = "good"  # Green
            emoji = ":star:"
        elif score.score >= 5:
            color = "warning"  # Yellow
            emoji = ":large_blue_circle:"
        else:
            color = "danger"  # Red
            emoji = ":warning:"
        
        # Create Slack payload
        payload = {
            "text": f"{emoji} Performance Score Update",
            "attachments": [
                {
                    "color": color,
                    "title": f"Performance Score: {score.developer}",
                    "fields": [
                        {
                            "title": "Score",
                            "value": f"*{score.score}/10*",
                            "short": True
                        },
                        {
                            "title": "Timestamp",
                            "value": score.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                            "short": True
                        },
                        {
                            "title": "Justification",
                            "value": score.justification,
                            "short": False
                        }
                    ],
                    "footer": "CodeWise",
                    "footer_icon": "https://platform.slack-edge.com/img/default_application_icon.png",
                    "ts": int(score.timestamp.timestamp())
                }
            ]
        }
        
        return payload
    
    @staticmethod
    def format_webhook_payload(score: PerformanceScore) -> Dict:
        """Format a performance score for generic webhook notification.
        
        Creates a JSON payload suitable for generic webhook endpoints.
        
        Args:
            score: The PerformanceScore to format.
            
        Returns:
            Dictionary containing webhook payload.
        """
        payload = {
            "event": "performance_score",
            "data": {
                "developer": score.developer,
                "score": score.score,
                "max_score": 10,
                "justification": score.justification,
                "timestamp": score.timestamp.isoformat(),
                "timestamp_unix": int(score.timestamp.timestamp())
            },
            "metadata": {
                "source": "codewise",
                "version": "1.0",
                "score_level": NotificationFormatter._get_score_level(score.score)
            }
        }
        
        return payload
    
    @staticmethod
    def _get_score_level(score: int) -> str:
        """Get the score level category.
        
        Args:
            score: The numerical score (0-10).
            
        Returns:
            String describing the score level.
        """
        if score >= 9:
            return "excellent"
        elif score >= 7:
            return "good"
        elif score >= 5:
            return "satisfactory"
        elif score >= 3:
            return "needs_improvement"
        else:
            return "critical"
    
    @staticmethod
    def format_console_notification(score: PerformanceScore) -> str:
        """Format a performance score for console display.
        
        Creates a formatted text output suitable for terminal display.
        
        Args:
            score: The PerformanceScore to format.
            
        Returns:
            Formatted string for console output.
        """
        separator = "=" * 60
        
        output = f"""
{separator}
PERFORMANCE SCORE NOTIFICATION
{separator}

Developer: {score.developer}
Score: {score.score}/10
Level: {NotificationFormatter._get_score_level(score.score).replace('_', ' ').title()}
Timestamp: {score.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

{separator}
JUSTIFICATION
{separator}

{score.justification}

{separator}
"""
        
        return output
    
    @staticmethod
    def format_summary_notification(scores: list) -> str:
        """Format multiple performance scores as a summary.
        
        Creates a summary report of multiple scores, useful for batch
        notifications or reports.
        
        Args:
            scores: List of PerformanceScore objects.
            
        Returns:
            Formatted summary string.
        """
        if not scores:
            return "No performance scores to report."
        
        separator = "=" * 60
        output = [f"\n{separator}"]
        output.append("PERFORMANCE SCORES SUMMARY")
        output.append(separator)
        output.append(f"\nTotal Developers: {len(scores)}")
        
        # Calculate statistics
        total_score = sum(s.score for s in scores)
        avg_score = total_score / len(scores)
        
        output.append(f"Average Score: {avg_score:.1f}/10")
        output.append(f"\n{separator}")
        output.append("INDIVIDUAL SCORES")
        output.append(separator)
        
        # Sort by score (descending)
        sorted_scores = sorted(scores, key=lambda s: s.score, reverse=True)
        
        for score in sorted_scores:
            level = NotificationFormatter._get_score_level(score.score)
            output.append(f"\n{score.developer}: {score.score}/10 ({level})")
        
        output.append(f"\n{separator}\n")
        
        return "\n".join(output)
