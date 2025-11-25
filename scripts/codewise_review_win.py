import shutil
import subprocess
import os
import sys
import re
import json
import argparse
from datetime import datetime

# ===================================================================
# SEÇÃO DE FUNÇÕES AUXILIARES (COMPARTILHADAS)
# ===================================================================

def run_codewise_mode(mode, repo_path, branch_name):
    """Executa a IA como um MÓDULO e captura a saída, resolvendo o ImportError."""
    print(f"\n--- *! Executando IA [modo: {mode}] !* ---")
    
    command = [
        sys.executable, "-m", "codewise_lib.main",
        "--repo", repo_path,
        "--branch", branch_name,
        "--mode", mode
    ]
    try:
        env = os.environ.copy()
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env['PYTHONPATH'] = f"{project_root}{os.pathsep}{env.get('PYTHONPATH', '')}"
        
        # For interactive modes (lgpd_verify), don't capture output
        # This allows user input prompts to work
        if mode == 'lgpd_verify':
            result = subprocess.run(
                command,
                check=True,
                text=True,
                encoding='utf-8',
                errors='ignore',
                env=env
            )
            return ""  # No output to capture for lgpd_verify
        else:
            result = subprocess.run(
                command, 
                check=True, 
                capture_output=True, 
                text=True, 
                encoding='utf-8', 
                errors='ignore', 
                env=env
            )
            return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        error_output = e.stderr or ""
        if "429" in error_output and "RESOURCE_EXHAUSTED" in error_output:
            # Imprime a mensagem amigável e formatada
            print("""
    ================================================================
    ❌ ERRO: Limite de Uso da API Atingido (Erro 429)
    ================================================================
    
    A sua chave de API atingiu o limite máximo de requisições
    permitido pelo plano selecionado do modelo.
    
    Isso não é um bug no CodeWise, mas uma limitação da sua conta
    na plataforma do provedor.
        
    .  Aguarde: A cota do plano gratuito geralmente é renovada a
        cada 24 horas. Você pode tentar novamente amanhã.
  
            """, file=sys.stderr)
        else:
            # Para lgpd_verify, exit code 1 é esperado quando provider não é conforme
            # Não mostrar erro nesse caso
            if mode == 'lgpd_verify' and e.returncode == 1:
                # Silenciosamente retornar None - o erro já foi mostrado pelo controller
                return None
            else:
                print(f"❌ FALHA Inesperada no modo '{mode}': O subprocesso falhou com o código de saída {e.returncode}", file=sys.stderr)
                print("\n--- Saída de Erro (stderr) do Subprocesso ---", file=sys.stderr)
                print(e.stderr if e.stderr else "Nenhuma saída de erro foi capturada.")
                print("---------------------------------------------", file=sys.stderr)
        return None 

def obter_branch_padrao_remota(repo_path):
    try:
        remote_url_result = subprocess.check_output(["git", "config", "--get", "remote.origin.url"], cwd=repo_path, text=True, encoding='utf-8').strip()
        match = re.search(r'github\.com/([^/]+/[^/]+?)(\.git)?$', remote_url_result)
        if not match: return "main"
        repo_slug = match.group(1)
        result = subprocess.check_output(
            ["gh", "repo", "view", repo_slug, "--json", "defaultBranchRef", "-q", ".defaultBranchRef.name"],
            text=True, encoding='utf-8', stderr=subprocess.DEVNULL
        ).strip()
        if not result: return "main"
        print(f"✅ Branch principal detectada no GitHub: '{result}'", file=sys.stderr)
        return result
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "main"

def extrair_titulo_valido(texto):
    match = re.search(r"(feat|fix|refactor|docs):\s.+", texto, re.IGNORECASE)
    if match: return match.group(0).strip()
    return None

