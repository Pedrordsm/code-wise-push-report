def main():
    print("""
CodeWise CLI 

Ferramenta para análise de código, documentação automática e geração de Pull Requests (Gemini + CrewAI).

 Pré-requisitos para evitar erros:
- Criar um arquivo .env com: GEMINI_API_KEY=sua-chave
- Ter o GitHub CLI (gh) instalado e autenticado
- Estar dentro de um repositório Git com commits válidos.

 Comandos disponíveis:

  codewise-init --all
    → Instala os hooks na pasta .git (pré-push e pré-commit), ativando a automação para o repositório atual.

  codewise-pr
    → Irá perguntar para qual remote você quer que o PR seja criado, caso tenha um upstream configurado.
    → Analisa commits e cria ou atualiza Pull Request com IA (título, descrição e análise técnica).
    → Há duas variações: no origin "codewise-pr-origin" / no upstream "codewise-pr-upstream"	

  codewise-lint
    → Analisa os arquivos staged antes do commit (modo leve, sem IA de PR).

💡 Dica:

- Rode codewise-pr após fazer commits e **antes do push**, para evitar erros silenciosos (ex: falta do `.env`, falha no gh, conflito de branch).
- O pre-push roda codewise-pr automaticamente — útil como backup, mas **pode bloquear o push se algo falhar**.

 →⚠️ Use codewise-init --all uma única vez por repositório para configurar os pré hooks ( a não ser que você queira trocar o destino da criação do PR para o upstream) , 
caso tenha um remoto upstream configurado você pode trocar aonde será criado o PR entre ele e o origin com esse comando também.⚠️

-  **LEMBRE-SE DE CONFIGURAR O .env COM SUA CHAVE DO GEMINI.**
-  Se estiver em um novo Repositório que você nunca trabalhou, você tem que configura-lo corretamente dando push inicial para a ferramenta funcionar.
-  Se você estiver apenas na branch main (sem commits ou sem branch separada), **o PR não poderá ser criado**, pois não há base de comparação.

""")
