import sys
import os
import re
import yaml
from dotenv import load_dotenv
from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from .select_llm import create_llm

@CrewBase
class Codewise:
    """Classe principal da crew Codewise"""
    def __init__(self, commit_message: str = ""):
        load_dotenv()
        self.commit_message = commit_message
        # self para utilizar na task de analise da politica
        self.provider = os.getenv("AI_PROVIDER").upper()
        self.model = os.getenv("AI_MODEL")
        ##
        self.llm = create_llm(provider,model)
        
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
    @agent
    def code_mentor(self) -> Agent: return Agent(config=self.agents_config['code_mentor'], llm=self.llm, verbose=False)

    @agent
    def dataCollect_policy_analytics(self) -> Agent: return Agent(config=self.agents_config['dataCollect_policy_analytics'], llm=self.llm, verbose=False)

    @agent
    def lgpd_judge(self) -> Agent: return Agent(config=self.agents_config['lgpd_judge'], llm=self.llm, verbose = False)
    
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
    
    @task
    def task_mentoring(self) -> Task:
        cfg = self.tasks_config['mentoring_task']
        return Task(description=cfg['description'], expected_output=cfg['expected_output'], agent=self.code_mentor())
    
    @task
    def task_policy(self) -> Task:
        cfg = self.tasks_config['policy_analytics']

        formatted_description = cfg['description'].format(
            IA_PROVIDER=self.provider,
            IA_MODEL=self.model
        )

        return Task(description=formatted_description, expected_output=cfg['expected_output'], agent=self.dataCollect_policy_analytics())

    @task
    def task_judging(self) -> Task:
        cfg = self.tasks_config['lgpd_judging']
        return Task(description=cfg['description'], expected_output=cfg['expected_output'], agent=self.task_policy_analytics())


    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=[self.senior_architect(), self.senior_analytics(), self.quality_consultant(), self.quality_control_manager(),self.code_mentor()],
            tasks=[self.task_estrutura(), self.task_heuristicas(), self.task_solid(), self.task_padroes(),self.task_mentoring()],
            process=Process.sequential
        )

    @crew
    def summary_crew(self) -> Crew:
        return Crew(
            agents=[self.summary_specialist()],
            tasks=[self.task_summarize()],
            process=Process.sequential
        )
        
    @crew
    def lgpd_crew(self) -> Crew:
        return Crew(
            agents=[self.dataCollect_policy_analytics(), self.lgpd_judge()],
            tasks=[self.task_policy(), self.task_judging()],
            process=Process.sequential
        )