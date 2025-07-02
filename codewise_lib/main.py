import argparse
# CORREÇÃO: Adicionado o '.' para indicar uma importação relativa dentro do pacote.
from .cw_runner import CodewiseRunner

def main():
    parser = argparse.ArgumentParser(description="Code Wise - Ferramenta de Análise de Código com IA.")
    parser.add_argument("--repo", type=str, required=True, help="Caminho para o repositório Git.")
    parser.add_argument("--branch", type=str, required=True, help="Nome da branch a ser analisada.")
    parser.add_argument(
        "--mode",
        type=str,
        required=True,
        choices=['descricao', 'analise', 'titulo', 'lint'],
        help="Modo de operação."
    )
    args = parser.parse_args()
    
    runner = CodewiseRunner()
    runner.executar(
        caminho_repo=args.repo,
        nome_branch=args.branch,
        modo=args.mode
    )

if __name__ == "__main__":
    main()