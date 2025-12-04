import os
import discord
from discord.ext import commands
import asyncio
from unittest.mock import patch
from pathlib import Path
import requests
import re
import base64
import io

# Import do Reportify
from reportify import Report

# === Variáveis de Ambiente ===
TOKEN = os.getenv("MY_API_REPORTFY")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID"))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Bot
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# 📨 Função para enviar mensagens no canal e no privado
async def enviar_status(bot, channel_id, mensagem):
    # Mandar no canal do servidor
    canal = bot.get_channel(channel_id)
    if canal:
        await canal.send(mensagem)

    # Mandar no privado para usuários configurados
    usuarios_str = os.getenv("DISCORD_TARGET_USERS", "")
    if usuarios_str.strip():
        ids = [u.strip() for u in usuarios_str.split(",") if u.strip().isdigit()]
        for user_id in ids:
            try:
                user = await bot.fetch_user(int(user_id))
                await user.send(mensagem)
            except Exception as e:
                print(f"Erro ao enviar DM para {user_id}: {e}")

# 📄 Ler último relatório MD
def ler_ultimo_arquivo_md():
    reports_path = Path("./Reports")
    if not reports_path.exists() or not reports_path.is_dir():
        return None

    report_dirs = sorted(
        [p for p in reports_path.iterdir() if p.is_dir()],
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )

    if not report_dirs:
        return None

    latest_dir = report_dirs[0]
    md_files = list(latest_dir.glob("developer_stats_*.md"))
    if not md_files:
        return None

    contents = []
    for md_file in md_files:
        try:
            with open(md_file, "r", encoding="utf-8") as f:
                contents.append(f"## {md_file.stem}\n\n{f.read()}\n")
        except Exception as e:
            print(f"Erro ao ler {md_file}: {e}")

    return "\n".join(contents) if contents else None



# Enviar imagens base64 do Relatório
async def mandar_imagens_b64(destino, list_b64):
    await destino.send(
        "📊 Enviando gráficos do relatório...\n"
        "• Gráfico 1: Barras — Prometido vs Entregue\n"
        "• Gráfico 2: Linhas — Issues fechadas nos últimos 15 dias"
    )

    for i, img64 in enumerate(list_b64):
        try:
            img_bytes = base64.b64decode(img64)
            buf = io.BytesIO(img_bytes)

            arquivo = discord.File(
                fp=buf,
                filename=f"grafico_{i+1}.png"
            )

            await destino.send(f"📈 Gráfico {i+1}/{len(list_b64)}:", file=arquivo)

        except Exception as e:
            print(f"Erro ao enviar gráfico {i+1}: {e}")

# 🤖 GEMINI (Uso da Api)
def gerar_resposta_gemini(pergunta):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{"parts": [{"text": pergunta}]}]
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        try:
            return response.json()['candidates'][0]['content']['parts'][0]['text']
        except Exception:
            return "⚠️ Não consegui entender a resposta da IA."
    else:
        print(response.text)
        return f"❌ Erro na API: {response.status_code}"



# 🚀 Fluxo principal
@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")

    await enviar_status(bot, CHANNEL_ID, "🚀 Iniciando geração de relatório...")

    try:
        # 1️⃣ Gera relatório
        def run_report():
            entradas = ['0', '']
            with patch('builtins.input', side_effect=lambda _: entradas.pop(0) if entradas else ''):
                relatorio = Report()
                try:
                    relatorio.run()
                except SystemExit:
                    pass
                except Exception as e:
                    print(f"Erro no Reportify.run(): {e}")

        await asyncio.to_thread(run_report)
        await enviar_status(bot, CHANNEL_ID, "📊 Relatório gerado com sucesso!")


        # 2️⃣ Ler o MD
        markdown = ler_ultimo_arquivo_md()
        if not markdown:
            await enviar_status(bot, CHANNEL_ID, "⚠️ Nenhum relatório encontrado.")
            await bot.close()
            return

        # ---------- EXTRAIR IMAGENS BASE64 ----------
        regex_base64 = r"data:image/png;base64,([^)\s]+)"
        imgs_b64 = re.findall(regex_base64, markdown)

        if imgs_b64:
            # Mandar para o canal
            canal = bot.get_channel(CHANNEL_ID)
            if canal:
                await mandar_imagens_b64(canal, imgs_b64)

            # Mandar para os usuários privados
            usuarios_str = os.getenv("DISCORD_TARGET_USERS", "")
            ids = [u.strip() for u in usuarios_str.split(",") if u.strip().isdigit()]
            for user_id in ids:
                try:
                    user = await bot.fetch_user(int(user_id))
                    await mandar_imagens_b64(user, imgs_b64)
                except Exception as e:
                    print(f"Erro ao enviar imagens para {user_id}: {e}")

        # 3️⃣ Gerar resumo
        prompt = (
             "Você receberá estatísticas individuais de desenvolvedores de um projeto. "
            "Para cada desenvolvedor, gere um resumo separado (em Portugues-BR) contendo:\n"
            "- Prometido vs. Realizado (se disponível)\n"
            "- Throughput (quantas issues fechadas)\n"
            "- O nome dentro de uma [] no relatorio, para destacar\n"
            "- Quais issues ele abriu ou está responsável\n"
            "- Observações sobre atividade, papel no projeto ou padrão de contribuição\n\n"
            "Aqui estão os dados:\n\n" + markdown
        )

        await enviar_status(bot, CHANNEL_ID, "📝 Gerando resumo com a IA Gemini...")
        resumo = gerar_resposta_gemini(prompt)


        # 4️⃣ Enviar resumo
        for i in range(0, len(resumo), 2000):
            await enviar_status(bot, CHANNEL_ID, resumo[i:i+2000])

        await enviar_status(bot, CHANNEL_ID, "✅ Processo concluído com sucesso!")

    except Exception as e:
        await enviar_status(bot, CHANNEL_ID, f"❌ Erro durante execução: {e}")

    finally:
        await bot.close()


# Executar bot
bot.run(TOKEN)