def obter_pr_aberto_para_branch(branch, repo_dir, repo_slug):
    try:
        comando_list = [
            "gh", "pr", "list",
            "--repo", repo_slug,  # Diz ao 'gh' em qual repositório procurar
            "--head", branch,
            "--state", "open",
            "--json", "number"
        ]
        
        result = subprocess.run(comando_list, check=True, capture_output=True, text=True, encoding='utf-8', cwd=repo_dir)
        
        pr_list = json.loads(result.stdout)
        return pr_list[0]['number'] if pr_list else None
    except (subprocess.CalledProcessError, json.JSONDecodeError):
        return None

def obter_repo_slug(remote_name, repo_path):
    """Obtém o slug 'usuario/repo' de um remote específico ('origin' ou 'upstream')."""
    try:
        remote_url = subprocess.check_output(
            ["git", "config", "--get", f"remote.{remote_name}.url"],
            cwd=repo_path, text=True, encoding='utf-8'
        ).strip()
        match = re.search(r'github\.com[/:]([^/]+/[^/]+?)(\.git)?$', remote_url)
        if match:
            return match.group(1)
        return None
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

def verificar_remote_existe(remote_name, repo_path):
    """Verifica se um remote com o nome especificado existe."""
    try:
        remotes = subprocess.check_output(["git", "remote"], cwd=repo_path, text=True, encoding='utf-8')
        return remote_name in remotes.split()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

# ===================================================================
# LÓGICA DO COMANDO 'codewise-lint' (PARA PRE-COMMIT)
# ===================================================================
def main_lint():
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    repo_path = os.getcwd()
    try:
        current_branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], encoding='utf-8', cwd=repo_path).strip()
    except Exception:
        current_branch = ""

    # Verificar LGPD e pedir autorização do usuário
    lgpd_dir = os.path.join(repo_path, "analises-julgamento-lgpd")
    judge_file = os.path.join(lgpd_dir, "julgamento_lgpd.md")
    policy_file = os.path.join(lgpd_dir, "analise_politica_coleta_de_dados.md")
    
    # Verificar se os arquivos LGPD existem
    if not os.path.exists(judge_file) or not os.path.exists(policy_file):
        # Primeira vez - criar arquivos de análise LGPD
        print("--- [PRIMEIRA EXECUÇÃO] Verificando conformidade LGPD... ---", file=sys.stderr)
        create_lgpd_analysis_files(repo_path, current_branch)
    
    # Sempre pedir autorização do usuário (primeira vez ou não)
    print("--- [Verificando autorização do usuário] ---", file=sys.stderr)
    if not ask_user_authorization(policy_file, judge_file):
        print("\n[ERROR] Usuário não autorizou o envio de dados.")
        sys.exit(1)
        
    print("--- 🔍 Executando análise rápida pré-commit do CodeWise ---", file=sys.stderr)
    sugestoes = run_codewise_mode("lint", repo_path, current_branch)

    if sugestoes is None:
        print("--- ❌ A análise rápida falhou. Verifique os erros acima. ---", file=sys.stderr)
        sys.exit(1)

    sugestoes_limpas = sugestoes.strip()

    if "AVISO:" in sugestoes_limpas or "FALHA:" in sugestoes_limpas:
        print("\n--- ⚠️  ATENÇÃO ---", file=sys.stderr)
        print(sugestoes_limpas, file=sys.stderr)
        print("-------------------", file=sys.stderr)
    elif "Nenhum problema aparente detectado" in sugestoes_limpas:
        print("--- ✅ Nenhuma sugestão crítica. Bom trabalho! ---", file=sys.stderr)
    elif sugestoes_limpas:
        # Verificar se a IA já incluiu um cabeçalho
        if sugestoes_limpas.lower().startswith("sugestões") or "💡" in sugestoes_limpas[:50]:
            # IA já incluiu cabeçalho, apenas mostrar
            print(f"\n{sugestoes_limpas}", file=sys.stderr)
        else:
            # Adicionar cabeçalho
            print("\n--- 💡 SUGESTÕES DE MELHORIA ---", file=sys.stderr)
            print(sugestoes_limpas, file=sys.stderr)
            print("---------------------------------", file=sys.stderr)
    else:
        print("--- ✅ Nenhuma sugestão crítica. Bom trabalho! ---", file=sys.stderr)

