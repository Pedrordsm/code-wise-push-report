import os
import sys
from .crew import Codewise
from .entradagit import gerar_entrada_automatica, obter_mudancas_staged
from crewai import Task, Crew

class CodewiseRunner:
    def __init__(self):
        self.BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.caminho_entrada = os.path.join(self.BASE_DIR, ".entrada_temp.txt")

    def executar(self, caminho_repo: str, nome_branch: str, modo: str):
        
        contexto_para_ia = ""

        if modo == 'lint':
            resultado_git = obter_mudancas_staged(caminho_repo)
            
            if resultado_git is None:
                print("Nenhum problema aparente detectado.")
                sys.exit(0)
            
            if resultado_git.startswith("AVISO:") or resultado_git.startswith("FALHA:"):
                print(resultado_git)
                sys.exit(0)
            
            contexto_para_ia = resultado_git
        else:
            if not gerar_entrada_automatica(caminho_repo, self.caminho_entrada, nome_branch):
                sys.exit(0)
            contexto_para_ia = self._ler_arquivo(self.caminho_entrada)
        
        codewise_instance = Codewise(commit_message=contexto_para_ia)
        resultado_final = ""

        if modo == 'titulo':
            agent = codewise_instance.summary_specialist()
            task = Task(description=f"Crie um título de PR conciso no padrão Conventional Commits para as seguintes mudanças. A resposta deve ser APENAS o título, **obrigatoriamente em Português do Brasil**, sem aspas, acentos graves ou qualquer outro texto:\n{contexto_para_ia}", expected_output="Um único título de PR.", agent=agent)
            resultado_final = Crew(agents=[agent], tasks=[task]).kickoff()

        elif modo == 'descricao':
            agent = codewise_instance.summary_specialist()
            task = Task(description=f"Crie uma descrição de um parágrafo **obrigatoriamente em Português do Brasil** para um Pull Request para as seguintes mudanças:\n{contexto_para_ia}", expected_output="Um único parágrafo de texto.", agent=agent)
            resultado_final = Crew(agents=[agent], tasks=[task]).kickoff()

        elif modo == 'analise':
            analysis_crew = codewise_instance.crew()
            analysis_crew.kickoff(inputs={'input': contexto_para_ia})

            print("Salvando relatórios de análise individuais...", file=sys.stderr)

            output_dir_name = "analises-concluidas"
            output_dir_path = os.path.join(caminho_repo, output_dir_name)
            os.makedirs(output_dir_path, exist_ok=True)

            keyword_map = {
                "inspeção na estrutura do projeto": "arquitetura_atual.md",
                "analise as integrações, bibliotecas externas e APIs": "analise_heuristicas_integracoes.md",
                "aderência da mudança aos princípios S.O.L.I.D.": "analise_solid.md",
                "aplicação correta ou ausência de padrões de projeto": "padroes_de_projeto.md"
            }

            tasks_processed = {key: False for key in keyword_map}

            for task in analysis_crew.tasks:
                for keyword, filename in keyword_map.items():
                    if keyword in task.description and not tasks_processed[keyword]:
                        file_path = os.path.join(output_dir_path, filename)
                        try:
                            with open(file_path, "w", encoding="utf-8") as f:
                                f.write(str(task.output))
                            print(f"   - Arquivo '{filename}' salvo com sucesso em '{output_dir_path}'.", file=sys.stderr)
                            tasks_processed[keyword] = True
                            break 
                        except Exception as e:
                            print(f"   - ERRO ao salvar o arquivo '{filename}': {e}", file=sys.stderr)
            
            resumo_agent = codewise_instance.summary_specialist()
            resumo_task = Task(
                description="Com base no contexto da análise completa fornecida, crie um 'Resumo Executivo do Pull Request' **obrigatoriamente em Português do Brasil**, bem formatado em markdown, com 3-4 bullet points detalhados.",
                expected_output="Um resumo executivo em markdown.",
                agent=resumo_agent,
                context=analysis_crew.tasks
            )
            resultado_final = Crew(agents=[resumo_agent], tasks=[resumo_task]).kickoff()

            mentor_agent = codewise_instance.code_mentor()
            mentor_task = Task(
                description="Com base nas análises técnicas realizadas, comente e sugira recursos educacionais personalizados com base nas mudanças **obrigatoriamente em Português do Brasil**, bem formatado em markdown, com links que possuam conteúdo para melhorar o código.",
                expected_output="Sugestões de melhoria.",
                agent=mentor_agent,
                context=analysis_crew.tasks
            )
            resultado_mentor = Crew(agents=[mentor_agent],tasks=[mentor_task]).kickoff()
            mentor_file_path = os.path.join(output_dir_path, "sugestoes_aprendizado.md")
            try:
                with open(mentor_file_path, "w", encoding="utf-8") as f:
                    f.write(str(resultado_mentor))
                    print(f"   - Arquivo 'sugestoes_aprendizado.md' salvo com sucesso em '{output_dir_path}'.", file=sys.stderr)
            except Exception as e:
                print(f"   - ERRO ao salvar o arquivo 'sugestoes_aprendizado.md': {e}", file=sys.stderr)

            
            # Tentativa de colocar a analise lgpd para rodar antes do envio dos dados sensiveis
            policy_agent = codewise_instance.dataCollect_policy_analytics()
            provedor_usado = codewise_instance.provider
            modelo_api_key = codewise_instance.model

            policy_analytics_task = Task(
                description=f"Analise a documentação oficial da política de coleta de dados do provedor '{provedor_usado}' para o modelo '{modelo_api_key}'. Crie um relatório, **obrigatoriamente em Português do Brasil**, focado nos pontos-chave de como os dados de entrada do usuário (inputs de API) são tratados, incluindo coleta, uso e retenção.",
                expected_output="Um relatório sobre a política de coleta de dados do modelo de api utilizado",
                agent=policy_analytics_agent
            )
            resultado_policy = Crew(agents=[policy_analytics_agent], tasks=[policy_analytics_task]).kickoff()
            policy_file_path = os.path.join(output_dir_path, "analise_politica_coleta_de_dados.md")
            try:
                with open(policy_file_path, "w", encoding="utf-8") as f:
                    f.write(str(resultado_policy))
                    print(f"   - Arquivo 'analise_politica_coleta_de_dados.md' salvo com sucesso em '{output_dir_path}'.", file=sys.stderr)
            except Exception as e:
                print(f"    - ERRO ao salvar o arquivo 'analise_politica_coleta_de_dados.md': {e}", file=sys.stderr)
            # fim
                
        elif modo == 'lint':
            agent = codewise_instance.quality_consultant()
            task = Task(description=f"Analise rapidamente as seguintes mudanças de código ('git diff') e aponte APENAS problemas óbvios ou code smells. A resposta deve ser **obrigatoriamente em Português do Brasil**. Seja conciso. Se não houver problemas, retorne 'Nenhum problema aparente detectado.'.\n\nCódigo a ser analisado:\n{contexto_para_ia}", expected_output="Uma lista curta em bullet points com sugestões, ou uma mensagem de que está tudo ok.", agent=agent)
            resultado_final = Crew(agents=[agent], tasks=[task]).kickoff()
        
        if os.path.exists(self.caminho_entrada):
            os.remove(self.caminho_entrada)

        print(str(resultado_final).strip().replace('`', ''))

    def _ler_arquivo(self, file_path: str) -> str:
        try:
            with open(file_path, "r", encoding="utf-8") as f: return f.read()
        except FileNotFoundError: return ""