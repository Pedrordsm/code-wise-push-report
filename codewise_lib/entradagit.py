import subprocess
import os
import sys

def run_git_command(command, repo_path):
    """
    Função auxiliar para executar comandos Git e capturar a saída.
    
    Args:
        command: Lista com o comando Git e seus argumentos
        repo_path: Caminho do repositório onde executar o comando
        
    Returns:
        str ou None: Saída do comando se tiver ok, string vazia para erros não fatais, None para erros fatais
    """
    try:
        #se não houver erro, retorna a saída do comando normal
        result = subprocess.check_output(command, cwd=repo_path, text=True, encoding='utf-8', stderr=subprocess.PIPE)
        return result.strip()
    except subprocess.CalledProcessError as e:
        #se for um erro não fatal, como branch inexistente, retorna string vazia para tratar depois e não quebrar o fluxo
        if e.stderr:
            print(f"Aviso do Git: {e.stderr.strip()}", file=sys.stderr)
        return ""
    except FileNotFoundError:
        #erros fatais, como o git não estar instalado ou coisas do tipo
        print("ERRO: O executável 'git' não foi encontrado. Verifique se o Git está instalado e no PATH.", file=sys.stderr)
        return None

def gerar_entrada_automatica(caminho_repo, caminho_saida, nome_branch):
    """
    Gera automaticamente o arquivo de entrada com commits e diffs para análise.
    
    Args:
        caminho_repo: Caminho para o repositório Git
        caminho_saida: Caminho onde salvar o arquivo de entrada gerado
        nome_branch: Nome da branch a ser analisada
        
    Returns:
        bool: True se gerado com sucesso, False caso contrário
    """
    try:
        #busca alguma alteração que tiver na branch remota
        print("🔄 Buscando atualizações do repositório remoto...", file=sys.stderr)
        run_git_command(["git", "fetch", "origin", "--prune"], caminho_repo)

        #define a branch remota a ser comparada já verificando se existe
        branch_remota_str = f'origin/{nome_branch}'
        remote_branch_exists = run_git_command(["git", "show-ref", "--verify", f"refs/remotes/{branch_remota_str}"], caminho_repo)
        
        default_branch_name = "main"
        base_ref_str = f'origin/{default_branch_name}'

        if remote_branch_exists:
            base_ref_str = branch_remota_str
            print(f"✅ Branch '{nome_branch}' já existe no remote. Analisando novos commits desde o último push.", file=sys.stderr)
        else:
            print(f"✅ Branch '{nome_branch}' é nova. Comparando com a branch principal remota ('{default_branch_name}').", file=sys.stderr)

        #pega a lista de commits
        range_commits = f"{base_ref_str}..{nome_branch}"
        log_commits = run_git_command(["git", "log", "--pretty=format:- %s", range_commits], caminho_repo)
        
        if not log_commits:
            print("Nenhum commit novo para analisar foi encontrado.", file=sys.stderr)
            return False
            
        commits_pendentes = log_commits.splitlines()

        #pega o diff completo dos commits 
        diff_completo = run_git_command(["git", "diff", f"{base_ref_str}..{nome_branch}"], caminho_repo)
        
        #monta o texto final para o arquivo de entrada
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
    """
    Verifica o estado do repositório para o modo lint.
    
    Args:
        repo_path: Caminho para o repositório Git (padrão: diretório atual)
        
    Returns:
        str ou None: Diff das mudanças staged, mensagem de aviso, ou None se não houver mudanças
    """
    try:
        #verifica a área de stage
        diff_staged = run_git_command(["git", "diff", "--cached"], repo_path)
        if diff_staged:
            return diff_staged

        #se não tiver nada na staging area, verifica se tem mudanças no working dir
        diff_working_dir = run_git_command(["git", "diff"], repo_path)
        if diff_working_dir:
            return "AVISO: Nenhuma mudança na 'staging area', mas existem modificações não adicionadas.\nUse 'git add <arquivo>' para prepará-las para a análise."

        #se ambos estiverem limpos, retorna None
        return None
    except Exception as e:
        print(f"Erro em 'entradagit.py' ao obter staged changes: {e}", file=sys.stderr)
        return "FALHA: Erro ao interagir com o repositório Git."