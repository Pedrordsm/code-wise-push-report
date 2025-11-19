import os
from crewai import LLM
import sys

def create_llm(provider:str, model:str)-> LLM:

    provider_conf = {
         "GEMINI": {
            "env_key": "GEMINI_API_KEY",
            "model_prefix": "gemini/"
        },
        "OPENAI": {
            "env_key": "OPENAI_API_KEY", 
            "model_prefix": "openai/"
        },
        "GROQ": {
            "env_key": "GROQ_API_KEY",
            "model_prefix": "groq/"
        },
        "COHERE": {
            "env_key": "COHERE_API_KEY",
            "model_prefix": "cohere_chat/"
        }
    }

    provider_upper = provider.upper()
    if provider_upper not in provider_conf:
        supported_providers = ", ".join(provider_conf.keys())
        print(f"Erro: Provedor '{provider}' não suportado. Provedores suportados: {supported_providers}")
        sys.exit(1)

    config = provider_conf[provider_upper]
    env_key = config["env_key"]
    env_model = config["model_prefix"]

    if not os.getenv(env_key):
        print(f"A variável de ambiente {env_key} não foi definida.")
    else:
        try:
            return LLM(
                model = env_model + model,
                temperature = 0.7)
        except Exception as e:
            print(f"Erro ao inicializar o LLM para {provider}. Erro: {e}")
            sys.exit(1)
    