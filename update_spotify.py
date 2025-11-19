import os
import base64
import requests
import re

# Configurações
CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")
REFRESH_TOKEN = os.environ.get("SPOTIFY_REFRESH_TOKEN")

def get_access_token():
    auth_header = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
    response = requests.post(
        "https://accounts.spotify.com/api/token",
        data={"grant_type": "refresh_token", "refresh_token": REFRESH_TOKEN},
        headers={"Authorization": f"Basic {auth_header}"},
    )
    return response.json().get("access_token")

def get_current_track(access_token):
    # Tenta pegar o que está tocando agora
    response = requests.get(
        "https://api.spotify.com/v1/me/player/currently-playing",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    
    if response.status_code == 204 or not response.text:
        # Se não estiver tocando nada, pega a última tocada
        response = requests.get(
            "https://api.spotify.com/v1/me/player/recently-played?limit=1",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        data = response.json()
        if "items" in data and len(data["items"]) > 0:
            track = data["items"][0]["track"]
            return track, False # False = não está tocando agora (é histórico)
        return None, None

    data = response.json()
    if "item" in data and data["item"]:
        return data["item"], data["is_playing"]
    return None, None

def update_readme(track, is_playing):
    if not track:
        return

    artist = track["artists"][0]["name"]
    song = track["name"]
    url = track["external_urls"]["spotify"]
    image = track["album"]["images"][0]["url"]
    
    status_text = "🎶 Ouvindo agora:" if is_playing else "⏮️ Última ouvida:"
    
    # HTML para inserir no README
    new_content = f"""
<!-- spotify_readme_start -->
<div align="center">
  <h3>{status_text}</h3>
  <a href="{url}">
    <img src="{image}" width="250" style="border-radius: 10px; box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);" alt="{song}">
  </a>
  <br/>
  <p><b>{song}</b> - {artist}</p>
</div>
<!-- spotify_readme_end -->
"""

    with open("README.md", "r", encoding="utf-8") as f:
        readme = f.read()

    # Substitui o conteúdo entre as tags
    new_readme = re.sub(
        r"<!-- spotify_readme_start -->.*<!-- spotify_readme_end -->",
        new_content.strip(),
        readme,
        flags=re.DOTALL
    )

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(new_readme)

if __name__ == "__main__":
    if not CLIENT_ID or not CLIENT_SECRET or not REFRESH_TOKEN:
        print("Erro: Variáveis de ambiente não configuradas.")
        exit(1)

    try:
        token = get_access_token()
        if token:
            track, is_playing = get_current_track(token)
            update_readme(track, is_playing)
            print("README atualizado com sucesso!")
        else:
            print("Erro ao obter token de acesso.")
    except Exception as e:
        print(f"Erro: {e}")