# ===================================================================
# LÓGICA DO COMANDO 'codewise-pr' (PARA PRE-PUSH)
# ===================================================================

def run_pr_logic(target_selecionado, pushed_branch):
    """Função principal que contém toda a lógica de criação de PR."""


    current_branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True).strip()

    if current_branch != pushed_branch:
        print(f" ⚠️ Hook de Push ignorado: Você está na branch '{current_branch}', mas o push é para a branch '{pushed_branch}'. Push será feito sem o Hook.", file=sys.stderr)
        sys.exit(0)  # Sai do script com sucesso, sem fazer nada.

    if not shutil.which("gh"):
        print("❌ Erro: GitHub CLI ('gh') não foi encontrado no seu sistema.", file=sys.stderr)
        print("   Por favor, instale-a a partir de: https://cli.github.com/", file=sys.stderr)
        sys.exit(1)

    os.environ['PYTHONIOENCODING'] = 'utf-8'
    repo_path = os.getcwd()

    upstream_existe = verificar_remote_existe('upstream', repo_path)
    upstream_renomeado = False

    # Verificar LGPD e pedir autorização do usuário
    lgpd_dir = os.path.join(repo_path, "analises-julgamento-lgpd")
    judge_file = os.path.join(lgpd_dir, "julgamento_lgpd.md")
    policy_file = os.path.join(lgpd_dir, "analise_politica_coleta_de_dados.md")
    
    # Verificar se os arquivos LGPD existem
    if not os.path.exists(judge_file) or not os.path.exists(policy_file):
        # Primeira vez - criar arquivos de análise LGPD
        print("--- [PRIMEIRA EXECUÇÃO] Verificando conformidade LGPD... ---", file=sys.stderr)
        create_lgpd_analysis_files(repo_path, current_branch)
    
    # Sempre pedir autorização do usuário (primeira vez ou não)
    print("--- [Verificando autorização do usuário] ---", file=sys.stderr)
    if not ask_user_authorization(policy_file, judge_file):
        print("\n[ERROR] Usuário não autorizou o envio de dados.")
        sys.exit(1)

    try:
        if target_selecionado == 'origin' and upstream_existe:
            print("Renomeando 'upstream' temporariamente para evitar bug do gh...", file=sys.stderr)
            subprocess.run(["git", "remote", "rename", "upstream", "upstream_temp"], cwd=repo_path, check=True, capture_output=True)
            upstream_renomeado = True

        print(f"📍 Analisando o repositório em: {repo_path}", file=sys.stderr)
        print(f"🎯 Alvo do Pull Request definido para: '{target_selecionado}'", file=sys.stderr)

        if target_selecionado == 'upstream' and not upstream_existe:
            sys.exit("❌ Erro: O alvo é 'upstream', mas o remote 'upstream' não está configurado.")

        try:
            current_branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], encoding='utf-8', cwd=repo_path).strip()
        except Exception as e:
            sys.exit(f"❌ Erro ao detectar a branch Git: {e}")

        base_branch_target = obter_branch_padrao_remota(repo_path)
        if current_branch == base_branch_target:
            sys.exit(f"❌ A automação não pode ser executada na branch principal ('{base_branch_target}').")

        origin_slug = obter_repo_slug('origin', repo_path)
        if not origin_slug:
            sys.exit("❌ Falha crítica: Não foi possível determinar o repositório 'origin'.")

        head_branch_completa = f"{origin_slug.split('/')[0]}:{current_branch}"
        repo_alvo_pr = obter_repo_slug(target_selecionado, repo_path)

        print("\n--- 🤖 Executando IA para documentação do PR ---", file=sys.stderr)

        titulo_bruto = run_codewise_mode("titulo", repo_path, current_branch)
        titulo_final = ""  # Inicializa a variável
        if titulo_bruto:
            titulo_final = extrair_titulo_valido(titulo_bruto) or f"feat: Modificações da branch {current_branch}"
            print(f" ✅ Título gerado: {titulo_final}", file=sys.stderr)

        descricao = run_codewise_mode("descricao", repo_path, current_branch)
        if descricao:
            print("\n ✅ Descrição gerada:", file=sys.stderr)
            print("-" * 40, file=sys.stderr)
            print(descricao, file=sys.stderr)
            print("-" * 40, file=sys.stderr)

        analise_tecnica = run_codewise_mode("analise", repo_path, current_branch)

        if not all([titulo_final, descricao, analise_tecnica]):
            sys.exit("❌ Falha ao gerar um ou mais textos necessários da IA.")

        temp_analise_path = os.path.join(repo_path, ".codewise_analise_temp.txt")
        with open(temp_analise_path, "w", encoding='utf-8') as f:
            f.write(analise_tecnica)

        pr_numero = obter_pr_aberto_para_branch(current_branch, repo_path, repo_alvo_pr)

        if pr_numero:
            print(f"⚠️ PR #{pr_numero} já existente. Acrescentando nova análise...", file=sys.stderr)
            try:
                descricao_antiga_raw = subprocess.check_output(
                    ["gh", "pr", "view", str(pr_numero), "--json", "body", "--repo", repo_alvo_pr],
                    cwd=repo_path, text=True, encoding='utf-8'
                )
                descricao_antiga = json.loads(descricao_antiga_raw).get("body", "")
                timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                nova_entrada_descricao = (
                    f"\n\n---\n\n"
                    f"**🔄 Atualização em {timestamp}**\n\n"
                    f"{descricao}"
                )
                body_final = descricao_antiga + nova_entrada_descricao
                subprocess.run(["gh", "pr", "edit", str(pr_numero), "--title", titulo_final, "--body", body_final, "--repo", repo_alvo_pr], check=False, cwd=repo_path)
                print(f"✅ Descrição do PR #{pr_numero} atualizada com novas informações.")
            except Exception as e:
                print(f"⚠️ Não foi possível buscar a descrição antiga. Substituindo pela nova. Erro: {e}", file=sys.stderr)
                subprocess.run(["gh", "pr", "edit", str(pr_numero), "--title", titulo_final, "--body", descricao, "--repo", repo_alvo_pr], check=False, cwd=repo_path)


        else:
            print("🆕 Nenhum PR aberto. Criando Pull Request...", file=sys.stderr)
            try:
                comando_pr = [
                    "gh", "pr", "create", "--repo", repo_alvo_pr,
                    "--base", base_branch_target, "--head", head_branch_completa,
                    "--title", titulo_final, "--body", descricao
                ]
                result = subprocess.run(comando_pr, check=True, capture_output=True, text=True, encoding='utf-8', cwd=repo_path)
                pr_url = result.stdout.strip()
                match = re.search(r"/pull/(\d+)", pr_url)
                if match:
                    pr_numero = match.group(1)
                else:
                    raise Exception(f"Não foi possível extrair o número do PR da URL: {pr_url}")
                print(f"✅ PR #{pr_numero} criado: {pr_url}", file=sys.stderr)
            except Exception as e:

                print("\n⚠️ AVISO: Não foi possível criar o Pull Request automaticamente.", file=sys.stderr)
                print("   Isso é normal no primeiro push para uma nova branch.", file=sys.stderr)
                print("   O seu git push continuará normalmente.", file=sys.stderr)
                print("   Após o push, rode 'codewise-pr' manualmente para criar o PR para o 'upstream'.", file=sys.stderr)
                if os.path.exists(temp_analise_path):
                    os.remove(temp_analise_path)
                sys.exit(0)

        if pr_numero:
            print(f"💬 Comentando análise técnica no PR #{pr_numero}...", file=sys.stderr)
            try:
                subprocess.run(["gh", "pr", "comment", str(pr_numero), "--body-file", temp_analise_path, "--repo", repo_alvo_pr], check=True, capture_output=True, text=True, encoding='utf-8', cwd=repo_path)
                print("✅ Comentário postado com sucesso.", file=sys.stderr)
            except subprocess.CalledProcessError as e:
                print(f"❌ Falha ao comentar no PR: {e.stderr}", file=sys.stderr)
            finally:
                if os.path.exists(temp_analise_path):
                    print("🧹 Limpando arquivo temporário...", file=sys.stderr)
                    os.remove(temp_analise_path)
    finally:
        if upstream_renomeado:
            print(" Restaurando nome do remote 'upstream'...", file=sys.stderr)
            subprocess.run(["git", "remote", "rename", "upstream_temp", "upstream"], cwd=repo_path, check=True, capture_output=True)


