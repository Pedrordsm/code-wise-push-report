"""Git operations service for CodeWise.

This module encapsulates all Git operations, providing a clean interface for
interacting with Git repositories. It handles command execution, error handling,
and output parsing.
"""

import subprocess
import sys
from typing import Dict, List, Optional

from .exceptions import GitOperationError


class GitService:
    """Service class for Git operations.
    
    This class provides methods for common Git operations such as fetching updates,
    getting commit ranges, generating diffs, and retrieving blame information.
    All Git errors are caught and converted to GitOperationError exceptions with
    contextual information.
    """
    
    def __init__(self, repo_path: str = "."):
        """Initialize GitService with a repository path.
        
        Args:
            repo_path: Path to the Git repository. Defaults to current directory.
        """
        self.repo_path = repo_path
    
    def _run_command(self, command: List[str]) -> str:
        """Execute a Git command and return its output.
        
        This is a private helper method that executes Git commands safely,
        handling errors and encoding issues.
        
        Args:
            command: List of command arguments (e.g., ['git', 'status']).
            
        Returns:
            The command output as a string, stripped of whitespace.
            
        Raises:
            GitOperationError: If the command fails or Git is not found.
        """
        try:
            result = subprocess.check_output(
                command,
                cwd=self.repo_path,
                text=True,
                encoding='utf-8',
                stderr=subprocess.PIPE
            )
            return result.strip()
        except subprocess.CalledProcessError as e:
            # Git command failed
            error_msg = e.stderr.strip() if e.stderr else str(e)
            operation = ' '.join(command[1:])  # Skip 'git' prefix
            raise GitOperationError(operation, self.repo_path, error_msg)
        except FileNotFoundError:
            # Git executable not found
            raise GitOperationError(
                'execute',
                self.repo_path,
                "Git executable not found. Please ensure Git is installed and in PATH."
            )
        except Exception as e:
            # Unexpected error
            operation = ' '.join(command[1:]) if len(command) > 1 else 'unknown'
            raise GitOperationError(operation, self.repo_path, str(e))
    
  
    def fetch_updates(self, branch: str) -> bool:
        """Fetch updates from the remote repository.
        
        Fetches the latest changes from the origin remote, pruning deleted branches.
        
        Args:
            branch: The branch name to fetch.
            
        Returns:
            True if fetch was successful.
            
        Raises:
            GitOperationError: If the fetch operation fails.
        """
        try:
            self._run_command(["git", "fetch", "origin", "--prune"])
            return True
        except GitOperationError:
            raise
    
    def get_commit_range(self, base_ref: str, branch: str) -> List[str]:
        """Get list of commit messages in a range.
        
        Retrieves commit messages between a base reference and a branch,
        useful for generating changelogs or PR descriptions.
        
        Args:
            base_ref: The base reference (e.g., 'origin/main').
            branch: The target branch name.
            
        Returns:
            List of commit messages, one per commit.
            
        Raises:
            GitOperationError: If the log operation fails.
        """
        range_commits = f"{base_ref}..{branch}"
        log_output = self._run_command([
            "git", "log", "--pretty=format:- %s", range_commits
        ])
        
        if not log_output:
            return []
        
        return log_output.splitlines()
    
    def get_diff(self, base_ref: str, branch: str) -> str:
        """Get the diff between a base reference and a branch.
        
        Generates a unified diff showing all changes between the base
        reference and the target branch.
        
        Args:
            base_ref: The base reference (e.g., 'origin/main').
            branch: The target branch name.
            
        Returns:
            The diff content as a string.
            
        Raises:
            GitOperationError: If the diff operation fails.
        """
        diff_range = f"{base_ref}..{branch}"
        return self._run_command(["git", "diff", diff_range])
    
    def get_staged_changes(self) -> Optional[str]:
        """Get staged changes from the repository.
        
        Checks for changes in the staging area. If no staged changes exist,
        checks the working directory for unstaged changes.
        
        Returns:
            The diff of staged changes, a warning message if only unstaged
            changes exist, or None if no changes are present.
            
        Raises:
            GitOperationError: If Git operations fail.
        """
        try:
            # Check staging area first
            diff_staged = self._run_command(["git", "diff", "--cached"])
            if diff_staged:
                return diff_staged
            
            # Check working directory
            diff_working = self._run_command(["git", "diff"])
            if diff_working:
                return ("WARNING: No changes in staging area, but unstaged modifications exist.\n"
                       "Use 'git add <file>' to stage them for analysis.")
            
            # No changes at all
            return None
        except GitOperationError:
            raise
    
    def get_blame(self, file_path: str) -> Dict[str, int]:
        """Get blame information for a file.
        
        Retrieves Git blame information showing which authors modified
        which lines in a file.
        
        Args:
            file_path: Path to the file relative to repository root.
            
        Returns:
            Dictionary mapping author names to line counts.
            
        Raises:
            GitOperationError: If the blame operation fails.
        """
        try:
            blame_output = self._run_command(["git", "blame", "--line-porcelain", file_path])
            
            # Parse blame output to count lines per author
            author_lines: Dict[str, int] = {}
            for line in blame_output.splitlines():
                if line.startswith('author '):
                    author = line[7:]  # Remove 'author ' prefix
                    author_lines[author] = author_lines.get(author, 0) + 1
            
            return author_lines
        except GitOperationError:
            raise
    
    def branch_exists_on_remote(self, branch: str) -> bool:
        """Check if a branch exists on the remote.
        
        Args:
            branch: The branch name to check.
            
        Returns:
            True if the branch exists on origin, False otherwise.
        """
        try:
            remote_ref = f"refs/remotes/origin/{branch}"
            result = self._run_command(["git", "show-ref", "--verify", remote_ref])
            return bool(result)
        except GitOperationError:
            # Branch doesn't exist on remote
            return False
    
    def get_default_branch(self) -> str:
        """Get the default branch name for the repository.
        
        Attempts to determine the default branch (usually 'main' or 'master').
        
        Returns:
            The default branch name, defaults to 'main' if detection fails.
        """
        try:
            # Try to get the default branch from remote HEAD
            result = self._run_command([
                "git", "symbolic-ref", "refs/remotes/origin/HEAD"
            ])
            # Extract branch name from refs/remotes/origin/branch_name
            if result:
                return result.split('/')[-1]
        except GitOperationError:
            pass
        
        # Try to detect from remote branches
        try:
            remote_branches = self._run_command(["git", "ls-remote", "--heads", "origin"])
            if remote_branches:
                # Check for common default branch names
                if "refs/heads/main" in remote_branches:
                    return "main"
                elif "refs/heads/master" in remote_branches:
                    return "master"
                # Return the first branch found
                first_branch = remote_branches.split('\n')[0]
                if first_branch:
                    branch_name = first_branch.split('refs/heads/')[-1]
                    return branch_name
        except GitOperationError:
            pass
        
        # Fallback to 'main'
        return "main"
