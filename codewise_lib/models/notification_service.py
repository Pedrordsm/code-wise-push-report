"""Notification service for sending performance scores.

This module handles sending performance score notifications to various channels
including email, Slack, and webhooks. It loads configuration from environment
variables and handles delivery failures gracefully without blocking workflows.
"""

import os
import json
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional
from datetime import datetime
import requests

from .analysis_models import PerformanceScore, NotificationConfig
from .exceptions import NotificationError


# Configure logging
logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending performance score notifications.
    
    This class manages notification delivery to multiple channels (email, Slack,
    webhooks). It handles configuration loading, message formatting, and graceful
    error handling to ensure notification failures don't block main workflows.
    """
    
    def __init__(self):
        """Initialize NotificationService and load configuration from environment."""
        self.config = self._load_configuration()
    
    def _load_configuration(self) -> NotificationConfig:
        """Load notification configuration from environment variables.
        
        Returns:
            NotificationConfig with loaded settings.
        """
        # Check if notifications are enabled
        enabled = os.getenv("NOTIFICATIONS_ENABLED", "false").lower() == "true"
        
        # Load email recipients
        email_recipients_str = os.getenv("NOTIFICATION_EMAIL_RECIPIENTS", "")
        email_recipients = [
            email.strip()
            for email in email_recipients_str.split(",")
            if email.strip()
        ]
        
        # Load Slack webhook
        slack_webhook = os.getenv("NOTIFICATION_SLACK_WEBHOOK")
        
        # Load generic webhook
        webhook_url = os.getenv("NOTIFICATION_WEBHOOK_URL")
        
        # Load SMTP configuration
        smtp_config = None
        if os.getenv("SMTP_HOST"):
            smtp_config = {
                "host": os.getenv("SMTP_HOST"),
                "port": int(os.getenv("SMTP_PORT", "587")),
                "username": os.getenv("SMTP_USERNAME", ""),
                "password": os.getenv("SMTP_PASSWORD", ""),
                "from_email": os.getenv("SMTP_FROM_EMAIL", "codewise@example.com")
            }
        
        return NotificationConfig(
            enabled=enabled,
            email_recipients=email_recipients,
            slack_webhook=slack_webhook,
            webhook_url=webhook_url,
            smtp_config=smtp_config
        )
    
    def send_score_notification(
        self,
        developer: str,
        score: int,
        justification: str
    ) -> bool:
        """Send performance score notification to all configured channels.
        
        This method attempts to send notifications to all configured channels.
        Failures are logged but don't raise exceptions to avoid blocking the
        main workflow.
        
        Args:
            developer: The developer's name or identifier.
            score: The performance score (0-10).
            justification: Detailed explanation of the score.
            
        Returns:
            True if at least one notification was sent successfully, False otherwise.
        """
        if not self.config.enabled:
            logger.info("Notifications are disabled")
            return False
        
        # Create performance score object
        perf_score = PerformanceScore(
            developer=developer,
            score=score,
            justification=justification,
            timestamp=datetime.now()
        )
        
        success_count = 0
        
        # Try email
        if self.config.email_recipients and self.config.smtp_config:
            try:
                if self.send_email(developer, score, justification):
                    success_count += 1
            except Exception as e:
                logger.warning(f"Email notification failed: {str(e)}")
        
        # Try Slack
        if self.config.slack_webhook:
            try:
                if self.send_slack_message(developer, score, justification):
                    success_count += 1
            except Exception as e:
                logger.warning(f"Slack notification failed: {str(e)}")
        
        # Try webhook
        if self.config.webhook_url:
            try:
                if self.send_webhook(developer, score, justification):
                    success_count += 1
            except Exception as e:
                logger.warning(f"Webhook notification failed: {str(e)}")
        
        return success_count > 0
    
    def send_email(self, developer: str, score: int, justification: str) -> bool:
        """Send performance score via email.
        
        Args:
            developer: The developer's name.
            score: The performance score.
            justification: Score justification.
            
        Returns:
            True if email was sent successfully.
            
        Raises:
            NotificationError: If email sending fails.
        """
        if not self.config.smtp_config:
            raise NotificationError("email", "SMTP configuration not available")
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.config.smtp_config['from_email']
            msg['To'] = ', '.join(self.config.email_recipients)
            msg['Subject'] = f"CodeWise: Performance Score for {developer}"
            
            # Create email body
            body = f"""
CodeWise Performance Report

Developer: {developer}
Score: {score}/10
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Justification:
{justification}

---
This is an automated message from CodeWise.
"""
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(
                self.config.smtp_config['host'],
                self.config.smtp_config['port']
            ) as server:
                server.starttls()
                if self.config.smtp_config['username']:
                    server.login(
                        self.config.smtp_config['username'],
                        self.config.smtp_config['password']
                    )
                server.send_message(msg)
            
            logger.info(f"Email notification sent for {developer}")
            return True
            
        except Exception as e:
            raise NotificationError("email", str(e))
    
    def send_slack_message(self, developer: str, score: int, justification: str) -> bool:
        """Send performance score to Slack.
        
        Args:
            developer: The developer's name.
            score: The performance score.
            justification: Score justification.
            
        Returns:
            True if Slack message was sent successfully.
            
        Raises:
            NotificationError: If Slack sending fails.
        """
        if not self.config.slack_webhook:
            raise NotificationError("slack", "Slack webhook URL not configured")
        
        try:
            # Determine color based on score
            if score >= 9:
                color = "good"  # Green
            elif score >= 5:
                color = "warning"  # Yellow
            else:
                color = "danger"  # Red
            
            # Create Slack message
            payload = {
                "attachments": [
                    {
                        "color": color,
                        "title": f"Performance Score: {developer}",
                        "fields": [
                            {
                                "title": "Score",
                                "value": f"{score}/10",
                                "short": True
                            },
                            {
                                "title": "Timestamp",
                                "value": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                "short": True
                            },
                            {
                                "title": "Justification",
                                "value": justification,
                                "short": False
                            }
                        ],
                        "footer": "CodeWise",
                        "footer_icon": "https://platform.slack-edge.com/img/default_application_icon.png"
                    }
                ]
            }
            
            # Send to Slack
            response = requests.post(
                self.config.slack_webhook,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            logger.info(f"Slack notification sent for {developer}")
            return True
            
        except Exception as e:
            raise NotificationError("slack", str(e))
    
    def send_webhook(self, developer: str, score: int, justification: str) -> bool:
        """Send performance score to a generic webhook.
        
        Args:
            developer: The developer's name.
            score: The performance score.
            justification: Score justification.
            
        Returns:
            True if webhook was called successfully.
            
        Raises:
            NotificationError: If webhook call fails.
        """
        if not self.config.webhook_url:
            raise NotificationError("webhook", "Webhook URL not configured")
        
        try:
            # Create webhook payload
            payload = {
                "event": "performance_score",
                "developer": developer,
                "score": score,
                "justification": justification,
                "timestamp": datetime.now().isoformat()
            }
            
            # Send to webhook
            response = requests.post(
                self.config.webhook_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            response.raise_for_status()
            
            logger.info(f"Webhook notification sent for {developer}")
            return True
            
        except Exception as e:
            raise NotificationError("webhook", str(e))