def main_pr_origin():
    """Ponto de entrada para criar um PR no 'origin'."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--pushed-branch", required=False, type=str, help="A branch que está sendo enviada.")
    args = parser.parse_args()

    if args.pushed_branch:
        pushed_branch = args.pushed_branch
    else:
        # Uso manual: detecta branch atual
        try:
            pushed_branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], encoding='utf-8').strip()
        except Exception as e:
            sys.exit(f"❌ Erro ao detectar a branch atual: {e}")

    run_pr_logic(target_selecionado="origin", pushed_branch=pushed_branch)


def main_pr_upstream():
    """Ponto de entrada para criar um PR no 'upstream'."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--pushed-branch", required=False, type=str, help="A branch que está sendo enviada.")
    args = parser.parse_args()

    if args.pushed_branch:
        pushed_branch = args.pushed_branch
    else:
        # Uso manual: detecta branch atual
        try:
            pushed_branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], encoding='utf-8').strip()
        except Exception as e:
            sys.exit(f"❌ Erro ao detectar a branch atual: {e}")

    run_pr_logic(target_selecionado="upstream", pushed_branch=pushed_branch)



def main_pr_interactive():
    """Função interativa para ser chamada manualmente pelo comando 'codewise-pr'."""
    repo_path = os.getcwd()

    try:
        remotes_output = subprocess.check_output(["git", "remote"], cwd=repo_path, text=True, encoding='utf-8')
        remotes = remotes_output.strip().splitlines()
    except subprocess.CalledProcessError:
        sys.exit("❌ Erro: Não foi possível listar os remotes do Git.")

    if not remotes:
        sys.exit("❌ Nenhum remote foi encontrado no repositório.")

    print("\n📍Remotes detectados:")
    for i, remote in enumerate(remotes, start=1):
        print(f"  {i}: {remote}")

    while True:
        try:
            escolha = input(f"Escolha o número do remote para o Pull Request [1-{len(remotes)}]: ").strip()
            if escolha.isdigit() and 1 <= int(escolha) <= len(remotes):
                target_selecionado = remotes[int(escolha) - 1]
                break
            else:
                print("❌ Escolha inválida. Digite um número válido.")
        except (KeyboardInterrupt, EOFError):
            print("\nOperação cancelada pelo usuário.")
            sys.exit(1)

    try:
        current_branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], encoding='utf-8', cwd=repo_path).strip()
    except Exception as e:
        sys.exit(f"❌ Erro ao detectar a branch Git atual: {e}")

    run_pr_logic(target_selecionado=target_selecionado, pushed_branch=current_branch)


