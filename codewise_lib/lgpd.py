import os
import sys
import re
from dotenv import load_dotenv
from .crew import Codewise

def verify_lgpd(caminho_repo: str, caminho_dir_lgpd: str, policy_file_path: str, lgpd_judge_file_path: str) -> bool:
    # Tentativa de colocar a analise lgpd para rodar antes do envio dos dados sensiveis
    # instancia sem passar o commit como contexto
    codewise_instance = Codewise()

    print(f"Verificando a política de coleta de dados do provedor com base neste modelo de api key...")

    #lgpd crew
    lgpd_check_crew = codewise_instance.lgpd_crew()

    # roda a analise e o julgamento lgpd (todo o time)
    lgpd_check_crew.kickoff()

    # cria directory
    os.makedirs(caminho_dir_lgpd, exist_ok=True)

    # salvando o resultado da analise da politica de coleta de dados
    resultado_policy = lgpd_check_crew.tasks[0].output

    # definindo caminho e nome do arquivo final.
    #policy_file_path = os.path.join(output_dir_path, "analise_politica_coleta_de_dados.md")

    try:
        with open(policy_file_path, "w", encoding="utf-8") as f:
            f.write(str(resultado_policy))
            print(f"   - Arquivo 'analise_politica_coleta_de_dados.md' salvo com sucesso em '{caminho_dir_lgpd}'.", file=sys.stderr)
    except Exception as e:
        print(f"    - ERRO ao salvar o arquivo 'analise_politica_coleta_de_dados.md': {e}", file=sys.stderr)
    
    
    #salvando o julgamento lgpd
    resultado_lgpd = lgpd_check_crew.tasks[1].output

    # definindo caminho e nome do arquivo final.
    #lgpd_judge_file_path = os.path.join(output_dir_path, "julgamento_lgpd.md")

    try:
        with open(lgpd_judge_file_path, "w", encoding="utf-8") as fj:
            fj.write(str(resultado_lgpd))
            print(f"    - Arquivo 'julgamento_lgpd.md' salvo com sucesso em '{caminho_dir_lgpd}'.", file=sys.stderr)
    except Exception as e:
        print(f"    - ERRO ao salvar o arquivo 'julgamento_lgpd.md': {e}", file=sys.stderr)
    
    # fim

    # Verificação dos resultados da política de coleta de dados do provedor e model utilizados
    return verify_result_judgement(lgpd_judge_file_path)
    
def verify_result_judgement(lgpd_judge_file_path) -> bool:
    try:
        with open(lgpd_judge_file_path, "r", encoding="utf-8") as julgamento:
            #print(julgamento.readline())

            for linha in julgamento:
                linha_clean = linha.strip().lower()

                linha_clean = re.sub(r'[*_#>`~]', '', linha_clean).strip()

                linha_clean = linha_clean.strip()

                if(linha_clean == "sim"):
                    return True
                if (linha_clean == "não"):
                    return False
    except Exception as e:
        print(f"    - ERRO ao ler o arquivo 'julgamento_lgpd.md': {e}", file=sys.stderr)

def verifica_se_existe_analise_lgpd(policy_file_path, lgpd_judge_file_path) -> bool:

    provider = os.getenv("AI_PROVIDER").lower()
    model = os.getenv("AI_MODEL").lower()
    model = re.sub(r'[*_#>`~]', '', model)

    provider_model = provider + model

    if(os.path.exists(policy_file_path) and os.path.exists(lgpd_judge_file_path)):
        try:
            with open(policy_file_path, "r", encoding="utf-8") as f:
                #print(julgamento.readline())

                for linha in f:
                    linha_clean = linha.strip().lower()

                    linha_clean = re.sub(r'[*_#>`~]', '', linha_clean).strip()

                    linha_clean = linha_clean.strip()
                    if(linha_clean == provider_model):
                        return True
                    if(not linha):
                        return False
        except Exception as e:
            print(f"    - ERRO ao ler o arquivo 'analise_politica_coleta_de_dados.md': {e}", file=sys.stderr)    
    else:
        return False 