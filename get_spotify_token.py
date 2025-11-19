import requests
import sys

# Configurar codificação para saída no terminal Windows
sys.stdout.reconfigure(encoding='utf-8')

# --- DADOS JÁ PREENCHIDOS ---
CLIENT_ID = "007fdedc6acc4adaa45ca119bdb6f1ba"
CLIENT_SECRET = "7d0f817e277a494bbf4d7a4b0a86bbbd"
CODE = "AQCVaCH95R_8QF228u8AO-WdnanOOpc6LzdeAd52u8qqULuu36fIQReH2pKLxiBjsqoAmx7qKStV5N_0Z8lfcGzupYfboZIk59I-t_F7hxF8racUVk8HTif0aY1B_urAnlTHW27KNT2-soXCYckSY0aM0Xg22S5s0scCUaaCeVebydmCPIKf693ALb9ADN9PUoZP-2tarWThMRwoMcOlvWSdHwZ76HbyiFq3Sd-xBA"
# ---------------------------

print(f"Tentando autenticar com código: {CODE[:15]}...")

url = "https://accounts.spotify.com/api/token"

payload = {
    "grant_type": "authorization_code",
    "code": CODE,
    # Atualizado para usar o redirect do Google conforme configurado
    "redirect_uri": "https://google.com/", 
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
}

try:
    response = requests.post(url, data=payload)
    data = response.json()

    if "refresh_token" in data:
        print("\n✅✅✅ SUCESSO ABSOLUTO! ✅✅✅\n")
        print("Aqui está seu REFRESH TOKEN (Guarde com sua vida):\n")
        print(data["refresh_token"])
        print("\n--------------------------------------------------")
        print("Agora vá no GitHub do seu projeto > Settings > Secrets > Actions")
        print("Crie os seguintes secrets:")
        print(f"SPOTIFY_CLIENT_ID: {CLIENT_ID}")
        print(f"SPOTIFY_CLIENT_SECRET: {CLIENT_SECRET}")
        print(f"SPOTIFY_REFRESH_TOKEN: {data['refresh_token']}")
        print("--------------------------------------------------")
    else:
        print("\n❌ ERRO AO OBTER TOKEN:", data)
except Exception as e:
    print("\n❌ Erro na requisição:", e)
