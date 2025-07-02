import os
import sys
import stat
import argparse
import subprocess

PRE_PUSH_CONTENT = """#!/bin/sh
set -e
echo "--- [HOOK PRE-PUSH CodeWise ATIVADO] ---"
codewise-pr
echo "--- [HOOK PRE-PUSH CodeWise CONCLUÍDO] ---"
exit 0
"""

PRE_COMMIT_CONTENT = """#!/bin/sh
set -e
echo "--- [HOOK PRE-COMMIT CodeWise ATIVADO] ---"
codewise-lint
echo "--- [HOOK PRE-COMMIT CodeWise CONCLUÍDO] ---"
exit 0
"""

def verificar_remote_existe(remote_name):
    try:
        repo_path = os.getcwd() 
        remotes = subprocess.check_output(["git", "remote"], cwd=repo_path, text=True, encoding='utf-8')
        return remote_name in remotes.split()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def install_hook(hook_name, hook_content, repo_root):
    hooks_dir = os.path.join(repo_root, '.git', 'hooks')
    if not os.path.isdir(hooks_dir):
        print(f"❌ Erro: Diretório de hooks do Git não encontrado em '{hooks_dir}'.", file=sys.stderr)
        return False

    hook_path = os.path.join(hooks_dir, hook_name)
    try:
        with open(hook_path, 'w', newline='\n') as f:
            f.write(hook_content)
        st = os.stat(hook_path)
        os.chmod(hook_path, st.st_mode | stat.S_IEXEC)
        print(f"✅ Hook '{hook_name}' instalado com sucesso.")
        return True
    except Exception as e:
        print(f"❌ Erro ao instalar o hook '{hook_name}': {e}", file=sys.stderr)
        return False

def main():
    parser = argparse.ArgumentParser(description="Instalador de hooks do CodeWise.")
    parser.add_argument('--commit', action='store_true', help='Instala o hook pre-commit.')
    parser.add_argument('--push', action='store_true', help='Instala o hook pre-push.')
    parser.add_argument('--all', action='store_true', help='Instala ambos os hooks.')
    args = parser.parse_args()

    print("🚀 Iniciando configuração de hooks do CodeWise...")
    repo_root = os.getcwd()

    if not any([args.commit, args.push, args.all]):
        print("Nenhum hook especificado. Use --commit, --push, ou --all.", file=sys.stderr)
        sys.exit(1)

    if args.commit or args.all:
        install_hook('pre-commit', PRE_COMMIT_CONTENT, repo_root)

    if args.push or args.all:
        try:
            remotes_raw = subprocess.check_output(["git", "remote"], cwd=repo_root, text=True, encoding='utf-8')
            remotes = [r.strip() for r in remotes_raw.splitlines() if r.strip()]
        except subprocess.CalledProcessError:
            sys.exit("❌ Erro: Não foi possível listar os remotes do Git.")

        if not remotes:
            sys.exit("❌ Nenhum remote foi encontrado no repositório.")

        print("\n🎯 Remotes disponíveis para criação automática de Pull Request:")
        for i, remote in enumerate(remotes, 1):
            print(f"   {i}: {remote}")

        while True:
            try:
                escolha = input(f"Escolha o remote padrão para o pre-push hook [1-{len(remotes)}]: ").strip()
                if escolha.isdigit() and 1 <= int(escolha) <= len(remotes):
                    remote_escolhido = remotes[int(escolha) - 1]
                    if remote_escolhido == "origin":
                        push_command = "codewise-pr-origin"
                    elif remote_escolhido == "upstream":
                        push_command = "codewise-pr-upstream"
                    else:
                        push_command = f"codewise-pr --target {remote_escolhido}"
                    break
                else:
                    print("Opção inválida. Digite um número válido.")
            except (KeyboardInterrupt, EOFError):
                print("\nInstalação do hook pre-push cancelada.")
                sys.exit(1)

        pre_push_content_dinamico = f"""#!/bin/sh
set -e

while read local_ref local_sha remote_ref remote_sha
do
    pushed_branch=$(basename "$local_ref")
    echo "--- [HOOK PRE-PUSH CodeWise ATIVADO (Alvo: {remote_escolhido})] ---"
    {push_command} --pushed-branch "$pushed_branch"
    echo "--- [HOOK PRE-PUSH CodeWise CONCLUÍDO] ---"
done

exit 0
"""
        install_hook('pre-push', pre_push_content_dinamico, repo_root)

    print("\n🎉 Configuração concluída!")