def ask_user_authorization(policy_file: str, judge_file: str) -> bool:
    """
    Mostra o resumo da política LGPD e pede autorização do usuário.
    
    Args:
        policy_file: Caminho para o arquivo de análise de política
        judge_file: Caminho para o arquivo de julgamento LGPD
        
    Returns:
        True se o usuário autorizar (S), False caso contrário (N)
    """
    try:
        # Ler o arquivo de política
        with open(policy_file, "r", encoding="utf-8") as f:
            content = f.read()
        
        print("-" * 40)
        print()
        print("Resumo sobre a análise da política de uso de dados:")
        print()
        
        # Extrair a conclusão
        conclusao_match = re.search(r"(?i)^#+\s*Conclusão\s*\n+(.*)", content, re.MULTILINE | re.DOTALL)
        
        if conclusao_match:
            conclusao_content = conclusao_match.group(1).strip()
            print(conclusao_content)
        else:
            print("Conclusão não encontrada no arquivo de análise.")
        
        print()
        
        # Pedir autorização
        while True:
            print("-" * 40)
            print("\n⚠️ AVISO: Esta ação requer o envio de dados, como por exemplo,")
            print("o código-fonte, para o provedor da API key fornecida.", file=sys.stderr)
            print()
            
            # Ler input diretamente do terminal (funciona em hooks Git)
            try:
                # No Windows, usar 'CON' para ler do console
                if sys.platform == 'win32':
                    with open('CON', 'r') as tty:
                        sys.stdout.write("* Com base na verificação apresentada acima, você gostaria de continuar com o envio de seus dados para o provedor e modelo de api key escolhido? [S/N]: ")
                        sys.stdout.flush()
                        choice = tty.readline().strip().upper()
                else:
                    # No Linux/Mac, usar '/dev/tty'
                    with open('/dev/tty', 'r') as tty:
                        sys.stdout.write("* Com base na verificação apresentada acima, você gostaria de continuar com o envio de seus dados para o provedor e modelo de api key escolhido? [S/N]: ")
                        sys.stdout.flush()
                        choice = tty.readline().strip().upper()
            except Exception as e:
                # Fallback para input() normal
                try:
                    choice = input("* Com base na verificação apresentada acima, você gostaria de continuar com o envio de seus dados para o provedor e modelo de api key escolhido? [S/N]: ").strip().upper()
                except (EOFError, OSError):
                    print(f"\nErro ao ler entrada do usuário: {e}", file=sys.stderr)
                    return False
            
            print()
            
            if choice == "S":
                print("-" * 40)
                print("\nVocê ✅ AUTORIZOU ✅ o envio de dados necessários para o")
                print("provedor da API key escolhida!", file=sys.stderr)
                print("\nContinuando as análises...")
                print()
                print("-" * 40)
                print()
                return True
            elif choice == "N":
                print("-" * 40)
                print("\nVocê ❌ NÃO AUTORIZOU ❌ o envio de dados necessários")
                print("para o provedor da API key escolhida.", file=sys.stderr)
                print("\nExecute novamente com outro modelo ou provedor.")
                print()
                print("Dados ❌ NÃO ENVIADOS! ❌ Interrompendo programa...", file=sys.stderr)
                print()
                print("-" * 40)
                return False
            else:
                print("Por favor, digite S para Sim ou N para Não.")
                
    except Exception as e:
        print(f"Erro ao ler arquivos LGPD: {e}", file=sys.stderr)
        return False


