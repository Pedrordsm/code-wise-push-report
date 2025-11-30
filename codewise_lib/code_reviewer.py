import os
import subprocess


def coletar_dados_git(repo_path: str, commits_limit: int = 3) -> str:
    try:
        # Obtém email do usuário
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
        
        # Coleta informações dos últimos commits
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
        
        # Monta o contexto para análise
        resultado = []
        resultado.append("=" * 80)
        resultado.append(f"ANÁLISE DE CÓDIGO - {user_email}")
        resultado.append("=" * 80)
        resultado.append("")
        resultado.append(f"Últimos {commits_limit} commits:")
        resultado.append("")
        resultado.append(log_output)
        resultado.append("")
        
        # Pega diff dos últimos commits
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
