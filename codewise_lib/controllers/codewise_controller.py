"""Main controller for CodeWise application.

This module provides the main controller that orchestrates all operations,
routing commands to appropriate handlers and coordinating between models and views.
"""

import os
import sys
import re
from typing import Optional

from ..models.git_service import GitService
from ..models.llm_factory import LLMFactory
from ..models.crew_orchestrator import CrewOrchestrator
from ..models.lgpd_service import LGPDService
from ..models.notification_service import NotificationService
from ..models.analysis_models import AnalysisResult
from ..models.exceptions import (
    CodewiseError,
    GitOperationError,
    ConfigurationError,
    FileOperationError
)
from ..views.output_formatter import OutputFormatter
from ..views.file_writer import FileWriter
from ..views.console_view import ConsoleView
from ..views.notification_formatter import NotificationFormatter


class CodewiseController:
    """Main controller for CodeWise operations.
    
    This controller orchestrates all CodeWise operations, routing execution
    to appropriate mode handlers and coordinating between models and views
    following the MVC pattern.
    """
    
    def __init__(self):
        """Initialize CodewiseController with all required services."""
        # Initialize views
        self.console = ConsoleView()
        self.formatter = OutputFormatter()
        self.file_writer = FileWriter()
        
        # Initialize models
        self.llm_factory = LLMFactory()
        self.notification_service = NotificationService()
        self.lgpd_service = LGPDService()
        
        # Temporary file for Git context
        self.temp_input_file = ".entrada_temp.txt"
    
    def execute(self, repo_path: str, branch: str, mode: str) -> int:
        """Execute CodeWise in the specified mode.
        
        This is the main entry point that routes execution to the appropriate
        mode handler based on user input.
        
        Args:
            repo_path: Path to the Git repository.
            branch: Branch name to analyze.
            mode: Execution mode ('analise', 'titulo', 'descricao', 'lint', 'lgpd_verify').
            
        Returns:
            Exit code (0 for success, non-zero for errors).
        """
        try:
            # Validate mode
            valid_modes = ['analise', 'titulo', 'descricao', 'lint', 'lgpd_verify']
            if mode not in valid_modes:
                self.console.print_error(
                    f"Invalid mode '{mode}'. Valid modes: {', '.join(valid_modes)}"
                )
                return 1
            
            # Handle LGPD verification mode
            if mode == 'lgpd_verify':
                lgpd_compliant = self._handle_lgpd_verification(repo_path)
                return 0 if lgpd_compliant else 1
            
            # For other modes, just check if LGPD was verified (don't prompt again)
            lgpd_dir = os.path.join(repo_path, "analises-julgamento-lgpd")
            judge_file = os.path.join(lgpd_dir, "julgamento_lgpd.md")
            if not os.path.exists(judge_file):
                self.console.print_error(
                    "LGPD verification not found. Please run with --mode lgpd_verify first."
                )
                return 1
            
            # Get context for AI analysis
            context = self._get_analysis_context(repo_path, branch, mode)
            
            if not context:
                self.console.print_warning("No changes to analyze")
                return 0
            
            # Route to appropriate handler
            if mode == 'analise':
                return self.handle_analysis_mode(repo_path, context)
            elif mode == 'titulo':
                return self.handle_title_mode(context)
            elif mode == 'descricao':
                return self.handle_description_mode(context)
            elif mode == 'lint':
                return self.handle_lint_mode(context)
            
            return 0
            
        except CodewiseError as e:
            self.console.print_error(str(e))
            return 1
        except Exception as e:
            self.console.print_error(f"Unexpected error: {str(e)}")
            return 1
        finally:
            # Cleanup temporary files
            if os.path.exists(self.temp_input_file):
                os.remove(self.temp_input_file)
    
    def _get_analysis_context(self, repo_path: str, branch: str, mode: str) -> Optional[str]:
        """Get the context for AI analysis based on mode.
        
        Args:
            repo_path: Path to the repository.
            branch: Branch name.
            mode: Execution mode.
            
        Returns:
            Context string for AI analysis, or None if no changes.
        """
        git_service = GitService(repo_path)
        
        if mode == 'lint':
            # For lint mode, get staged changes
            result = git_service.get_staged_changes()
            
            if result is None:
                return None
            
            if result.startswith("WARNING:"):
                self.console.print_warning(result)
                return None
            
            return result
        else:
            # For other modes, generate full context
            try:
                # Fetch updates
                self.console.print_progress("Fetching repository updates...")
                git_service.fetch_updates(branch)
                
                # Determine base reference
                default_branch = git_service.get_default_branch()
                
                # Check if remote has any branches at all
                try:
                    # Try to get remote branches
                    result = git_service._run_command(["git", "ls-remote", "--heads", "origin"])
                    has_remote_branches = bool(result.strip())
                except:
                    has_remote_branches = False
                
                if not has_remote_branches:
                    # No remote branches yet - analyze all local commits
                    self.console.print_success(
                        "No remote branches found. Analyzing all local commits."
                    )
                    # Use initial commit as base
                    try:
                        first_commit = git_service._run_command(["git", "rev-list", "--max-parents=0", "HEAD"])
                        base_ref = first_commit.strip()
                    except:
                        self.console.print_warning("Cannot determine commit history")
                        return None
                elif branch == default_branch:
                    # If analyzing the default branch itself, compare with its remote version
                    base_ref = f"origin/{branch}"
                    self.console.print_success(
                        f"Analyzing changes on '{branch}' branch."
                    )
                elif git_service.branch_exists_on_remote(branch):
                    # Branch exists on remote, compare with its remote version
                    base_ref = f"origin/{branch}"
                    self.console.print_success(
                        f"Branch '{branch}' exists on remote. Analyzing new commits."
                    )
                else:
                    # New branch, compare with default branch
                    base_ref = f"origin/{default_branch}"
                    self.console.print_success(
                        f"Branch '{branch}' is new. Comparing with '{default_branch}'."
                    )
                
                # Get commit messages
                commits = git_service.get_commit_range(base_ref, branch)
                
                if not commits:
                    self.console.print_warning("No new commits found")
                    return None
                
                # Get diff
                diff = git_service.get_diff(base_ref, branch)
                
                # Build context
                context_lines = [
                    f"Analyzing {len(commits)} new commit(s).\n",
                    "Commit messages:"
                ]
                context_lines.extend(commits)
                context_lines.append("\n" + "=" * 80)
                context_lines.append("Consolidated code differences to analyze:")
                context_lines.append(diff)
                
                context = "\n".join(context_lines)
                
                # Save to temporary file
                with open(self.temp_input_file, 'w', encoding='utf-8') as f:
                    f.write(context)
                
                return context
                
            except GitOperationError as e:
                raise e
    
    def _handle_lgpd_verification(self, repo_path: str) -> bool:
        """Handle LGPD compliance verification.
        
        Args:
            repo_path: Path to the repository.
            
        Returns:
            True if provider is LGPD compliant and user authorizes, False otherwise.
        """
        lgpd_dir = os.path.join(repo_path, "analises-julgamento-lgpd")
        policy_file = os.path.join(lgpd_dir, "analise_politica_coleta_de_dados.md")
        judge_file = os.path.join(lgpd_dir, "julgamento_lgpd.md")
        
        # Check if analysis already exists
        if self._check_existing_lgpd_analysis(policy_file, judge_file):
            self.console.print_success("Using existing LGPD analysis")
            compliant = self._read_lgpd_judgment(judge_file)
            
            if compliant:
                # Ask for user authorization
                return self._get_user_authorization(policy_file)
            else:
                self.console.print_error("Provider is NOT LGPD compliant")
                return False
        
        # Perform new LGPD verification
        self.console.print_progress("Starting LGPD compliance verification...")
        
        try:
            # Create crew orchestrator
            orchestrator = CrewOrchestrator(self.llm_factory)
            
            # Create and execute LGPD crew
            lgpd_crew = orchestrator.create_lgpd_crew()
            result = orchestrator.execute_crew(lgpd_crew)
            
            # Ensure directory exists
            self.file_writer.ensure_directory(lgpd_dir)
            
            # Save policy analysis
            policy_output = str(lgpd_crew.tasks[0].output)
            self.file_writer.write_file(policy_file, policy_output)
            self.console.print_success(f"Policy analysis saved to {policy_file}")
            
            # Save judgment
            judge_output = str(lgpd_crew.tasks[1].output)
            self.file_writer.write_file(judge_file, judge_output)
            self.console.print_success(f"LGPD judgment saved to {judge_file}")
            
            # Parse result
            compliant = self._read_lgpd_judgment(judge_file)
            
            if compliant:
                self.console.print_success("Provider is LGPD compliant")
                # Ask for user authorization
                return self._get_user_authorization(policy_file)
            else:
                self.console.print_error("Provider is NOT LGPD compliant")
                return False
            
        except Exception as e:
            self.console.print_error(f"LGPD verification failed: {str(e)}")
            return False
    
    def _check_existing_lgpd_analysis(self, policy_file: str, judge_file: str) -> bool:
        """Check if LGPD analysis already exists for current provider/model.
        
        Args:
            policy_file: Path to policy analysis file.
            judge_file: Path to judgment file.
            
        Returns:
            True if existing analysis matches current provider/model.
        """
        if not (os.path.exists(policy_file) and os.path.exists(judge_file)):
            return False
        
        provider = os.getenv("AI_PROVIDER", "").lower()
        model = os.getenv("AI_MODEL", "").lower()
        model = re.sub(r'[*_#>`~]', '', model)
        provider_model = provider + model
        
        try:
            with open(policy_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line_clean = line.strip().lower()
                    line_clean = re.sub(r'[*_#>`~]', '', line_clean).strip()
                    
                    if line_clean == provider_model:
                        return True
                    if not line:
                        return False
        except Exception:
            return False
        
        return False
    
    def _read_lgpd_judgment(self, judge_file: str) -> bool:
        """Read LGPD judgment result from file.
        
        Args:
            judge_file: Path to judgment file.
            
        Returns:
            True if judgment is "sim" (compliant), False otherwise.
        """
        try:
            with open(judge_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line_clean = line.strip().lower()
                    line_clean = re.sub(r'[*_#>`~]', '', line_clean).strip()
                    
                    if line_clean == "sim":
                        return True
                    if line_clean == "não":
                        return False
        except Exception as e:
            self.console.print_error(f"Failed to read judgment: {str(e)}")
        
        return False
    
    def _get_user_authorization(self, policy_file: str) -> bool:
        """Get user authorization to send data to AI provider.
        
        Displays the policy analysis conclusion and asks for user consent.
        
        Args:
            policy_file: Path to the policy analysis file.
            
        Returns:
            True if user authorizes, False otherwise.
        """
        try:
            # Read and display policy conclusion
            with open(policy_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            print("\nResumo sobre a analise da politica de uso de dados:")
            print()
            
            # Extract conclusion section
            conclusion_match = re.search(
                r"(?i)^#+\s*Conclusao\s*\n+(.*)",
                content,
                re.MULTILINE | re.DOTALL
            )
            
            if conclusion_match:
                conclusion = conclusion_match.group(1).strip()
                print(conclusion)
            else:
                print("Conclusao nao encontrada no arquivo de analise.")
            
            print()
            print("-" * 40)
            print()
            print("[WARNING] Esta acao requer o envio de dados, como por exemplo,")
            print("o codigo-fonte, para o provedor da API key fornecida.")
            print()
            
            # Ask for authorization
            while True:
                choice = input(
                    "* Com base na verificacao apresentada acima, voce gostaria de "
                    "continuar com o envio de seus dados para o provedor e modelo "
                    "de api key escolhido? [S/N]: "
                ).strip().upper()
                
                if choice == "S":
                    print()
                    print("-" * 40)
                    print()
                    print("[OK] Voce AUTORIZOU o envio de dados necessarios para o")
                    print("provedor da API key escolhida!")
                    print()
                    print("Continuando as analises...")
                    print()
                    print("-" * 40)
                    print()
                    return True
                elif choice == "N":
                    print()
                    print("-" * 40)
                    print()
                    print("[ERROR] Voce NAO AUTORIZOU o envio de dados necessarios")
                    print("para o provedor da API key escolhida.")
                    print()
                    print("Execute novamente com outro modelo ou provedor.")
                    print()
                    print("Dados NAO ENVIADOS! Interrompendo programa...")
                    print()
                    print("-" * 40)
                    return False
                else:
                    print("Por favor, digite S para Sim ou N para Nao.")
                    
        except Exception as e:
            self.console.print_error(f"Erro em obter a autorizacao do usuario: {e}")
            return False
    
    def handle_analysis_mode(self, repo_path: str, context: str) -> int:
        """Handle full code analysis mode.
        
        Args:
            repo_path: Path to the repository.
            context: Analysis context from Git.
            
        Returns:
            Exit code (0 for success).
        """
        try:
            self.console.print_header("Code Analysis")
            
            # Create crew orchestrator
            orchestrator = CrewOrchestrator(self.llm_factory, context)
            
            # Create and execute analysis crew
            self.console.print_progress("Running code analysis...")
            analysis_crew = orchestrator.create_analysis_crew()
            orchestrator.execute_crew(analysis_crew, inputs={'input': context})
            
            # Save individual analysis files
            self.console.print_progress("Saving analysis reports...")
            output_dir = os.path.join(repo_path, "analises-concluidas")
            self.file_writer.ensure_directory(output_dir)
            
            # Map tasks to files
            task_file_map = {
                "inspeção na estrutura do projeto": "arquitetura_atual.md",
                "analise as integrações, bibliotecas externas e APIs": "analise_heuristicas_integracoes.md",
                "aderência da mudança aos princípios S.O.L.I.D.": "analise_solid.md",
                "aplicação correta ou ausência de padrões de projeto": "padroes_de_projeto.md"
            }
            
            tasks_processed = {key: False for key in task_file_map}
            
            for task in analysis_crew.tasks:
                for keyword, filename in task_file_map.items():
                    if keyword in task.description and not tasks_processed[keyword]:
                        file_path = os.path.join(output_dir, filename)
                        self.file_writer.write_file(file_path, str(task.output))
                        self.console.print_success(f"Saved {filename}")
                        tasks_processed[keyword] = True
                        break
            
            # Generate summary
            self.console.print_progress("Generating summary...")
            summary_crew = orchestrator.create_summary_crew("")
            summary_crew.tasks[0].context = analysis_crew.tasks
            summary_result = orchestrator.execute_crew(summary_crew)
            
            # Save mentoring suggestions
            self.console.print_progress("Generating mentoring suggestions...")
            # Note: Mentoring is already part of analysis_crew
            mentor_output = None
            for task in analysis_crew.tasks:
                if "mentoring" in task.description.lower() or "aprendizado" in task.description.lower():
                    mentor_output = str(task.output)
                    break
            
            if mentor_output:
                mentor_file = os.path.join(output_dir, "sugestoes_aprendizado.md")
                self.file_writer.write_file(mentor_file, mentor_output)
                self.console.print_success("Saved sugestoes_aprendizado.md")
            
            # Save grading task output
            self.console.print_progress("Saving performance score...")
            grading_output = None
            for task in analysis_crew.tasks:
                task_desc = task.description.lower()
                if "grading" in task_desc or "nota" in task_desc or "avaliação" in task_desc or "registrar" in task_desc:
                    grading_output = str(task.output)
                    break
            
            if grading_output:
                grading_file = os.path.join(output_dir, "avaliacao_performance.md")
                self.file_writer.write_file(grading_file, grading_output)
                self.console.print_success("Saved avaliacao_performance.md")
            
            # Extract and send performance score notification
            self._send_score_notification(analysis_crew.tasks)
            
            # Print summary
            self.console.print_header("Summary")
            summary_text = str(summary_result).strip().replace('`', '')
            self.console.print_result(summary_text)
            
            return 0
            
        except Exception as e:
            self.console.print_error(f"Analysis failed: {str(e)}")
            return 1
    
    def _send_score_notification(self, tasks: list) -> None:
        """Extract score from grading task and send notification.
        
        Args:
            tasks: List of completed tasks from the analysis crew.
        """
        try:
            # Find the grading task output
            grading_output = None
            for task in tasks:
                task_desc = task.description.lower()
                # Debug: print task descriptions
                print(f"[DEBUG] Checking task: {task_desc[:100]}...", file=sys.stderr)
                
                if "grading" in task_desc or "nota" in task_desc or "avaliação" in task_desc or "registrar" in task_desc:
                    grading_output = str(task.output)
                    print(f"[DEBUG] Found grading task output: {grading_output}", file=sys.stderr)
                    break
            
            if not grading_output:
                print("[DEBUG] No grading task found in tasks", file=sys.stderr)
                print(f"[DEBUG] Total tasks: {len(tasks)}", file=sys.stderr)
                for i, task in enumerate(tasks):
                    print(f"[DEBUG] Task {i}: {task.description[:50]}...", file=sys.stderr)
                return  # No grading task found
            
            # Parse the score output
            # Expected format: "Desenvolvedor: Name\nNota Final: X/10\nMotivo: Justification"
            import re
            from datetime import datetime
            
            developer_match = re.search(r"Desenvolvedor:\s*(.+?)(?:\n|$)", grading_output, re.IGNORECASE)
            score_match = re.search(r"Nota\s+Final:\s*(\d+)/10", grading_output, re.IGNORECASE)
            justification_match = re.search(r"Motivo:\s*(.+)", grading_output, re.DOTALL | re.IGNORECASE)
            
            print(f"[DEBUG] Developer match: {developer_match.group(1) if developer_match else 'None'}", file=sys.stderr)
            print(f"[DEBUG] Score match: {score_match.group(1) if score_match else 'None'}", file=sys.stderr)
            print(f"[DEBUG] Justification match: {'Found' if justification_match else 'None'}", file=sys.stderr)
            
            if developer_match and score_match:
                developer = developer_match.group(1).strip()
                score = int(score_match.group(1))
                justification = justification_match.group(1).strip() if justification_match else "No justification provided"
                
                print(f"[DEBUG] Extracted - Developer: {developer}, Score: {score}, Type: {type(score)}", file=sys.stderr)
                
                # Save score to file for testing
                # Ensure score is formatted as integer
                score_value = int(score)
                score_file_content = f"""# Performance Score Report

**Developer:** {developer}
**Score:** {score_value}/10
**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Justification

{justification}

---
*Generated by CodeWise*
"""
                
                try:
                    score_file_path = os.path.join("analises-concluidas", "performance_score.md")
                    print(f"[DEBUG] Attempting to write score file to: {score_file_path}", file=sys.stderr)
                    self.file_writer.write_file(score_file_path, score_file_content)
                    self.console.print_success(f"Score saved to {score_file_path}")
                    print(f"[DEBUG] Score file written successfully", file=sys.stderr)
                except Exception as e:
                    print(f"[DEBUG] Failed to write score file: {str(e)}", file=sys.stderr)
                    self.console.print_warning(f"Failed to save score file: {str(e)}")
                
                # Send notification
                self.console.print_progress(f"Sending score notification for {developer}...")
                success = self.notification_service.send_score_notification(
                    developer=developer,
                    score=score,
                    justification=justification
                )
                
                if success:
                    self.console.print_success("Score notification sent successfully")
                else:
                    self.console.print_warning("Score notification was not sent (notifications may be disabled)")
            else:
                print(f"[DEBUG] Failed to extract score information from grading output", file=sys.stderr)
                print(f"[DEBUG] Grading output was: {grading_output}", file=sys.stderr)
                    
        except Exception as e:
            # Don't fail the analysis if notification fails
            print(f"[DEBUG] Exception in _send_score_notification: {str(e)}", file=sys.stderr)
            import traceback
            traceback.print_exc(file=sys.stderr)
            self.console.print_warning(f"Failed to send score notification: {str(e)}")
    
    def handle_title_mode(self, context: str) -> int:
        """Handle PR title generation mode.
        
        Args:
            context: Analysis context from Git.
            
        Returns:
            Exit code (0 for success).
        """
        try:
            orchestrator = CrewOrchestrator(self.llm_factory)
            summary_agent = orchestrator._create_agent('summary_specialist')
            
            from crewai import Task, Crew
            
            task = Task(
                description=f"Crie um título de PR conciso no padrão Conventional Commits para as seguintes mudanças. A resposta deve ser APENAS o título, **obrigatoriamente em Português do Brasil**, sem aspas, acentos graves ou qualquer outro texto:\n{context}",
                expected_output="Um único título de PR.",
                agent=summary_agent
            )
            
            crew = Crew(agents=[summary_agent], tasks=[task])
            result = crew.kickoff()
            
            title = str(result).strip().replace('`', '')
            self.console.print_result(title)
            
            return 0
            
        except Exception as e:
            self.console.print_error(f"Title generation failed: {str(e)}")
            return 1
    
    def handle_description_mode(self, context: str) -> int:
        """Handle PR description generation mode.
        
        Args:
            context: Analysis context from Git.
            
        Returns:
            Exit code (0 for success).
        """
        try:
            orchestrator = CrewOrchestrator(self.llm_factory)
            summary_agent = orchestrator._create_agent('summary_specialist')
            
            from crewai import Task, Crew
            
            task = Task(
                description=f"Crie uma descrição de um parágrafo **obrigatoriamente em Português do Brasil** para um Pull Request para as seguintes mudanças:\n{context}",
                expected_output="Um único parágrafo de texto.",
                agent=summary_agent
            )
            
            crew = Crew(agents=[summary_agent], tasks=[task])
            result = crew.kickoff()
            
            description = str(result).strip().replace('`', '')
            self.console.print_result(description)
            
            return 0
            
        except Exception as e:
            self.console.print_error(f"Description generation failed: {str(e)}")
            return 1
    
    def handle_lint_mode(self, diff: str) -> int:
        """Handle quick lint/code smell detection mode.
        
        Args:
            diff: Git diff to analyze.
            
        Returns:
            Exit code (0 for success).
        """
        try:
            orchestrator = CrewOrchestrator(self.llm_factory)
            quality_agent = orchestrator._create_agent('quality_consultant')
            
            from crewai import Task, Crew
            
            task = Task(
                description=f"Analise rapidamente as seguintes mudanças de código ('git diff') e aponte APENAS problemas óbvios ou code smells. A resposta deve ser **obrigatoriamente em Português do Brasil**. Seja conciso. Se não houver problemas, retorne 'Nenhum problema aparente detectado.'.\n\nCódigo a ser analisado:\n{diff}",
                expected_output="Uma lista curta em bullet points com sugestões, ou uma mensagem de que está tudo ok.",
                agent=quality_agent
            )
            
            crew = Crew(agents=[quality_agent], tasks=[task])
            result = crew.kickoff()
            
            lint_result = str(result).strip().replace('`', '')
            self.console.print_result(lint_result)
            
            return 0
            
        except Exception as e:
            self.console.print_error(f"Lint analysis failed: {str(e)}")
            return 1
    
    def handle_lgpd_verify_mode(self) -> bool:
        """Handle LGPD verification mode.
        
        Returns:
            True if provider is compliant, False otherwise.
        """
        # This is handled in execute() method
        pass
