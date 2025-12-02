# CodeWise

Ferramenta instalavel via `pip` que utiliza IA para analisar codigo e automatizar a documentacao de Pull Requests atraves de hooks do Git.

---

## Funcionalidades

- **Geracao de Titulo:** Cria titulos de PR claros e concisos seguindo o padrao Conventional Commits.
- **Geracao de Descricao:** Escreve descricoes detalhadas baseadas nas alteracoes do codigo.
- **Analise Tecnica:** Posta um comentario no PR com resumo executivo de melhorias de arquitetura, aderencia a principios S.O.L.I.D. e outros pontos de qualidade.
- **Automacao com Hooks:** Integra-se ao fluxo de trabalho Git para rodar automaticamente a cada `git commit` e `git push`.
- **Flexibilidade de IA:** Escolha qual provedor de IA usar (`Cohere`, `Google Gemini`, `Groq`, `OpenAI`) atraves de configuracao.
- **Verificacao de Privacidade (LGPD):** Analisa automaticamente a politica de coleta de dados do provedor de IA antes de enviar o codigo.
- **Avaliacao de Codigo:** Gera relatorios de avaliacao com nota e justificativa detalhada.
- **Notificacao via Telegram:** Envia avaliacoes automaticamente para gestores via Telegram Bot API.

---

## Pre-requisitos

Antes de comecar, garanta que voce tenha instaladas as seguintes ferramentas:

1. **Python** (versao 3.11 ou superior)
2. **Git**
3. **GitHub CLI (`gh`)**

Apos instalar a CLI do GitHub (https://cli.github.com), execute:

```bash
gh auth login
```

Faca login na sua conta. Este passo e necessario apenas uma vez por computador.

---

## Instalacao

### 1. Criar e Ativar o Ambiente Virtual

Crie o ambiente virtual na raiz do repositorio onde esta a pasta `.git`:

```bash
# Windows
py -m venv .venv

# Linux/WSL
python3 -m venv .venv
```

Ative o ambiente:

```bash
# Windows (PowerShell)
.\.venv\Scripts\activate

# Linux/WSL
source .venv/bin/activate
```

Se ocorrer erro de politica de execucao no PowerShell, rode:

```bash
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 2. Instalar o CodeWise

Com o ambiente virtual ativo, instale o pacote:

```bash
pip install codewise-lib
```

Apos concluir, confirme se esta tudo certo com:

```bash
codewise-help
```

---

## Configuracao do Arquivo .env

Na raiz do projeto, crie um arquivo `.env` com as seguintes variaveis:

```ini
# PROVEDOR DE IA
# Opcoes disponiveis: "COHERE", "GROQ", "GEMINI", "OPENAI"
AI_PROVIDER="GEMINI"

# MODELO ESPECIFICO
# Exemplos: "gemini-2.0-flash", "gpt-4o-mini", "command-r-plus", "llama-3.1-70b-versatile"
AI_MODEL=gemini-2.0-flash

# CHAVES DE API DOS PROVEDORES
# Configure a chave correspondente ao AI_PROVIDER escolhido
COHERE_API_KEY=sua_chave_cohere_aqui
GROQ_API_KEY=sua_chave_groq_aqui
GEMINI_API_KEY=sua_chave_gemini_aqui
OPENAI_API_KEY=sua_chave_openai_aqui

# TELEGRAM (opcional - para notificacoes de avaliacao)
TELEGRAM_BOT_TOKEN=seu_token_do_bot_telegram
TELEGRAM_CHAT_ID=seu_chat_id_telegram
```

**Importante:** Adicione o arquivo `.env` ao `.gitignore` para evitar expor suas chaves secretas.

---

## Chave OpenAI para Embedding (Obrigatorio)

O CodeWise utiliza o CrewAI com ferramentas que dependem de embedding para busca semantica. Por isso, **a chave `OPENAI_API_KEY` e obrigatoria** no arquivo `.env`, mesmo que voce utilize outro provedor de IA (Gemini, Groq, Cohere) como modelo principal.

A OpenAI e utilizada internamente pelo CrewAI Tools para realizar operacoes de embedding. Sem essa chave configurada, as ferramentas de analise nao funcionarao corretamente.

---

## Configuracao do Telegram (Opcional)

Para receber notificacoes de avaliacao de codigo via Telegram:

1. **Criar um Bot no Telegram:**
   - Abra o Telegram e busque por `@BotFather`
   - Envie o comando `/newbot` e siga as instrucoes
   - Copie o token gerado para `TELEGRAM_BOT_TOKEN`

2. **Obter o Chat ID:**
   - Inicie uma conversa com seu bot
   - Acesse `https://api.telegram.org/bot<SEU_TOKEN>/getUpdates`
   - Localize o campo `chat.id` na resposta JSON
   - Copie o valor para `TELEGRAM_CHAT_ID`

3. **Adicionar ao .env:**

```ini
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=987654321
```

As notificacoes incluem: desenvolvedor avaliado, repositorio, nota, resumo da avaliacao e data.

---

## Ativar a Automacao no Repositorio

Na raiz do projeto (onde esta a pasta `.git`), execute uma unica vez:

```bash
codewise-init --all
```

Esse comando adicionara automaticamente os hooks `pre-commit` e `pre-push`.

Se o seu repositorio tiver um `upstream`, o instalador perguntara qual deve ser o comportamento padrao do `git push` para criacao de Pull Requests.

---

## Comandos Disponiveis

| Comando | Descricao |
|---------|-----------|
| `codewise-init --all` | Instala os hooks pre-commit e pre-push |
| `codewise-init --commit` | Instala apenas o hook pre-commit |
| `codewise-init --push` | Instala apenas o hook pre-push |
| `codewise-pr` | Analisa commits e cria/atualiza PR com IA |
| `codewise-pr-origin` | Cria PR no remote origin |
| `codewise-pr-upstream` | Cria PR no remote upstream |
| `codewise-lint` | Analisa arquivos staged antes do commit |
| `codewise-help` | Exibe ajuda e comandos disponiveis |

---

## Fluxo de Uso

1. **Adicione suas alteracoes:**

```bash
git add .
```

2. **Faca o commit:**

```bash
git commit -m "implementa novo recurso"
```

O hook `pre-commit` sera ativado e executara o `codewise-lint` automaticamente.

3. **Envie para o GitHub:**

```bash
git push
```

O hook `pre-push` ativara o `codewise-pr`, que criara ou atualizara o Pull Request com titulo, descricao e analise tecnica gerados pela IA.

---

## Nota sobre Remotes

A ferramenta CodeWise espera que seus remotes sigam a convencao padrao do GitHub:

- **origin:** aponta para o seu fork pessoal do repositorio
- **upstream:** (opcional) aponta para o repositorio principal

Se o repositorio for novo, execute um push inicial com:

```bash
git push --no-verify
```

Isso garante que o `gh` funcione corretamente na criacao dos Pull Requests.

---

## Verificacao de Privacidade e LGPD

Antes de qualquer envio de codigo, o CodeWise realiza uma verificacao de privacidade automatica. O objetivo e garantir que o provedor de IA configurado no `.env` possua politicas compativeis com a LGPD, assegurando a protecao dos seus dados e da sua base de codigo.

---

## Dependencias

- crewai >= 0.201.1
- crewai-tools >= 0.76.0
- python-dotenv >= 1.1.1
- PyYAML >= 6.0.3
- litellm >= 1.74.9
- qdrant-client >= 1.15.1
- requests >= 2.32.3

---

✅ Tudo pronto!

Seu repositório já está com o CodeWise ativo.
Para usar em outro repositório, basta repetir os passos acima.
