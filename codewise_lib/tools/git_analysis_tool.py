import os
import subprocess
import tempfile
from typing import Optional


class GitAnalysisTool:
    """Ferramenta para analisar mudanças do Git usando git log e git blame."""
    
    name: str = "Git Analysis Tool"
    description: str = (
        "Ferramenta para analisar mudanças do Git usando git log e git blame. "
        "Retorna informações detalhadas sobre commits, autores, e mudanças no código."
    )

    def run(self, repo_path: str, author_email: Optional[str] = None, 
             commits_limit: int = 10, branch: str = "HEAD") -> str:
        """
        Analisa o repositório Git e retorna informações sobre commits e mudanças.
        
        Args:
            repo_path: Caminho para o repositório Git
            author_email: Email do autor para filtrar (opcional)
            commits_limit: Número de commits a analisar
            branch: Branch a ser analisada
        """
        try:
            # Verifica se é um repositório Git válido
            if not os.path.exists(os.path.join(repo_path, '.git')):
                return f"Erro: {repo_path} não é um repositório Git válido."

            result = []
            result.append("=" * 80)
            result.append("ANÁLISE DE MUDANÇAS GIT")
            result.append("=" * 80)
            result.append("")

            # Comando git log com informações detalhadas
            git_log_cmd = [
                'git', '-C', repo_path, 'log',
                f'-{commits_limit}',
                '--pretty=format:%H|%an|%ae|%ad|%s',
                '--date=iso',
                '--numstat',
                branch
            ]

            if author_email:
                git_log_cmd.extend(['--author', author_email])

            log_output = subprocess.check_output(
                git_log_cmd,
                stderr=subprocess.STDOUT,
                text=True
            )

            # Processa a saída do git log
            commits_data = self._parse_git_log(log_output)
            
            for commit in commits_data:
                result.append(f"Commit: {commit['hash'][:8]}")
                result.append(f"Autor: {commit['author']} <{commit['email']}>")
                result.append(f"Data: {commit['date']}")
                result.append(f"Mensagem: {commit['message']}")
                result.append("")
                
                if commit['files']:
                    result.append("Arquivos modificados:")
                    for file_info in commit['files']:
                        result.append(f"  {file_info['additions']:>4}+ {file_info['deletions']:>4}- {file_info['file']}")
                    result.append("")

                # Git diff para ver as mudanças reais
                try:
                    diff_cmd = ['git', '-C', repo_path, 'show', 
                               '--pretty=format:', '--unified=3', commit['hash']]
                    diff_output = subprocess.check_output(
                        diff_cmd,
                        stderr=subprocess.STDOUT,
                        text=True
                    )
                    if diff_output.strip():
                        result.append("Mudanças no código:")
                        result.append(diff_output[:2000])  # Limita o tamanho
                        result.append("")
                except:
                    pass

                result.append("-" * 80)
                result.append("")

            return "\n".join(result)

        except subprocess.CalledProcessError as e:
            return f"Erro ao executar comando Git: {e.output}"
        except Exception as e:
            return f"Erro na análise Git: {str(e)}"

    def _parse_git_log(self, log_output: str) -> list:
        """Parse da saída do git log."""
        commits = []
        current_commit = None
        
        for line in log_output.split('\n'):
            if '|' in line and len(line.split('|')) == 5:
                # Nova linha de commit
                if current_commit:
                    commits.append(current_commit)
                
                parts = line.split('|')
                current_commit = {
                    'hash': parts[0],
                    'author': parts[1],
                    'email': parts[2],
                    'date': parts[3],
                    'message': parts[4],
                    'files': []
                }
            elif line.strip() and current_commit and '\t' in line:
                # Linha de estatísticas de arquivo
                parts = line.split('\t')
                if len(parts) == 3:
                    additions = parts[0] if parts[0] != '-' else '0'
                    deletions = parts[1] if parts[1] != '-' else '0'
                    current_commit['files'].append({
                        'additions': additions,
                        'deletions': deletions,
                        'file': parts[2]
                    })
        
        if current_commit:
            commits.append(current_commit)
        
        return commits


class GitBlameAnalysisTool:
    """Ferramenta para analisar autoria de linhas de código usando git blame."""
    
    name: str = "Git Blame Analysis Tool"
    description: str = (
        "Ferramenta para analisar autoria de linhas de código usando git blame. "
        "Útil para entender quem modificou cada parte do código."
    )

    def run(self, repo_path: str, file_path: str) -> str:
        """
        Analisa a autoria de um arquivo específico usando git blame.
        
        Args:
            repo_path: Caminho para o repositório Git
            file_path: Caminho relativo do arquivo a ser analisado
        """
        try:
            full_path = os.path.join(repo_path, file_path)
            
            if not os.path.exists(full_path):
                return f"Erro: Arquivo {file_path} não encontrado."

            # Git blame com informações detalhadas
            blame_cmd = [
                'git', '-C', repo_path, 'blame',
                '--line-porcelain',
                file_path
            ]

            blame_output = subprocess.check_output(
                blame_cmd,
                stderr=subprocess.STDOUT,
                text=True
            )

            # Processa e agrupa por autor
            authors_stats = self._parse_git_blame(blame_output)
            
            result = []
            result.append("=" * 80)
            result.append(f"ANÁLISE DE AUTORIA: {file_path}")
            result.append("=" * 80)
            result.append("")
            
            for author, stats in sorted(authors_stats.items(), 
                                       key=lambda x: x[1]['lines'], 
                                       reverse=True):
                percentage = (stats['lines'] / stats['total_lines']) * 100
                result.append(f"Autor: {author}")
                result.append(f"Email: {stats['email']}")
                result.append(f"Linhas: {stats['lines']} ({percentage:.1f}%)")
                result.append(f"Último commit: {stats['last_commit'][:8]}")
                result.append("")

            return "\n".join(result)

        except subprocess.CalledProcessError as e:
            return f"Erro ao executar git blame: {e.output}"
        except Exception as e:
            return f"Erro na análise: {str(e)}"

    def _parse_git_blame(self, blame_output: str) -> dict:
        """Parse da saída do git blame."""
        authors = {}
        current_commit = None
        current_author = None
        current_email = None
        total_lines = 0
        
        for line in blame_output.split('\n'):
            if line.startswith('author '):
                current_author = line[7:]
            elif line.startswith('author-mail '):
                current_email = line[12:].strip('<>')
            elif line.startswith('summary '):
                if current_author:
                    if current_author not in authors:
                        authors[current_author] = {
                            'email': current_email,
                            'lines': 0,
                            'last_commit': current_commit,
                            'total_lines': 0
                        }
                    authors[current_author]['lines'] += 1
                    total_lines += 1
            elif len(line) == 40 and all(c in '0123456789abcdef' for c in line):
                current_commit = line
        
        # Atualiza total de linhas
        for author in authors:
            authors[author]['total_lines'] = total_lines
        
        return authors
