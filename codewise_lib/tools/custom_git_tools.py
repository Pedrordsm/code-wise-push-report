from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type
import subprocess
import os
from collections import Counter

# ======================================================
# FERRAMENTA 1: OWNERSHIP (Quem é dono do arquivo)
# ======================================================

class OwnershipInput(BaseModel):
    """Schema de entrada para a ferramenta de Ownership."""
    file_path: str = Field(..., description="Caminho relativo do arquivo para analisar (ex: 'main.py').")

class OwnershipTool(BaseTool):
    name: str = "Calcular Ownership por Arquivo"
    description: str = (
        "Usa 'git blame' para calcular a porcentagem exata de linhas que cada autor "
        "possui em um arquivo específico. Retorna estatísticas de quem é o 'dono'."
    )
    args_schema: Type[BaseModel] = OwnershipInput

    def _run(self, file_path: str) -> str:
        try:
            if not os.path.exists(file_path):
                return f"Erro: O arquivo '{file_path}' não foi encontrado."

            result = subprocess.run(
                ['git', 'blame', '--line-porcelain', file_path],
                capture_output=True, text=True, check=True
            )

            authors = [
                line.replace("author ", "") 
                for line in result.stdout.splitlines() 
                if line.startswith("author ")
            ]

            if not authors:
                return f"O arquivo {file_path} parece estar vazio ou não commitado."

            total_lines = len(authors)
            counts = Counter(authors)

            summary = f"--- RELATÓRIO DE OWNERSHIP: {file_path} ---\n"
            summary += f"Total de linhas: {total_lines}\n"
            
            for author, count in counts.most_common():
                percent = (count / total_lines) * 100
                summary += f"👤 {author}: {percent:.1f}% ({count} linhas)\n"

            return summary

        except subprocess.CalledProcessError:
            return f"Erro: Falha ao rodar git blame em '{file_path}'."
        except Exception as e:
            return f"Erro inesperado: {e}"


# ======================================================
# FERRAMENTA 2: COMMIT HISTORY (Histórico do usuário)
# ======================================================

class UserCommitsInput(BaseModel):
    """Schema de entrada para a ferramenta de Histórico."""
    author_name: str = Field(..., description="Nome do autor para buscar os commits.")
    limit: int = Field(5, description="Número de commits recentes para buscar.")

class UserCommitsTool(BaseTool):
    name: str = "Ler Histórico de Commits do Usuário"
    description: str = (
        "Busca os últimos commits de um autor específico. "
        "Retorna Hash, Data, Mensagem e arquivos alterados."
    )
    args_schema: Type[BaseModel] = UserCommitsInput

    def _run(self, author_name: str, limit: int = 5) -> str:
        try:
            cmd = [
                'git', 'log', 
                f'--author={author_name}', 
                f'-n {limit}', 
                '--pretty=format:--- COMMIT: %h | DATA: %ad | MSG: %s', 
                '--stat', 
                '--date=short'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if not result.stdout:
                return f"Nenhum commit encontrado para o autor: '{author_name}'."
                
            return result.stdout

        except Exception as e:
            return f"Erro ao buscar commits: {e}"


# ======================================================
# FERRAMENTA 3: DIFF READER (Ler código alterado)
# ======================================================

class CommitDiffInput(BaseModel):
    """Schema de entrada para a ferramenta de Diff."""
    commit_hash: str = Field(..., description="O hash (ID) do commit para ler o código.")

class CommitDiffTool(BaseTool):
    name: str = "Ler Código do Commit (Diff)"
    description: str = (
        "Obtém as alterações de código (diff) de um commit específico pelo seu HASH. "
        "Use isso para analisar a qualidade técnica do código."
    )
    args_schema: Type[BaseModel] = CommitDiffInput

    def _run(self, commit_hash: str) -> str:
        try:
            cmd = ['git', 'show', commit_hash, '--pretty=format:', '--patch']
            result = subprocess.run(cmd, capture_output=True, text=True)
            output = result.stdout
            
            if not output:
                return f"Não foi possível ler o diff do hash {commit_hash}."

            limit_chars = 6000
            if len(output) > limit_chars:
                return output[:limit_chars] + f"\n\n... [TRUNCADO: O diff excede {limit_chars} caracteres] ..."
            
            return output

        except Exception as e:
            return f"Erro ao ler diff: {e}"