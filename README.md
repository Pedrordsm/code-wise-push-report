#  CodeWise

* Ferramenta instalável via pip que usa IA para analisar o código e automatizar a documentação de Pull Requests através de hooks do Git.

## Funcionalidades Principais
- **Geração de Título:** Cria títulos de PR claros e concisos seguindo o padrão *Conventional Commits*.
- **Geração de Descrição:** Escreve descrições detalhadas baseadas nas alterações do código.
- **Análise Técnica:** Posta um comentário no PR com um resumo executivo de melhorias de arquitetura, aderência a princípios S.O.L.I.D. e outros pontos de qualidade.
- **Automação com hooks:** Integra-se ao seu fluxo de trabalho Git para rodar automaticamente a cada `git commit` e `git push`.

---

## Guia de Instalação 
Siga estes passos para instalar e configurar o CodeWise em qualquer um dos seus repositórios.

---

### Passo 1: Pré-requisitos (ter no PC antes de tudo)

Antes de começar, garanta que você tenha as seguintes ferramentas instaladas em seu sistema:

1.  **Python** (versão 3.11 ou superior).
2.  **Git**.
3.  **GitHub CLI (`gh`)**: Após instalar em (https://cli.github.com), logue com sua conta do GitHub executando `gh auth login` no seu terminal (só precisa fazer isso uma vez por PC).
---

### Passo 2: Configurando Seu Repositório

**Para cada novo Repositório em que você desejar usar o CodeWise, siga os passos abaixo.**
 
"*O ideal é sempre criar um ambiente virtual na pasta raiz do novo repositório para evitar conflitos das dependências.*"

---
#### 2.1 Crie e Utilize um Ambiente Virtual

Para evitar conflitos com outros projetos Python, use um ambiente virtual (`venv`).

* **Para Criar o Ambiente:**

    * Este comando cria uma pasta `.venv` com uma instalação limpa do Python. Faça isso uma única vez por repositório,
    *Lembrando que o ".venv" é o nome da pasta que foi criada, voce pode escolher qualquer outro nome pra ela.*
 

(**dentro da raíz do repositório onde está a pasta .git**)

    ```bash
    # No Windows
    py -m venv .venv
    
    # No Linux/WSL
    python3 -m venv .venv
    ```

* **Para Ativar o Ambiente:**

    * Sempre que for trabalhar no projeto, você precisa ativar o ambiente.

    * **Dica para Windows/PowerShell:** Se o comando de ativação der um erro de política de execução, rode este comando primeiro: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

    ```bash
    # No Windows (PowerShell)
    .\.venv\Scripts\activate
    
    # No Linux/WSL
    source .venv/bin/activate
    ```
    *Você saberá que funcionou porque o nome `(.venv)` aparecerá no início da linha do seu terminal.*
---
#### 2.2 Instale a Ferramenta CodeWise
Com o ambiente virtual ativo, instale a biblioteca com o `pip`.

```bash
pip install codewise-lib
```
 **Pode demorar um pouco pra instalar todas as dependências na primeira vez.**


*Após instalar a lib, você pode confirmar se está tudo certo com o comando `codewise-help`*

---

#### 2.3 Configure a Chave da API (.env)
Para que a IA funcione, você precisa configurar sua chave da API do Google Gemini.

1.  **Na raiz do seu projeto**, crie um arquivo chamado `.env`. Você pode usar os seguintes comandos no terminal:

    * **Windows**
        ```bash
        notepad .env
        ```
    * **Linux/WSL:**
        ```bash
        touch .env && nano .env
        ```

2.  Dentro do arquivo `.env`, cole o seguinte conteúdo, adicione sua chave e salve:
        ```
        GEMINI_API_KEY=SUA_CHAVE_AQUI
        MODEL_NAME=gemini-2.0-flash
        ```
    ⚠️ **Importante:** Lembre-se de adicionar o arquivo `.env` ao seu `.gitignore` para não enviar sua chave secreta para o GitHub ao dar push e que ele deve ser do tipo "arquivo ENV" e não .txt ou coisa do tipo.

---

## Nota Importante: A ferramenta CodeWise espera que seus remotes sigam a convenção padrão do GitHub:

origin: Deve apontar para o seu fork pessoal do repositório.

upstream: (caso você adicione ao repositório)Deve apontar para o repositório principal do qual você fez o fork.

**Caso você comece um repositório novo totalmente zerado, você tem que dar um push inicial com "git push --no-verify" antes de usar a ferramenta para que o GH CLI funcione corretamente ao criar os Pull Requests**

#### 2.4 Agora apenas uma vez > Ative a Automação no Repositório com um comando.
Na raiz do projeto onde também está a pasta .git use:

```bash
codewise-init --all
```
**Use esse comando sempre que você quiser mudar para onde o PULL REQUEST SERÁ CRIADO nos hooks de pre push, pois se você adicionar um remoto upstream você tem que alternar entre qual o PR será gerado.**

Aqui está a configuração do Alvo do Pull Request:

Se o seu repositório tiver um remote upstream configurado, o instalador fará uma pergunta depois que você usou o comando "codewise-init --all"
para definir o comportamento padrão do hook pre-push:

 Um remote 'upstream' foi detectado.
Qual deve ser o comportamento padrão do 'git push' para este repositório?
1: Criar Pull Request no 'origin' (seu fork)
2: Criar Pull Request no 'upstream' (projeto principal)
Escolha o padrão (1 ou 2):

Sua escolha será salva no hook, e você não precisará mais se preocupar com isso. Se não houver upstream, ele será configurado para origin por padrão.

Você verá uma mensagem de sucesso confirmando que a automação está ativa.

Com esse comando os arquivos de pre-commit e pre-push já terão sido adicionados ao seu hooks do repositório.

---

Tudo está funcionando agora no repositório que você configurou.
Caso queira instalar em um novo repositório basta repetir os passos.

# Usando o CodeWise 
Com a configuração concluída, você já tem acesso aos comandos **codewise-lint** e **codewise-pr** de forma manual e automatizada após instalar os hooks.

1.  **Adicione suas alterações**

    * Após modificar seus arquivos, adicione-os à "staging area":
    ```bash
    git add .
    ```
    * Aqui você já pode usar o comando `codewise-lint` para analisar os arquivos e você poder fazer ajustes antes de commitar.

2.  **Faça o commit**
    ```bash
    git commit -m "implementa novo recurso "
    ```
    * Neste momento, o **hook `pre-commit` será ativado**, e o `codewise-lint` fará a análise rápida no seu terminal.

3.  **Envie para o GitHub**
    ```bash
    git push
    ```
    * Agora, o **hook `pre-push` será ativado**. O `codewise-pr` vai perguntar para qual remote você quer enviar caso haja um upstream além do seu origin em seguida irá criar um novo/atualizar seu Pull Request com título, descrição e análise técnica gerados pela IA.