# 🧠 **CodeWise**

> **Ferramenta instalável via `pip` que usa IA para analisar o código e automatizar a documentação de Pull Requests através de hooks do Git.**

---

## 🚀 **Funcionalidades Principais**

- 🏷️ **Geração de Título:** Cria títulos de PR claros e concisos seguindo o padrão *Conventional Commits*.  
- 📝 **Geração de Descrição:** Escreve descrições detalhadas baseadas nas alterações do código.  
- 🧩 **Análise Técnica:** Posta um comentário no PR com um resumo executivo de melhorias de arquitetura, aderência a princípios S.O.L.I.D. e outros pontos de qualidade.  
- 🔁 **Automação com Hooks:** Integra-se ao seu fluxo de trabalho Git para rodar automaticamente a cada `git commit` e `git push`.  
- 🤖 **Flexibilidade de IA:** Escolha qual provedor de IA usar (`Cohere`, `Google Gemini`, `Groq`, `OpenAI`) através de uma simples configuração.  
- 🔒 **Verificação de Privacidade (LGPD):** Analisa automaticamente a política de coleta de dados do provedor de IA antes de enviar o seu código.

---

## ⚙️ **Guia de Instalação**

Siga os passos abaixo para instalar e configurar o **CodeWise** em qualquer repositório.

---

### 🧩 **Passo 1 — Pré-requisitos**

Antes de começar, garanta que você tenha instaladas as seguintes ferramentas:

1. **Python** (versão 3.11 ou superior)  
2. **Git**  
3. **GitHub CLI (`gh`)**

