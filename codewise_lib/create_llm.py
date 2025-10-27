import os
import sys
from dotenv import load_dotenv

#import dos modelos de api que o codewise vai suportar
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_openai import ChatOpenAI

# trata erros de importação caso as libs não estejam instaladas
# instalar: pip install -r requirements.txt (adicionar as outras llms no requirements.txt)
except ImportError:
    print("Erro: Bibliotecas de LLM (ex: langchain-google-genai, langchain-openai) não encontradas.", file=sys.stderr)
    print("Instale as dependências necessárias (verifique o requirements.txt).", file=sys.stderr)
    sys.exit(1)

def create_llm():
    """
    Lê as variáveis de ambiente e instancia o modelo de LLM selecionado.
    """
    load_dotenv()

    provider = os.getenv("AI_PROVIDER", "google").lower() # só de garantia, se não for definido, setei a do goodle como padrão
     # o modelo acho que é válido ser opcional, pro usuário escolher o modelo padrão do provider se quiser 
     # acho que resolve aquela questão de querer o gemini pro, fica a critério do usuário
    model_name = os.getenv("AI_MODEL") 

    print(f"--- 🤖 Inicializando IA com o provedor: {provider} ---", file=sys.stderr)

    try:
        if provider == "google":
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                print("Erro: AI_PROVIDER='google', mas GEMINI_API_KEY não foi definida no .env", file=sys.stderr)
                sys.exit(1)
            
            model = model_name or "gemini-2.0-flash" # se não for definido, usa a versão gratuita como padrão
            print(f"Usando Google (Gemini) - Modelo: {model}", file=sys.stderr)
            return ChatGoogleGenerativeAI(
                model_name=model,
                google_api_key=api_key
            )

        elif provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                print("Erro: AI_PROVIDER='openai', mas OPENAI_API_KEY não foi definida no .env", file=sys.stderr)
                sys.exit(1)
            
            model = model_name or "gpt-4o-mini" #mesma coisa, usa esse modelo como padrão se não for definido um específicosw
            print(f"Usando OpenAI - Modelo: {model}", file=sys.stderr)
            return ChatOpenAI(
                model_name=model,
                api_key=api_key
            )
        
        # se quisermos, da pra adicionar outras llms aqui

        else:
            print(f"Erro: AI_PROVIDER '{provider}' não é suportado. (Use 'google' ou 'openai')", file=sys.stderr)
            sys.exit(1)

    except Exception as e:
        print(f"Erro ao inicializar o LLM para o provider '{provider}'.", file=sys.stderr)
        print(f"Verifique suas chaves de API e se o modelo '{model_name}' é válido.", file=sys.stderr)
        print(f"Erro original: {e}")
        sys.exit(1)