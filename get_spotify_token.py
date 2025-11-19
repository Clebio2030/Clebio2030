import requests

# --- PREENCHA ESTES DADOS ---
CLIENT_ID = "007fdedc6acc4adaa45ca119bdb6f1ba"
CLIENT_SECRET = "COLE_SEU_CLIENT_SECRET_AQUI"
CODE = "COLE_O_CODIGO_DA_URL_AQUI"
# ---------------------------

url = "https://accounts.spotify.com/api/token"

payload = {
    "grant_type": "authorization_code",
    "code": CODE,
    "redirect_uri": "http://localhost",
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
}

try:
    response = requests.post(url, data=payload)
    data = response.json()

    if "refresh_token" in data:
        print("\n✅ SUCESSO! Aqui está seu Refresh Token para colocar no GitHub:\n")
        print(data["refresh_token"])
        print("\n(Copie o código acima e coloque no secret SPOTIFY_REFRESH_TOKEN)")
    else:
        print("\n❌ ERRO:", data)
except Exception as e:
    print("\n❌ Erro na requisição:", e)

