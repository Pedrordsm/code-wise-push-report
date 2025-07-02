import subprocess
import os
import sys

def run_git_command(command, repo_path):
    """Função auxiliar para executar comandos Git e capturar a saída."""
    try:
        # Usamos repo_path como o diretório de trabalho para o comando
        result = subprocess.check_output(command, cwd=repo_path, text=True, encoding='utf-8', stderr=subprocess.PIPE)
        return result.strip()
    except subprocess.CalledProcessError as e:
        # Se o comando falhar, mas o erro não for fatal, imprime no stderr e continua
        if e.stderr:
            print(f"Aviso do Git: {e.stderr.strip()}", file=sys.stderr)
        return "" # Retorna vazio para erros não fatais (ex: branch não encontrada no remote)
    except FileNotFoundError:
        print("ERRO: O executável 'git' não foi encontrado. Verifique se o Git está instalado e no PATH.", file=sys.stderr)
        return None # Retorna None para erros fatais

def gerar_entrada_automatica(caminho_repo, caminho_saida, nome_branch):
    try:
        # 1. Busca atualizações do repositório remoto
        print("🔄 Buscando atualizações do repositório remoto...", file=sys.stderr)
        run_git_command(["git", "fetch", "origin", "--prune"], caminho_repo)

        # 2. Define a branch base para comparação
        branch_remota_str = f'origin/{nome_branch}'
        # Verifica se a branch existe no remote
        remote_branch_exists = run_git_command(["git", "show-ref", "--verify", f"refs/remotes/{branch_remota_str}"], caminho_repo)
        
        default_branch_name = "main" # Assume 'main' como padrão
        base_ref_str = f'origin/{default_branch_name}'

        if remote_branch_exists:
            # Se a branch já existe, a base é ela mesma no remote
            base_ref_str = branch_remota_str
            print(f"✅ Branch '{nome_branch}' já existe no remote. Analisando novos commits desde o último push.", file=sys.stderr)
        else:
            print(f"✅ Branch '{nome_branch}' é nova. Comparando com a branch principal remota ('{default_branch_name}').", file=sys.stderr)

        # 3. Pega a lista de mensagens de commit
        range_commits = f"{base_ref_str}..{nome_branch}"
        log_commits = run_git_command(["git", "log", "--pretty=format:- %s", range_commits], caminho_repo)
        
        if not log_commits:
            print("Nenhum commit novo para analisar foi encontrado.", file=sys.stderr)
            return False
            
        commits_pendentes = log_commits.splitlines()

        # 4. Gera o diff incremental
        diff_completo = run_git_command(["git", "diff", f"{base_ref_str}..{nome_branch}"], caminho_repo)
        
        # 5. Monta o texto final
        entrada = [f"Analisando {len(commits_pendentes)} novo(s) commit(s).\n\nMensagens de commit:\n"]
        entrada.extend(commits_pendentes)
        entrada.append(f"\n{'='*80}\nDiferenças de código consolidadas a serem analisadas:\n{diff_completo}")

        with open(caminho_saida, "w", encoding="utf-8") as arquivo_saida:
            arquivo_saida.write("\n".join(entrada))
        return True
    except Exception as e:
        print(f"Ocorreu um erro inesperado em 'entradagit.py': {e}", file=sys.stderr)
        return False

def obter_mudancas_staged(repo_path="."):
    """Verifica o estado do repositório para o modo lint usando subprocess."""
    try:
        # 1. Verifica a 'staging area'
        diff_staged = run_git_command(["git", "diff", "--cached"], repo_path)
        if diff_staged:
            return diff_staged

        # 2. Se o stage está limpo, verifica o 'working directory'
        diff_working_dir = run_git_command(["git", "diff"], repo_path)
        if diff_working_dir:
            return "AVISO: Nenhuma mudança na 'staging area', mas existem modificações não adicionadas.\nUse 'git add <arquivo>' para prepará-las para a análise."

        # 3. Se ambos estiverem limpos, retorna None
        return None
    except Exception as e:
        print(f"Erro em 'entradagit.py' ao obter staged changes: {e}", file=sys.stderr)
        return "FALHA: Erro ao interagir com o repositório Git."