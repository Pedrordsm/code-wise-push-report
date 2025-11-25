"""Output formatting service for CodeWise.

This module handles formatting of analysis results for display and file output.
It provides methods to format analysis results as markdown, sanitize text,
and create structured output.
"""

import re
from typing import Optional

from ..models.analysis_models import AnalysisResult


class OutputFormatter:
    """Formatter for analysis results and output.
    
    This class provides methods to format various types of analysis results
    into human-readable formats, primarily markdown for documentation purposes.
    """
    
    @staticmethod
    def format_analysis_result(result: AnalysisResult) -> str:
        """Format a complete analysis result as markdown.
        
        Creates a comprehensive markdown document containing all analysis
        sections with proper formatting and structure.
        
        Args:
            result: The AnalysisResult to format.
            
        Returns:
            Formatted markdown string containing all analysis sections.
        """
        sections = []
        
        # Architecture section
        if result.architecture:
            sections.append("# Architecture Analysis\n")
            sections.append(OutputFormatter.sanitize_output(result.architecture))
            sections.append("\n")
        
        # Heuristics section
        if result.heuristics:
            sections.append("# Heuristics and Best Practices\n")
            sections.append(OutputFormatter.sanitize_output(result.heuristics))
            sections.append("\n")
        
        # SOLID principles section
        if result.solid:
            sections.append("# SOLID Principles Analysis\n")
            sections.append(OutputFormatter.sanitize_output(result.solid))
            sections.append("\n")
        
        # Design patterns section
        if result.patterns:
            sections.append("# Design Patterns\n")
            sections.append(OutputFormatter.sanitize_output(result.patterns))
            sections.append("\n")
        
        # Summary section
        if result.summary:
            sections.append("# Summary\n")
            sections.append(OutputFormatter.sanitize_output(result.summary))
            sections.append("\n")
        
        # Mentoring section
        if result.mentoring:
            sections.append("# Mentoring Suggestions\n")
            sections.append(OutputFormatter.sanitize_output(result.mentoring))
            sections.append("\n")
        
        return "\n".join(sections)
    
    @staticmethod
    def format_summary(summary: str) -> str:
        """Format a summary for PR description.
        
        Formats a summary text for use in pull request descriptions,
        ensuring proper markdown formatting and readability.
        
        Args:
            summary: The summary text to format.
            
        Returns:
            Formatted summary string.
        """
        # Sanitize the summary
        formatted = OutputFormatter.sanitize_output(summary)
        
        # Ensure it starts with a header if it doesn't have one
        if not formatted.startswith('#'):
            formatted = "## Summary\n\n" + formatted
        
        return formatted
    
    @staticmethod
    def format_mentoring_suggestions(suggestions: str) -> str:
        """Format mentoring suggestions for display.
        
        Formats mentoring suggestions with proper structure and emphasis
        on learning resources and improvement areas.
        
        Args:
            suggestions: The mentoring suggestions text.
            
        Returns:
            Formatted mentoring suggestions string.
        """
        formatted = OutputFormatter.sanitize_output(suggestions)
        
        # Add header if not present
        if not formatted.startswith('#'):
            formatted = "## Learning Path\n\n" + formatted
        
        return formatted
    
    @staticmethod
    def sanitize_output(text: str) -> str:
        """Sanitize text output for safe display.
        
        Removes potentially problematic characters, normalizes whitespace,
        and ensures consistent formatting.
        
        Args:
            text: The text to sanitize.
            
        Returns:
            Sanitized text string.
        """
        if not text:
            return ""
        
        # Remove any null bytes
        text = text.replace('\x00', '')
        
        # Normalize line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        # Remove excessive blank lines (more than 2 consecutive)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text
    
    @staticmethod
    def format_file_content(title: str, content: str) -> str:
        """Format content for file output with title.
        
        Creates a formatted document with a title and content,
        suitable for saving to a file.
        
        Args:
            title: The document title.
            content: The document content.
            
        Returns:
            Formatted document string.
        """
        formatted = f"# {title}\n\n"
        formatted += OutputFormatter.sanitize_output(content)
        return formatted
    
    @staticmethod
    def format_error_message(error: Exception, context: Optional[str] = None) -> str:
        """Format an error message for display.
        
        Creates a user-friendly error message with optional context.
        
        Args:
            error: The exception to format.
            context: Optional context about where the error occurred.
            
        Returns:
            Formatted error message string.
        """
        message = f"Error: {str(error)}"
        
        if context:
            message = f"{context}\n{message}"
        
        return message
    
    @staticmethod
    def format_progress_message(step: str, total_steps: int, current_step: int) -> str:
        """Format a progress message.
        
        Creates a formatted progress message showing current step and progress.
        
        Args:
            step: Description of the current step.
            total_steps: Total number of steps.
            current_step: Current step number (1-indexed).
            
        Returns:
            Formatted progress message.
        """
        percentage = int((current_step / total_steps) * 100)
        return f"[{current_step}/{total_steps}] ({percentage}%) {step}"
