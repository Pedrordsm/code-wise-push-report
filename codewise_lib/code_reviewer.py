import os
import subprocess


def coletar_dados_git(repo_path: str, commits_limit: int = 3) -> str:
    """
    Coleta informações detalhadas do repositório Git para análise de código.
    
    Args:
        repo_path: Caminho para o repositório Git local
        commits_limit: Número máximo de commits a analisar (padrão: 3)
        
    Returns:
        str: Texto formatado com informações dos commits e diffs para análise
    """
    try:
        try:
            result = subprocess.run(
                ['git', '-C', repo_path, 'config', 'user.email'],
                capture_output=True,
                text=True,
                check=True
            )
            user_email = result.stdout.strip()
        except:
            user_email = "Desenvolvedor"
        
        #coleta de logs dos commits anteriores
        git_log_cmd = [
            'git', '-C', repo_path, 'log',
            f'-{commits_limit}',
            '--pretty=format:%H|%an|%ae|%ad|%s',
            '--date=iso',
            '--numstat',
            'HEAD'
        ]
        
        log_output = subprocess.check_output(
            git_log_cmd,
            stderr=subprocess.STDOUT,
            text=True
        )
        
        #formatação do resultado final
        resultado = []
        resultado.append("=" * 80)
        resultado.append(f"ANÁLISE DE CÓDIGO - {user_email}")
        resultado.append("=" * 80)
        resultado.append("")
        resultado.append(f"Últimos {commits_limit} commits:")
        resultado.append("")
        resultado.append(log_output)
        resultado.append("")
        
        #coleta de diffs dos commits anteriores
        for i in range(commits_limit):
            try:
                diff_cmd = ['git', '-C', repo_path, 'show', f'HEAD~{i}', '--unified=3']
                diff_output = subprocess.check_output(
                    diff_cmd,
                    stderr=subprocess.STDOUT,
                    text=True
                )
                resultado.append(f"--- Mudanças do commit HEAD~{i} ---")
                resultado.append(diff_output[:3000])  # Limita tamanho
                resultado.append("")
            except:
                pass
        
        return "\n".join(resultado)
        
    except subprocess.CalledProcessError as e:
        return f"Erro ao coletar dados Git: {e.output}"
    except Exception as e:
        return f"Erro: {str(e)}"
