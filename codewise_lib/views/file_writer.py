"""File writing service for CodeWise.

This module handles all file I/O operations for saving analysis results,
creating output directories, and managing file writes with proper error handling.
"""

import os
from pathlib import Path
from typing import Dict

from ..models.analysis_models import AnalysisResult
from ..models.exceptions import FileOperationError


class FileWriter:
    """Service for file writing operations.
    
    This class provides methods for writing analysis results to files,
    creating directories, and handling file operations with proper error
    handling and validation.
    """
    
    def __init__(self, base_output_dir: str = "codewise_output"):
        """Initialize FileWriter with base output directory.
        
        Args:
            base_output_dir: Base directory for output files.
                           Defaults to 'codewise_output'.
        """
        self.base_output_dir = Path(base_output_dir)
    
    def ensure_directory(self, path: str) -> bool:
        """Ensure a directory exists, creating it if necessary.
        
        Args:
            path: Path to the directory.
            
        Returns:
            True if directory exists or was created successfully.
            
        Raises:
            FileOperationError: If directory creation fails.
        """
        try:
            dir_path = Path(path)
            dir_path.mkdir(parents=True, exist_ok=True)
            return True
        except PermissionError:
            raise FileOperationError(
                "mkdir",
                path,
                "Permission denied. Check directory permissions."
            )
        except OSError as e:
            raise FileOperationError(
                "mkdir",
                path,
                f"Failed to create directory: {str(e)}"
            )
    
    def write_file(self, path: str, content: str) -> bool:
        """Write content to a file.
        
        Creates parent directories if they don't exist and writes the
        content to the specified file.
        
        Args:
            path: Path to the file to write.
            content: Content to write to the file.
            
        Returns:
            True if file was written successfully.
            
        Raises:
            FileOperationError: If file writing fails.
        """
        try:
            file_path = Path(path)
            
            # Ensure parent directory exists
            if file_path.parent != Path('.'):
                self.ensure_directory(str(file_path.parent))
            
            # Write file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return True
            
        except PermissionError:
            raise FileOperationError(
                "write",
                path,
                "Permission denied. Check file permissions."
            )
        except OSError as e:
            raise FileOperationError(
                "write",
                path,
                f"Failed to write file: {str(e)}"
            )
    
    def write_analysis_files(self, output_dir: str, result: AnalysisResult) -> bool:
        """Write all analysis result files to a directory.
        
        Creates separate files for each analysis section (architecture,
        heuristics, SOLID, patterns, summary, mentoring).
        
        Args:
            output_dir: Directory to write files to.
            result: The AnalysisResult containing all analysis sections.
            
        Returns:
            True if all files were written successfully.
            
        Raises:
            FileOperationError: If any file writing fails.
        """
        # Ensure output directory exists
        self.ensure_directory(output_dir)
        
        # Define file mappings
        files_to_write: Dict[str, str] = {}
        
        if result.architecture:
            files_to_write["arquitetura_atual.md"] = result.architecture
        
        if result.heuristics:
            files_to_write["analise_heuristicas_integracoes.md"] = result.heuristics
        
        if result.solid:
            files_to_write["analise_solid.md"] = result.solid
        
        if result.patterns:
            files_to_write["padroes_de_projeto.md"] = result.patterns
        
        if result.summary:
            files_to_write["resumo.md"] = result.summary
        
        if result.mentoring:
            files_to_write["sugestoes_aprendizado.md"] = result.mentoring
        
        # Write all files
        for filename, content in files_to_write.items():
            file_path = os.path.join(output_dir, filename)
            self.write_file(file_path, content)
        
        return True
    
    def append_to_file(self, path: str, content: str) -> bool:
        """Append content to an existing file.
        
        Args:
            path: Path to the file.
            content: Content to append.
            
        Returns:
            True if content was appended successfully.
            
        Raises:
            FileOperationError: If appending fails.
        """
        try:
            file_path = Path(path)
            
            # Ensure parent directory exists
            if file_path.parent != Path('.'):
                self.ensure_directory(str(file_path.parent))
            
            # Append to file
            with open(file_path, 'a', encoding='utf-8') as f:
                f.write(content)
            
            return True
            
        except PermissionError:
            raise FileOperationError(
                "append",
                path,
                "Permission denied. Check file permissions."
            )
        except OSError as e:
            raise FileOperationError(
                "append",
                path,
                f"Failed to append to file: {str(e)}"
            )
    
    def file_exists(self, path: str) -> bool:
        """Check if a file exists.
        
        Args:
            path: Path to the file.
            
        Returns:
            True if file exists, False otherwise.
        """
        return Path(path).exists()
    
    def delete_file(self, path: str) -> bool:
        """Delete a file.
        
        Args:
            path: Path to the file to delete.
            
        Returns:
            True if file was deleted successfully.
            
        Raises:
            FileOperationError: If deletion fails.
        """
        try:
            file_path = Path(path)
            
            if not file_path.exists():
                return True  # File doesn't exist, consider it deleted
            
            file_path.unlink()
            return True
            
        except PermissionError:
            raise FileOperationError(
                "delete",
                path,
                "Permission denied. Check file permissions."
            )
        except OSError as e:
            raise FileOperationError(
                "delete",
                path,
                f"Failed to delete file: {str(e)}"
            )
