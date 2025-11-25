"""Crew orchestration service for CodeWise.

This module manages AI agent crews and task execution, loading configurations
from YAML files and orchestrating multi-agent workflows for code analysis.
"""

import os
import sys
import yaml
from typing import Dict, Any
from dotenv import load_dotenv
from crewai import Agent, Crew, Process, Task

# Try to import WebsiteSearchTool, but make it optional
try:
    from crewai_tools import WebsiteSearchTool
    HAS_WEBSITE_SEARCH = True
except ImportError:
    HAS_WEBSITE_SEARCH = False
    WebsiteSearchTool = None

from .llm_factory import LLMFactory
from .exceptions import ConfigurationError
from ..tools.custom_git_tools import OwnershipTool, UserCommitsTool, CommitDiffTool
from ..tools.score_tool import ScoreFormalizerTool
from ..tools.current_user_tool import CurrentUserTool


class CrewOrchestrator:
    """Orchestrator for managing AI agent crews and tasks.
    
    This class handles loading agent and task configurations from YAML files,
    creating configured agents, and executing crew workflows for various
    analysis modes (code analysis, summary generation, LGPD verification).
    """
    
    def __init__(self, llm_factory: LLMFactory, commit_message: str = ""):
        """Initialize CrewOrchestrator with LLM factory and optional commit message.
        
        Args:
            llm_factory: Factory for creating LLM instances.
            commit_message: Optional commit message for context.
            
        Raises:
            ConfigurationError: If configuration files cannot be loaded.
        """
        load_dotenv()
        
        self.llm_factory = llm_factory
        self.commit_message = commit_message
        
        # Get Git user name
        self.git_user_name = self._get_git_user_name()
        
        # Load provider configuration
        self.provider = os.getenv("AI_PROVIDER", "").upper()
        self.model = os.getenv("AI_MODEL", "")
        
        if not self.provider or not self.model:
            raise ConfigurationError(
                "AI_PROVIDER/AI_MODEL",
                "Environment variables AI_PROVIDER and AI_MODEL must be set"
            )
        
        # Create LLM instance
        self.llm = self.llm_factory.create_llm(self.provider, self.model)
        
        # Initialize tools
        if HAS_WEBSITE_SEARCH:
            self.web_search_tool = WebsiteSearchTool()
        else:
            self.web_search_tool = None
        
        # Load configuration files
        self._load_configurations()
    
    def _get_git_user_name(self) -> str:
        """Get the current Git user name.
        
        Returns:
            Git user name or 'Unknown Developer' if not found.
        """
        import subprocess
        try:
            result = subprocess.run(
                ['git', 'config', 'user.name'],
                capture_output=True,
                text=True,
                check=True
            )
            user_name = result.stdout.strip()
            return user_name if user_name else "Unknown Developer"
        except:
            return "Unknown Developer"
    
    def _load_configurations(self) -> None:
        """Load agent and task configurations from YAML files.
        
        Raises:
            ConfigurationError: If configuration files are not found or invalid.
        """
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_path = os.path.join(base_dir, "config")
        agents_path = os.path.join(config_path, "agents.yaml")
        tasks_path = os.path.join(config_path, "tasks.yaml")
        
        try:
            with open(agents_path, "r", encoding="utf-8") as f:
                self.agents_config = yaml.safe_load(f)
            with open(tasks_path, "r", encoding="utf-8") as f:
                self.tasks_config = yaml.safe_load(f)
        except FileNotFoundError as e:
            raise ConfigurationError(
                "config_files",
                f"Configuration file not found: {e}"
            )
        except yaml.YAMLError as e:
            raise ConfigurationError(
                "config_files",
                f"Invalid YAML configuration: {e}"
            )
    
    def _create_agent(self, agent_name: str, tools: list = None, verbose: bool = False) -> Agent:
        """Create an agent from configuration.
        
        Args:
            agent_name: Name of the agent in the configuration.
            tools: Optional list of tools for the agent.
            verbose: Whether to enable verbose output.
            
        Returns:
            Configured Agent instance.
            
        Raises:
            ConfigurationError: If agent configuration is not found.
        """
        if agent_name not in self.agents_config:
            raise ConfigurationError(
                "agent_config",
                f"Agent '{agent_name}' not found in configuration"
            )
        
        return Agent(
            config=self.agents_config[agent_name],
            llm=self.llm,
            tools=tools or [],
            verbose=verbose
        )
    
    def _create_task(self, task_name: str, agent: Agent, context: list = None, **kwargs) -> Task:
        """Create a task from configuration.
        
        Args:
            task_name: Name of the task in the configuration.
            agent: The agent responsible for the task.
            context: Optional list of dependent tasks.
            **kwargs: Additional parameters for task description formatting.
            
        Returns:
            Configured Task instance.
            
        Raises:
            ConfigurationError: If task configuration is not found.
        """
        if task_name not in self.tasks_config:
            raise ConfigurationError(
                "task_config",
                f"Task '{task_name}' not found in configuration"
            )
        
        cfg = self.tasks_config[task_name]
        description = cfg['description'].format(**kwargs) if kwargs else cfg['description']
        
        return Task(
            description=description,
            expected_output=cfg['expected_output'],
            agent=agent,
            context=context or []
        )
    
    def create_analysis_crew(self) -> Crew:
        """Create the main code analysis crew.
        
        This crew performs comprehensive code analysis including architecture,
        heuristics, SOLID principles, design patterns, ownership analysis,
        quality assessment, and mentoring suggestions.
        
        Returns:
            Configured Crew for code analysis.
        """
        # Create agents
        senior_architect = self._create_agent('senior_architect')
        senior_analytics = self._create_agent('senior_analytics')
        quality_consultant = self._create_agent('quality_consultant')
        quality_control_manager = self._create_agent('quality_control_manager')
        git_analyst = self._create_agent(
            'git_analyst',
            tools=[CurrentUserTool(), OwnershipTool(), UserCommitsTool(), CommitDiffTool()]
        )
        grader_agent = self._create_agent(
            'grader_agent',
            tools=[ScoreFormalizerTool()]
        )
        code_mentor = self._create_agent('code_mentor')
        
        # Create tasks
        task_estrutura = self._create_task(
            'analise_estrutura',
            senior_architect,
            input=self.commit_message
        )
        task_heuristicas = self._create_task(
            'analise_heuristicas',
            senior_analytics,
            input=self.commit_message
        )
        task_solid = self._create_task(
            'analise_solid',
            quality_consultant,
            input=self.commit_message
        )
        task_padroes = self._create_task(
            'padroes_projeto',
            quality_control_manager,
            input=self.commit_message
        )
        ownership_task = self._create_task('ownership_task', git_analyst)
        quality_analysis_task = self._create_task(
            'quality_analysis_task',
            git_analyst,
            context=[ownership_task]
        )
        grading_task = self._create_task(
            'grading_task',
            grader_agent,
            context=[quality_analysis_task],
            git_user_name=self.git_user_name
        )
        mentoring_task = self._create_task(
            'mentoring_task',
            code_mentor,
            context=[grading_task]
        )
        
        return Crew(
            agents=[
                senior_architect,
                senior_analytics,
                quality_consultant,
                quality_control_manager,
                git_analyst,
                grader_agent,
                code_mentor
            ],
            tasks=[
                task_estrutura,
                task_heuristicas,
                task_solid,
                task_padroes,
                ownership_task,
                quality_analysis_task,
                grading_task,
                mentoring_task
            ],
            process=Process.sequential
        )
    
    def create_summary_crew(self, analysis_result: str) -> Crew:
        """Create a crew for generating PR summaries.
        
        Args:
            analysis_result: The analysis result to summarize.
            
        Returns:
            Configured Crew for summary generation.
        """
        summary_specialist = self._create_agent('summary_specialist')
        
        task_summarize = self._create_task(
            'summarize_analysis',
            summary_specialist,
            analysis_result=analysis_result
        )
        
        return Crew(
            agents=[summary_specialist],
            tasks=[task_summarize],
            process=Process.sequential
        )
    
    def create_lgpd_crew(self) -> Crew:
        """Create a crew for LGPD compliance verification.
        
        This crew analyzes AI provider data collection policies and determines
        LGPD compliance.
        
        Returns:
            Configured Crew for LGPD verification.
        """
        # Prepare tools list
        tools = [self.web_search_tool] if self.web_search_tool else []
        
        policy_analyst = self._create_agent(
            'dataCollect_policy_analytics',
            tools=tools
        )
        lgpd_judge = self._create_agent(
            'lgpd_judge',
            tools=tools
        )
        
        task_policy = self._create_task(
            'policy_analytics',
            policy_analyst,
            IA_PROVIDER=self.provider,
            IA_MODEL=self.model
        )
        task_judging = self._create_task(
            'lgpd_judging',
            lgpd_judge,
            context=[task_policy]
        )
        
        return Crew(
            agents=[policy_analyst, lgpd_judge],
            tasks=[task_policy, task_judging],
            process=Process.sequential
        )
    
    def execute_crew(self, crew: Crew, inputs: Dict[str, Any] = None) -> Any:
        """Execute a crew with optional inputs.
        
        Args:
            crew: The crew to execute.
            inputs: Optional dictionary of inputs for the crew.
            
        Returns:
            The crew execution result.
            
        Raises:
            Exception: If crew execution fails.
        """
        try:
            if inputs:
                return crew.kickoff(inputs=inputs)
            else:
                return crew.kickoff()
        except Exception as e:
            raise Exception(f"Crew execution failed: {str(e)}")
