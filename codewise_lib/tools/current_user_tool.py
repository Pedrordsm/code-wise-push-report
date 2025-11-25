"""Tool to get the current Git user information."""

from crewai.tools import BaseTool
from pydantic import BaseModel
from typing import Type
import subprocess


class CurrentUserInput(BaseModel):
    """Schema for current user tool - no input needed."""
    pass


class CurrentUserTool(BaseTool):
    name: str = "Obter usuário Git atual"
    description: str = (
        "Obtém o nome do usuário Git configurado no repositório local. "
        "Use esta ferramenta para identificar o desenvolvedor atual."
    )
    args_schema: Type[BaseModel] = CurrentUserInput

    def _run(self) -> str:
        try:
            # Get git user name
            result = subprocess.run(
                ['git', 'config', 'user.name'],
                capture_output=True,
                text=True,
                check=True
            )
            
            user_name = result.stdout.strip()
            
            if not user_name:
                return "Erro: Nome de usuário Git não configurado."
            
            return f"Usuário Git atual: {user_name}"
            
        except subprocess.CalledProcessError:
            return "Erro: Não foi possível obter o nome do usuário Git."
        except Exception as e:
            return f"Erro inesperado: {e}"
