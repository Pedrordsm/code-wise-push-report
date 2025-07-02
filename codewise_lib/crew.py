import sys
import os
import re
import yaml
from dotenv import load_dotenv
from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task

@CrewBase
class Codewise:
    """Classe principal da crew Codewise"""
    def __init__(self, commit_message: str = ""):
        load_dotenv()
        self.commit_message = commit_message
        if not os.getenv("GEMINI_API_KEY"):
            print("Erro: A variável de ambiente GEMINI_API_KEY não foi definida.")
            sys.exit(1)
        try:
            self.llm = LLM(
                model="gemini/gemini-2.0-flash",
                temperature=0.7
            )
        except Exception as e:
            print(f"Erro ao inicializar o LLM. Verifique sua chave de API e dependências. Erro: {e}")
            sys.exit(1)
        
        base_dir = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(base_dir, "config")
        agents_path = os.path.join(config_path, "agents.yaml")
        tasks_path = os.path.join(config_path, "tasks.yaml")

        try:
            with open(agents_path, "r", encoding="utf-8") as f:
                self.agents_config = yaml.safe_load(f)
            with open(tasks_path, "r", encoding="utf-8") as f:
                self.tasks_config = yaml.safe_load(f)
        except FileNotFoundError as e:
            print(f"Erro: Arquivo de configuração não encontrado: {e}")
            sys.exit(1)

    @agent
    def senior_architect(self) -> Agent: return Agent(config=self.agents_config['senior_architect'], llm=self.llm, verbose=False)
    @agent
    def senior_analytics(self) -> Agent: return Agent(config=self.agents_config['senior_analytics'], llm=self.llm, verbose=False)
    @agent
    def quality_consultant(self) -> Agent: return Agent(config=self.agents_config['quality_consultant'], llm=self.llm, verbose=False)
    @agent
    def quality_control_manager(self) -> Agent: return Agent(config=self.agents_config['quality_control_manager'], llm=self.llm, verbose=False)
    @agent
    def summary_specialist(self) -> Agent: return Agent(config=self.agents_config['summary_specialist'], llm=self.llm, verbose=False)
    
    @task
    def task_estrutura(self) -> Task:
        cfg = self.tasks_config['analise_estrutura']
        return Task(description=cfg['description'], expected_output=cfg['expected_output'], agent=self.senior_architect())
    @task
    def task_heuristicas(self) -> Task:
        cfg = self.tasks_config['analise_heuristicas']
        return Task(description=cfg['description'], expected_output=cfg['expected_output'], agent=self.senior_analytics())
    @task
    def task_solid(self) -> Task:
        cfg = self.tasks_config['analise_solid']
        return Task(description=cfg['description'], expected_output=cfg['expected_output'], agent=self.quality_consultant())
    @task
    def task_padroes(self) -> Task:
        cfg = self.tasks_config['padroes_projeto']
        return Task(description=cfg['description'], expected_output=cfg['expected_output'], agent=self.quality_control_manager())
    @task
    def task_summarize(self) -> Task:
        cfg = self.tasks_config['summarize_analysis']
        return Task(description=cfg['description'], expected_output=cfg['expected_output'], agent=self.summary_specialist())

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[self.senior_architect(), self.senior_analytics(), self.quality_consultant(), self.quality_control_manager()],
            tasks=[self.task_estrutura(), self.task_heuristicas(), self.task_solid(), self.task_padroes()],
            process=Process.sequential
        )

    def summary_crew(self) -> Crew:
        return Crew(
            agents=[self.summary_specialist()],
            tasks=[self.task_summarize()],
            process=Process.sequential
        )