def create_lgpd_analysis_files(repo_path:str, branch_atual:str):
    """
    Cria os arquivos de análise LGPD pela primeira vez.
    Executa a verificação LGPD através do controller MVC, mas SEM pedir autorização.
    A autorização será pedida depois pelo main_lint.
    """
    caminho_dir_lgpd = os.path.join(repo_path, "analises-julgamento-lgpd")
    policy_file_path = os.path.join(caminho_dir_lgpd, "analise_politica_coleta_de_dados.md")
    lgpd_judge_file_path = os.path.join(caminho_dir_lgpd, "julgamento_lgpd.md")

    # Executar verificação LGPD para criar os arquivos
    # O controller vai pedir autorização, mas vamos ignorar isso por enquanto
    try:
        run_codewise_mode("lgpd_verify", repo_path, branch_atual)
        return True
    except subprocess.CalledProcessError as e:
        # Se falhou, pode ser que o provider não seja conforme
        # Verificar se os arquivos foram criados mesmo assim
        if os.path.exists(policy_file_path) and os.path.exists(lgpd_judge_file_path):
            return True
        else:
            print("\n[ERROR] LGPD verification failed.")
            print("Please check your provider configuration.")
            sys.exit(1)
    except Exception as e:
        print(f"Erro ao criar arquivos LGPD: {e}", file=sys.stderr)
        sys.exit(1)
