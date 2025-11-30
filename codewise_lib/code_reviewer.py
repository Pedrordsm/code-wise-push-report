import os
import sys
import yaml
import tempfile
from datetime import datetime
from dotenv import load_dotenv
from crewai import Agent, Crew, Process, Task
from .select_llm import create_llm
from .tools.git_analysis_tool import GitAnalysisTool, GitBlameAnalysisTool


class CodeReviewerCrew:
    """Crew especializada em avaliar mudanças de código e gerar notas."""
    
    def __init__(self, repo_path: str, author_email: str = None, commits_limit: int = 5):
        load_dotenv()
        self.repo_path = repo_path
        self.author_email = author_email
        self.commits_limit = commits_limit
        
        provider = os.getenv("AI_PROVIDER").upper()
        model = os.getenv("AI_MODEL")
        self.llm = create_llm(provider, model)
        
        # Ferramentas Git
        self.git_tool = GitAnalysisTool()
        self.git_blame_tool = GitBlameAnalysisTool()
        
        # Carrega configurações
        base_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(base_dir, "config")
        agents_path = os.path.join(config_path, "agents.yaml")
        tasks_path = os.path.join(config_path, "tasks.yaml")
        
        with open(agents_path, "r", encoding="utf-8") as f:
            self.agents_config = yaml.safe_load(f)
        with open(tasks_path, "r", encoding="utf-8") as f:
            self.tasks_config = yaml.safe_load(f)
    
    def analyze_git_changes(self) -> str:
        """Coleta dados do Git para análise."""
        print(f"Analisando mudanças no repositório: {self.repo_path}")
        
        git_data = self.git_tool.run(
            repo_path=self.repo_path,
            author_email=self.author_email,
            commits_limit=self.commits_limit,
            branch="HEAD"
        )
        
        return git_data
    
    def create_reviewer_agent(self) -> Agent:
        """Cria o agente revisor de código."""
        return Agent(
            config=self.agents_config['code_reviewer'],
            llm=self.llm,
            verbose=True
        )
    
    def create_review_task(self, git_analysis_data: str) -> Task:
        """Cria a task de revisão de código."""
        cfg = self.tasks_config['code_review_scoring']
        
        # Substitui placeholders
        description = cfg['description'].format(
            git_analysis_data=git_analysis_data
        )
        
        # Determina o nome do arquivo de saída
        author_identifier = self.author_email.replace('@', '_').replace('.', '_') if self.author_email else "geral"
        expected_output = cfg['expected_output'].format(
            author_email=author_identifier
        )
        
        return Task(
            description=description,
            expected_output=expected_output,
            agent=self.create_reviewer_agent()
        )
    
    def run_review(self, output_dir: str = None) -> str:
        """Executa a revisão completa e gera o arquivo de avaliação."""
        print("Iniciando revisão de código...")
        
        #Coleta dados do Git
        git_data = self.analyze_git_changes()
        
        if "Erro" in git_data:
            print(f"{git_data}")
            return None
        
        #Salva dados em arquivo temporário para referência
        temp_file = tempfile.NamedTemporaryFile(
            mode='w', 
            delete=False, 
            suffix='.txt',
            encoding='utf-8'
        )
        temp_file.write(git_data)
        temp_file.close()
        
        print(f"Dados Git salvos em: {temp_file.name}")
        
        #Cria crew de revisão
        reviewer = self.create_reviewer_agent()
        review_task = self.create_review_task(git_data)
        
        crew = Crew(
            agents=[reviewer],
            tasks=[review_task],
            process=Process.sequential,
            verbose=True
        )
        
        # Executa a revisão
        print("Executando análise de código...")
        result = crew.kickoff()
        
        # Salva resultado
        if output_dir is None:
            output_dir = os.path.join(self.repo_path, 'code_reviews')
        
        os.makedirs(output_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        author_identifier = self.author_email.replace('@', '_').replace('.', '_') if self.author_email else "geral"
        output_file = os.path.join(
            output_dir, 
            f"avaliacao_codigo_{author_identifier}_{timestamp}.md"
        )
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# Avaliação de Código\n\n")
            f.write(f"**Data da Análise:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n\n")
            if self.author_email:
                f.write(f"**Desenvolvedor:** {self.author_email}\n\n")
            f.write("---\n\n")
            f.write(str(result))
        
        print(f"Avaliação concluída e salva em: {output_file}")
        
        # Limpa arquivo temporário
        try:
            os.unlink(temp_file.name)
        except:
            pass
        
        return output_file


def main():
    """Função principal para uso via CLI."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Code Reviewer - Avalia mudanças de código e gera notas"
    )
    parser.add_argument(
        "--repo",
        type=str,
        required=True,
        help="Caminho para o repositório Git"
    )
    parser.add_argument(
        "--author",
        type=str,
        help="Email do autor para filtrar commits (opcional)"
    )
    parser.add_argument(
        "--commits",
        type=int,
        default=5,
        help="Número de commits a analisar (padrão: 5)"
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Diretório de saída para o arquivo de avaliação (opcional)"
    )
    
    args = parser.parse_args()
    
    reviewer = CodeReviewerCrew(
        repo_path=args.repo,
        author_email=args.author,
        commits_limit=args.commits
    )
    
    output_file = reviewer.run_review(output_dir=args.output)
    
    if output_file:
        print(f"\nRevisão completa! Arquivo gerado: {output_file}")
    else:
        print("\nFalha na revisão de código.")
        sys.exit(1)


if __name__ == "__main__":
    main()
