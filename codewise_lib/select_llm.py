import os
from crewai import LLM
import sys

def create_llm(provider:str, model:str)-> LLM:
    if provider == "GEMINI":
        if not os.getenv("GEMINI_API_KEY"):
            print("Erro: A variável de ambiente GEMINI_API_KEY não foi definida.")
            sys.exit(1)
        try:
            return LLM(
                model= "gemini/" + model,
                temperature=0.7
            )
        except Exception as e:
            print(f"Erro ao inicializar o LLM. Verifique sua chave de API e dependências. Erro: {e}")
            sys.exit(1)
    elif provider == "OPENAI":
        if not os.getenv("OPENAI_API_KEY"):
            print("Erro: A variável de ambiente OPENAI_API_KEY não foi definida.")
            sys.exit(1)
        try:
            return LLM(
                model= "openai/" + model,
                temperature=0.7,
            )
        except Exception as e:
            print(f"Erro ao inicializar o LLM. Verifique sua chave de API e dependências. Erro: {e}")
            sys.exit(1)
    elif provider == "GROQ":
        if not os.getenv("GROQ_API_KEY"):
            print("Erro: A variável de ambiente OPENAI_API_KEY não foi definida.")
            sys.exit(1)
        try:
            return LLM(
                model= "groq/" + model,
                temperature=0.7,
            )
        except Exception as e:
            print(f"Erro ao inicializar o LLM. Verifique sua chave de API e dependências. Erro: {e}")
            sys.exit(1)
    elif provider == "COHERE":
        if not os.getenv("COHERE_API_KEY"):
            print("Erro: A variável de ambiente COHERE_API_KEY não foi definida.")
            sys.exit(1)
        try:
            return LLM(
                model= "cohere_chat/" + model,
                temperature=0.7,
            )
        except Exception as e:
            print(f"Erro ao inicializar o LLM. Verifique sua chave de API e dependências. Erro: {e}")
            sys.exit(1)