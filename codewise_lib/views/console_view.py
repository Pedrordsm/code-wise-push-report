"""Console output service for CodeWise.

This module handles all terminal/console output, providing methods for
displaying progress messages, errors, warnings, and results with consistent
formatting.
"""

import sys
from typing import Optional


class ConsoleView:
    """Service for console/terminal output.
    
    This class provides methods for displaying various types of messages
    to the console with consistent formatting and color coding (where supported).
    """
    
    # ANSI color codes for terminal output
    COLORS = {
        'reset': '\033[0m',
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'magenta': '\033[95m',
        'cyan': '\033[96m',
        'white': '\033[97m',
        'bold': '\033[1m'
    }
    
    def __init__(self, use_colors: bool = True):
        """Initialize ConsoleView.
        
        Args:
            use_colors: Whether to use ANSI color codes in output.
                       Defaults to True. Set to False for environments
                       that don't support ANSI colors.
        """
        self.use_colors = use_colors and sys.stdout.isatty()
    
    def _colorize(self, text: str, color: str) -> str:
        """Apply color to text if colors are enabled.
        
        Args:
            text: The text to colorize.
            color: The color name (from COLORS dict).
            
        Returns:
            Colorized text if colors are enabled, plain text otherwise.
        """
        if not self.use_colors or color not in self.COLORS:
            return text
        
        return f"{self.COLORS[color]}{text}{self.COLORS['reset']}"
    
    def print_progress(self, message: str) -> None:
        """Print a progress message to stdout.
        
        Progress messages are displayed in cyan with an info icon.
        
        Args:
            message: The progress message to display.
        """
        formatted = self._colorize(f"[INFO] {message}", 'cyan')
        print(formatted, file=sys.stdout)
    
    def print_success(self, message: str) -> None:
        """Print a success message to stdout.
        
        Success messages are displayed in green with a checkmark.
        
        Args:
            message: The success message to display.
        """
        formatted = self._colorize(f"[OK] {message}", 'green')
        print(formatted, file=sys.stdout)
    
    def print_error(self, message: str) -> None:
        """Print an error message to stderr.
        
        Error messages are displayed in red with an error icon.
        
        Args:
            message: The error message to display.
        """
        formatted = self._colorize(f"[ERROR] {message}", 'red')
        print(formatted, file=sys.stderr)
    
    def print_warning(self, message: str) -> None:
        """Print a warning message to stderr.
        
        Warning messages are displayed in yellow with a warning icon.
        
        Args:
            message: The warning message to display.
        """
        formatted = self._colorize(f"[WARNING] {message}", 'yellow')
        print(formatted, file=sys.stderr)
    
    def print_result(self, result: str) -> None:
        """Print a result message to stdout.
        
        Result messages are displayed without special formatting.
        
        Args:
            result: The result to display.
        """
        print(result, file=sys.stdout)
    
    def print_header(self, title: str) -> None:
        """Print a section header.
        
        Headers are displayed in bold with decorative lines.
        
        Args:
            title: The header title.
        """
        separator = "=" * len(title)
        formatted_title = self._colorize(title, 'bold')
        print(f"\n{separator}", file=sys.stdout)
        print(formatted_title, file=sys.stdout)
        print(f"{separator}\n", file=sys.stdout)
    
    def print_step(self, step_num: int, total_steps: int, description: str) -> None:
        """Print a step indicator.
        
        Step indicators show progress through a multi-step process.
        
        Args:
            step_num: Current step number (1-indexed).
            total_steps: Total number of steps.
            description: Description of the current step.
        """
        formatted = self._colorize(
            f"[{step_num}/{total_steps}] {description}",
            'blue'
        )
        print(formatted, file=sys.stdout)
    
    def print_separator(self) -> None:
        """Print a visual separator line."""
        print("-" * 80, file=sys.stdout)
    
    def print_blank_line(self) -> None:
        """Print a blank line for spacing."""
        print("", file=sys.stdout)
    
    def prompt_user(self, message: str, default: Optional[str] = None) -> str:
        """Prompt the user for input.
        
        Args:
            message: The prompt message.
            default: Optional default value if user presses Enter.
            
        Returns:
            The user's input or the default value.
        """
        if default:
            prompt = f"{message} [{default}]: "
        else:
            prompt = f"{message}: "
        
        formatted_prompt = self._colorize(prompt, 'yellow')
        response = input(formatted_prompt).strip()
        
        return response if response else (default or "")
    
    def print_list(self, items: list, bullet: str = "-") -> None:
        """Print a list of items.
        
        Args:
            items: List of items to display.
            bullet: Bullet character to use. Defaults to '-'.
        """
        for item in items:
            print(f"  {bullet} {item}", file=sys.stdout)
    
    def clear_line(self) -> None:
        """Clear the current line (for progress updates)."""
        if self.use_colors:
            print('\r\033[K', end='', file=sys.stdout)
    
    def print_table(self, headers: list, rows: list) -> None:
        """Print a simple table.
        
        Args:
            headers: List of column headers.
            rows: List of rows, where each row is a list of values.
        """
        # Calculate column widths
        col_widths = [len(str(h)) for h in headers]
        for row in rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(cell)))
        
        # Print header
        header_row = " | ".join(
            str(h).ljust(w) for h, w in zip(headers, col_widths)
        )
        print(self._colorize(header_row, 'bold'), file=sys.stdout)
        print("-" * len(header_row), file=sys.stdout)
        
        # Print rows
        for row in rows:
            row_str = " | ".join(
                str(cell).ljust(w) for cell, w in zip(row, col_widths)
            )
            print(row_str, file=sys.stdout)
