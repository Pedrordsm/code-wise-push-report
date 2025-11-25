"""CodeWise - AI-powered code analysis tool.

This module serves as the main entry point for the CodeWise application,
handling command-line argument parsing and routing execution to the
CodewiseController.
"""

import sys
import argparse

from .controllers.codewise_controller import CodewiseController
from .models.exceptions import CodewiseError


def main():
    """Main entry point for CodeWise application.
    
    Parses command-line arguments and executes the appropriate analysis mode
    through the CodewiseController.
    
    Returns:
        Exit code (0 for success, non-zero for errors).
    """
    parser = argparse.ArgumentParser(
        description="CodeWise - AI-powered code analysis tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full code analysis
  codewise --repo /path/to/repo --branch feature-branch --mode analise
  
  # Generate PR title
  codewise --repo /path/to/repo --branch feature-branch --mode titulo
  
  # Generate PR description
  codewise --repo /path/to/repo --branch feature-branch --mode descricao
  
  # Quick lint check
  codewise --repo /path/to/repo --branch feature-branch --mode lint
  
  # Verify LGPD compliance
  codewise --repo /path/to/repo --branch main --mode lgpd_verify
"""
    )
    
    parser.add_argument(
        "--repo",
        type=str,
        required=True,
        help="Path to the Git repository to analyze"
    )
    
    parser.add_argument(
        "--branch",
        type=str,
        required=True,
        help="Name of the branch to analyze"
    )
    
    parser.add_argument(
        "--mode",
        type=str,
        required=True,
        choices=['descricao', 'analise', 'titulo', 'lint', 'lgpd_verify'],
        help="Operation mode: analise (full analysis), titulo (PR title), "
             "descricao (PR description), lint (quick check), lgpd_verify (compliance check)"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    try:
        # Create controller and execute
        controller = CodewiseController()
        exit_code = controller.execute(
            repo_path=args.repo,
            branch=args.branch,
            mode=args.mode
        )
        
        sys.exit(exit_code)
        
    except CodewiseError as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"Unexpected error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()