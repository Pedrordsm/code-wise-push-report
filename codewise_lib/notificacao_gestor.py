import os
import sys
import re
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


def enviar_telegram(mensagem: str) -> bool:
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if not telegram_token or not telegram_chat_id:
        print("⚠️  TELEGRAM_BOT_TOKEN ou TELEGRAM_CHAT_ID não configurados no .env", file=sys.stderr)
        return False
    
    try:
        url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
        
        payload = {
            "chat_id": telegram_chat_id,
            "text": mensagem,
            "parse_mode": "Markdown"
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            print("✅ Notificação enviada via Telegram", file=sys.stderr)
            return True
        else:
            print(f"⚠️  Erro ao enviar Telegram: {response.status_code}", file=sys.stderr)
            return False
            
    except Exception as e:
        print(f"⚠️  Erro ao conectar com Telegram: {str(e)}", file=sys.stderr)
        return False


def processar_avaliacao_e_notificar(caminho_arquivo: str, email_dev: str, repo_path: str) -> bool:
    try:
        # Lê o arquivo linha por linha
        nota = 0.0
        justificativa_linhas = []
        capturando_breakdown = False
        
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            for linha in f:
                # Limpa a linha
                linha_clean = linha.strip()
                
                # Procura pela nota
                if 'nota final' in linha_clean.lower():
                    # Remove caracteres especiais
                    linha_limpa = re.sub(r'[*_#>`~]', '', linha_clean)
                    linha_limpa = linha_limpa.strip()
                    
                    # Extrai o número
                    nota_match = re.search(r'(\d+\.?\d*)', linha_limpa)
                    if nota_match:
                        nota = float(nota_match.group(1))
                        print(f"   ✓ Nota encontrada: {nota}/10", file=sys.stderr)
                
                # Procura pelo início do breakdown
                if 'breakdown de pontos' in linha_clean.lower():
                    capturando_breakdown = True
                    continue
                
                # Para de capturar quando encontrar "Justificativa detalhada"
                if capturando_breakdown and 'justificativa detalhada' in linha_clean.lower():
                    break
                
                # Captura linhas do breakdown até "Justificativa"
                if capturando_breakdown:
                    # Remove caracteres especiais
                    linha_limpa = re.sub(r'[*_#>`~]', '', linha_clean)
                    linha_limpa = linha_limpa.strip()
                    
                    if linha_limpa:
                        # Adiciona a linha com quebra de linha
                        justificativa_linhas.append(linha_limpa)
        
        # Monta a justificativa com quebras de linha
        justificativa = '\n'.join(justificativa_linhas)
        
        # Limita a 4000 caracteres para o Telegram
        if len(justificativa) > 4000:
            justificativa = justificativa[:3997] + "..."
        
        if justificativa:
            print(f"   ✓ Justificativa extraída ({len(justificativa)} chars)", file=sys.stderr)
        else:
            print(f"   ⚠️  Justificativa não encontrada", file=sys.stderr)
            justificativa = "Avaliação concluída."
        
        # Obtém nome do repositório
        repo_nome = os.path.basename(repo_path)
        
        # Prepara mensagem para Telegram
        # Nota é de 0 a 10, então ajusta os limites
        emoji_nota = "🟢" if nota >= 8.5 else "🟡" if nota >= 7.0 else "🔴"
        
        # Escapa caracteres especiais do Markdown
        justificativa_escaped = justificativa.replace('*', '\\*').replace('_', '\\_').replace('[', '\\[').replace('`', '\\`')
        
        mensagem = f"""
{emoji_nota} *Nova Avaliação de Código*

👤 *Desenvolvedor:* {email_dev}
📦 *Repositório:* {repo_nome}
📊 *Nota:* {nota}/10

📝 *Resumo:*
{justificativa_escaped}

📅 *Data:* {datetime.now().strftime("%d/%m/%Y %H:%M")}
"""
        
        # Envia notificação
        telegram_ok = enviar_telegram(mensagem)
        
        return telegram_ok
        
    except Exception as e:
        print(f"⚠️  Erro ao processar avaliação: {str(e)}", file=sys.stderr)
        return False
