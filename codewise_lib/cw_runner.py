import os
import sys
import re
from .crew import Codewise
from .entradagit import gerar_entrada_automatica, obter_mudancas_staged
from crewai import Task, Crew


class CodewiseRunner:
    def __init__(self):
        self.BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.caminho_entrada = os.path.join(self.BASE_DIR, ".entrada_temp.txt")

    def executar(self, caminho_repo: str, nome_branch: str, modo: str):
        
        # Tentativa de colocar a analise lgpd para rodar antes do envio dos dados sensiveis
        # instancia sem passar o commit como contexto
        codewise_instance = Codewise()

        print(f"Verificando a política de coleta de dados do provedor com base neste modelo de api key...")

        #lgpd crew
        lgpd_check_crew = codewise_instance.lgpd_crew()

        # roda a analise e o julgamento lgpd (todo o time)
        lgpd_check_crew.kickoff()

        #definicao do caminho
        output_dir_name = "analises-julgamento-lgpd"
        output_dir_path = os.path.join(caminho_repo, output_dir_name)
        os.makedirs(output_dir_path, exist_ok=True)

        # salvando o resultado da analise da politica de coleta de dados
        resultado_policy = lgpd_check_crew.tasks[0].output

        # definindo caminho e nome do arquivo final.
        policy_file_path = os.path.join(output_dir_path, "analise_politica_coleta_de_dados.md")

        try:
            with open(policy_file_path, "w", encoding="utf-8") as f:
                f.write(str(resultado_policy))
                print(f"   - Arquivo 'analise_politica_coleta_de_dados.md' salvo com sucesso em '{output_dir_path}'.", file=sys.stderr)
        except Exception as e:
            print(f"    - ERRO ao salvar o arquivo 'analise_politica_coleta_de_dados.md': {e}", file=sys.stderr)
        
        
        #salvando o julgamento lgpd
        resultado_lgpd = lgpd_check_crew.tasks[1].output

        # definindo caminho e nome do arquivo final.
        lgpd_judge_file_path = os.path.join(output_dir_path, "julgamento_lgpd.md")

        try:
            with open(lgpd_judge_file_path, "w", encoding="utf-8") as fj:
                fj.write(str(resultado_lgpd))
                print(f"    - Arquivo 'julgamento_lgpd.md' salvo com sucesso em '{output_dir_path}'.", file=sys.stderr)
        except Exception as e:
            print(f"    - ERRO ao salvar o arquivo 'julgamento_lgpd.md': {e}", file=sys.stderr)
        
        # fim

        # Verificação dos resultados da política de coleta de dados do provedor e model utilizados
        caminho = os.path.join("analises-julgamento-lgpd", "julgamento_lgpd.md")
        status = False
        print("****************")
        print("Arquivo existe?", os.path.exists(policy_file_path))
        print("Arquivo existe (status)?", os.path.exists(lgpd_judge_file_path))
        print("****************")
        try:
            with open(lgpd_judge_file_path, "r", encoding="utf-8") as julgamento:
                #print(julgamento.readline())

                for linha in julgamento:
                    linha_clean = linha.strip().lower()

                    linha_clean = re.sub(r'[*_#>`~]', '', linha_clean).strip()

                    linha_clean = linha_clean.strip()
                    
                    print(f"{linha_clean}")
                    if(linha_clean == "sim"):
                        print(f"SSSSSSSIIIMMMMMMMMMFASOKFSAOFKAOFKAOS")
                        status = True
                        print("Provedor requisitado está respeitando as normas LGPD, podemos proseguir com a análise.")
                        print(f"Acesse os arquivos 'analise_politica_coleta_de_dados.md.' e 'julgamento_lgpd.md' para comprovações do julgamento.")
                        break
                    if (linha_clean == "não"):
                        status = False
                        print(f"NAAAAAAOFASOKFSAOFKAOFKAOS")
                        print("Provedor requisitado não está dentro das normas LGPD! Por conta disso, as análises foram interrompidas antes que seus dados fossem enviados.")
                        print(f"Tente novamente escolhendo outro provedor ou modelo de api key.")
                        print(f"Para mais informações, acesse os arquivos 'analise_politica_coleta_de_dados.md.' e 'julgamento_lgpd.md'.")
                        break
                    print(f"{linha}")
        except Exception as e:
            print(f"    - ERRO ao ler o arquivo 'julgamento_lgpd.md': {e}", file=sys.stderr)
        
        print(status)
        
        if(status == True):

            print("Provedor requisitado está respeitando as normas LGPD, podemos proseguir com a análise.")
            print(f"Acesse os arquivos 'analise_politica_coleta_de_dados.md.' e 'julgamento_lgpd.md' para comprovações do julgamento.")

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
                    
            elif modo == 'lint':
                agent = codewise_instance.quality_consultant()
                task = Task(description=f"Analise rapidamente as seguintes mudanças de código ('git diff') e aponte APENAS problemas óbvios ou code smells. A resposta deve ser **obrigatoriamente em Português do Brasil**. Seja conciso. Se não houver problemas, retorne 'Nenhum problema aparente detectado.'.\n\nCódigo a ser analisado:\n{contexto_para_ia}", expected_output="Uma lista curta em bullet points com sugestões, ou uma mensagem de que está tudo ok.", agent=agent)
                resultado_final = Crew(agents=[agent], tasks=[task]).kickoff()
            
            if os.path.exists(self.caminho_entrada):
                os.remove(self.caminho_entrada)

            print(str(resultado_final).strip().replace('`', ''))

        else:
            print(f"Provedor requisitado não está dentro das normas LGPD! Por conta disso, as análises foram interrompidas antes que seus dados fossem enviados.")
            print(f"Tente novamente escolhendo outro provedor ou modelo de api key.")
            print(f"Para mais informações, acesse os arquivos 'analise_politica_coleta_de_dados.md.' e 'julgamento_lgpd.md'.")
        
    def _ler_arquivo(self, file_path: str) -> str:
        try:
            with open(file_path, "r", encoding="utf-8") as f: return f.read()
        except FileNotFoundError: return ""