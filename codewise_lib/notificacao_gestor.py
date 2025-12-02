import os
import sys
import re
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


def enviar_telegram(mensagem: str) -> bool:
    """
    Envia uma mensagem via Telegram Bot API.
    
    Args:
        mensagem: Texto da mensagem que será enviada
        
    Returns:
        bool: True se enviado, False caso contrário
    """
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
    """
    Processa o arquivo de avaliação de código e envia notificação ao gestor.
    
    Args:
        caminho_arquivo: Caminho do arquivo de avaliação gerado
        email_dev: Email do desenvolvedor avaliado
        repo_path: Caminho do repositório Git
        
    Returns:
        bool: True se notificação for enviada com sucesso, False caso contrário
    """
    try:
        nota = 0.0
        justificativa_linhas = []
        capturando_breakdown = False
        
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            for linha in f:
                linha_clean = linha.strip()
                
                #varre o arquivo gerado procurando a nota final
                if 'nota final' in linha_clean.lower():
                    linha_limpa = re.sub(r'[*_#>`~]', '', linha_clean)
                    linha_limpa = linha_limpa.strip()
                    
                    #pega a nota
                    nota_match = re.search(r'(\d+\.?\d*)', linha_limpa)
                    if nota_match:
                        nota = float(nota_match.group(1))
                        print(f"   ✓ Nota encontrada: {nota}/10", file=sys.stderr)
                
                #varre o arquivo procurando o breakdown de pontos
                if 'breakdown de pontos' in linha_clean.lower():
                    capturando_breakdown = True
                    continue
                
                # Para de capturar quando encontrar "Justificativa detalhada"
                if capturando_breakdown and 'fim justificativa' in linha_clean.lower():
                    break
                
                if capturando_breakdown:
                    # Remove caracteres especiais
                    linha_limpa = re.sub(r'[*_#>`~]', '', linha_clean)
                    linha_limpa = linha_limpa.strip()
                    
                    if linha_limpa:
                        justificativa_linhas.append(linha_limpa)
        
        #justificativa final da nota
        justificativa = '\n'.join(justificativa_linhas)
        
        if len(justificativa) > 4000:
            justificativa = justificativa[:3997] + "..."
        
        if justificativa:
            print(f"   ✓ Justificativa extraída ({len(justificativa)} chars)", file=sys.stderr)
        else:
            print(f"   ⚠️  Justificativa não encontrada", file=sys.stderr)
            justificativa = "Avaliação concluída."
        
        #nome do repositório
        repo_nome = os.path.basename(repo_path)
        
        #visual para a nota
        emoji_nota = "🟢" if nota >= 8.5 else "🟡" if nota >= 7.0 else "🔴"
        
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
        
        #faz o envio pro telegram já formatado
        telegram_ok = enviar_telegram(mensagem)
        
        return telegram_ok
        
    except Exception as e:
        print(f"⚠️  Erro ao processar avaliação: {str(e)}", file=sys.stderr)
        return False