> Após instalar a CLI do GitHub ([https://cli.github.com](https://cli.github.com)), execute:
> ```bash
> gh auth login
> ```
> Faça login na sua conta — este passo é necessário apenas uma vez por computador.

---

### 🧱 **Passo 2 — Configurando Seu Repositório**

> O ideal é sempre criar um **ambiente virtual na pasta raiz** do novo repositório para evitar conflitos de dependências.

---

#### 🔹 2.1 Criar e Ativar o Ambiente Virtual

**Crie o ambiente virtual** (dentro da raiz do repositório onde está a pasta `.git`):

```bash
# Windows
py -m venv .venv

# Linux/WSL
python3 -m venv .venv
```

> 💡 O nome `.venv` é apenas uma convenção — você pode usar outro nome se quiser.

**Ative o ambiente:**

```bash
# Windows (PowerShell)
.\.venv\Scripts\activate

# Linux/WSL
source .venv/bin/activate
```

> ⚠️ Se ocorrer erro de política de execução no PowerShell, rode:
> ```bash
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

Você saberá que funcionou quando o nome `(.venv)` aparecer no início da linha do terminal.

---

#### 🔹 2.2 Instalar a Ferramenta CodeWise

Com o ambiente virtual ativo, instale o pacote:

```bash
pip install codewise-lib
```

> ⏳ A primeira instalação pode demorar um pouco.  
> Após concluir, confirme se está tudo certo com:
> ```bash
> codewise-help
> ```

---

#### 🔹 2.3 Configurar a Chave da API (`.env`)

Para que a IA funcione, configure suas chaves de API e o provedor desejado.

1. **Na raiz do projeto**, crie um arquivo `.env`:

```bash
# Windows
notepad .env

# Linux/WSL
touch .env && nano .env
```

2. **Adicione o conteúdo abaixo e insira suas chaves:**

```ini
# 1. ESCOLHA O PROVEDOR DE IA
# Opções disponíveis: "COHERE", "GROQ", "GEMINI", "OPENAI"
AI_PROVIDER="GEMINI"  # -> maiúsculo!!!

# 2. ESCOLHA O MODELO ESPECÍFICO
# Ex.: "gemini-2.0-flash", "gpt-4o-mini"
AI_MODEL=gemini-2.0-flash  # -> *sem* aspas

# 3. COLOQUE SUA(S) CHAVE(S) DE API
# A ferramenta usará a chave correta com base no AI_PROVIDER
COHERE_API_KEY=sua_chave_cohere_api_aqui
GROQ_API_KEY=sua_chave_groq_api_aqui
GEMINI_API_KEY=sua_chave_gemini_api_aqui
OPENAI_API_KEY=sua_chave_openai_api_aqui
```

> ⚠️ **Importante:**  
> Adicione o arquivo `.env` ao `.gitignore` para evitar expor suas chaves secretas no GitHub.

---

### 🔸 **Nota Importante sobre Remotes**

A ferramenta CodeWise espera que seus remotes sigam a convenção padrão do GitHub:

- **origin** → aponta para o **seu fork pessoal** do repositório  
- **upstream** → (opcional) aponta para o **repositório principal**

> 🧠 Dica:  
> Se o repositório for novo, execute um push inicial com:
> ```bash
> git push --no-verify
> ```
> Isso garante que o `gh` funcione corretamente na criação dos Pull Requests.

---

#### 🔹 2.4 Ativar a Automação no Repositório

Na raiz do projeto (onde está a pasta `.git`), execute **uma única vez**:

```bash
codewise-init --all
```

Esse comando adicionará automaticamente os hooks `pre-commit` e `pre-push`.

Se o seu repositório tiver um `upstream`, o instalador perguntará:

```
Um remote 'upstream' foi detectado.
Qual deve ser o comportamento padrão do 'git push'?
1: Criar Pull Request no 'origin' (seu fork)
2: Criar Pull Request no 'upstream' (projeto principal)
Escolha o padrão (1 ou 2):
```

> Sua escolha será salva no hook — não será necessário configurá-la novamente.  
> Se não houver `upstream`, o padrão será `origin`.

---

## 🧰 **Usando o CodeWise**

Com tudo configurado, você pode usar os comandos **`codewise-lint`** e **`codewise-pr`** manualmente ou automaticamente pelos hooks.

---

### 🔸 **Fluxo de Uso**

#### 1️⃣ Adicione suas alterações
```bash
git add .
```
> 💡 Use `codewise-lint` antes do commit para revisar seu código.

---

#### 2️⃣ Faça o commit
```bash
git commit -m "implementa novo recurso"
```
> O **hook `pre-commit`** será ativado e executará o `codewise-lint` automaticamente.

---

#### 3️⃣ Envie para o GitHub
```bash
git push
```
> O **hook `pre-push`** ativará o `codewise-pr`, que:
> - Perguntará para qual remote enviar (caso exista um `upstream`);
> - Criará ou atualizará o Pull Request com **título, descrição e análise técnica** gerados pela IA.

---

## 🛡️ **Verificação de Privacidade e LGPD**

Antes de qualquer envio de código, o `codewise-lib` realiza uma **verificação de privacidade automática**.  
O objetivo é garantir que o provedor de IA configurado no `.env` possua políticas compatíveis com a **LGPD**, assegurando a proteção dos seus dados e da sua base de código.

---

## 🏗️ **Arquitetura do Sistema**

O CodeWise segue o padrão **MVC (Model-View-Controller)** para garantir separação de responsabilidades, manutenibilidade e extensibilidade.

### 📐 **Visão Geral da Arquitetura**

```
┌─────────────────────────────────────────────────────────────┐
│                        Entry Point                          │
│                    (main.py - CLI)                          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Controller Layer                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  CodewiseController                                   │  │
│  │  - Roteamento de comandos                            │  │
│  │  - Orquestração de workflows                         │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      Model Layer                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  GitService          │  LLMFactory                   │  │
│  │  - Operações Git     │  - Criação de provedores IA   │  │
│  ├──────────────────────┼───────────────────────────────┤  │
│  │  CrewOrchestrator    │  LGPDService                  │  │
│  │  - Gerencia agentes  │  - Verificação de privacidade │  │
│  ├──────────────────────┼───────────────────────────────┤  │
│  │  AnalysisModels      │  NotificationService          │  │
│  │  - Estruturas dados  │  - Notificações de scores     │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                       View Layer                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  OutputFormatter     │  FileWriter                   │  │
│  │  - Formatação        │  - Operações de arquivo       │  │
│  ├──────────────────────┼───────────────────────────────┤  │
│  │  ConsoleView         │  NotificationFormatter        │  │
│  │  - Saída terminal    │  - Formatação notificações    │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 📁 **Estrutura de Diretórios**

```
codewise_lib/
├── __init__.py
├── main.py                          # Ponto de entrada
├── controllers/
│   ├── __init__.py
│   └── codewise_controller.py       # Controlador principal
├── models/
│   ├── __init__.py
│   ├── exceptions.py                # Hierarquia de exceções
│   ├── analysis_models.py           # Estruturas de dados
│   ├── git_service.py               # Operações Git
│   ├── llm_factory.py               # Factory de provedores IA
│   ├── crew_orchestrator.py         # Orquestração de agentes
│   ├── lgpd_service.py              # Verificação LGPD
│   └── notification_service.py      # Serviço de notificações
├── views/
│   ├── __init__.py
│   ├── output_formatter.py          # Formatação de resultados
│   ├── file_writer.py               # Escrita de arquivos
│   ├── console_view.py              # Saída no console
│   └── notification_formatter.py    # Formatação de notificações
├── config/
│   ├── agents.yaml                  # Configuração de agentes
│   └── tasks.yaml                   # Configuração de tarefas
└── tools/
    ├── __init__.py
    ├── custom_git_tools.py          # Ferramentas Git customizadas
    └── score_tool.py                # Ferramenta de pontuação
```

### 🔧 **Componentes Principais**

#### **Model Layer (Camada de Modelo)**
- **GitService**: Encapsula todas as operações Git (fetch, diff, log, blame)
- **LLMFactory**: Padrão Factory para criar instâncias de provedores IA
- **CrewOrchestrator**: Gerencia crews de agentes IA e execução de tarefas
- **LGPDService**: Verifica conformidade LGPD com cache de resultados
- **NotificationService**: Envia notificações de performance via email/Slack/webhooks
- **AnalysisModels**: Estruturas de dados (AnalysisResult, PerformanceScore, etc.)

#### **View Layer (Camada de Visualização)**
- **OutputFormatter**: Formata resultados de análise como markdown
- **FileWriter**: Gerencia operações de I/O de arquivos com tratamento de erros
- **ConsoleView**: Gerencia saída no terminal com cores e formatação
- **NotificationFormatter**: Formata notificações para diferentes canais

#### **Controller Layer (Camada de Controle)**
- **CodewiseController**: Orquestra todas as operações, roteia comandos e coordena Models e Views

### 🎯 **Tratamento de Erros**

O sistema implementa uma hierarquia de exceções customizadas:

- `CodewiseError`: Exceção base para todos os erros
- `GitOperationError`: Erros em operações Git
- `ConfigurationError`: Erros de configuração
- `FileOperationError`: Erros em operações de arquivo
- `ValidationError`: Erros de validação de entrada
- `LGPDComplianceError`: Erros de conformidade LGPD
- `NotificationError`: Erros em entrega de notificações

Todas as exceções incluem informações contextuais detalhadas para facilitar a depuração.

### 🔌 **Extensibilidade**

A arquitetura MVC facilita extensões futuras:

1. **Novos Provedores IA**: Adicione ao `LLMFactory`
2. **Novos Formatos de Saída**: Estenda `OutputFormatter`
3. **Novos Canais de Notificação**: Estenda `NotificationService`
4. **Interface Web**: Adicione views web sem alterar models ou controllers
5. **API REST**: Exponha funcionalidade via API usando controllers existentes


### ✅ **Tudo pronto!**
Seu repositório já está com o CodeWise ativo.  
Para usar em outro repositório, basta repetir os passos acima.

---

## 🤝 **Contribuindo**

Contribuições são bem-vindas! A arquitetura MVC facilita a adição de novos recursos:

1. **Models**: Adicione nova lógica de negócio em `models/`
2. **Views**: Adicione novos formatadores em `views/`
3. **Controllers**: Estenda o `CodewiseController` para novos modos

Consulte a documentação inline (docstrings no estilo Google) para detalhes de implementação.
