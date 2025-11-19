import os
import base64
import requests
import re

# Configurações
CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")
REFRESH_TOKEN = os.environ.get("SPOTIFY_REFRESH_TOKEN")

def get_access_token():
    try:
        auth_header = base64.b64encode(f"{CLIENT_ID}:{CLIENT_SECRET}".encode()).decode()
        response = requests.post(
            "https://accounts.spotify.com/api/token",
            data={"grant_type": "refresh_token", "refresh_token": REFRESH_TOKEN},
            headers={"Authorization": f"Basic {auth_header}"},
        )
        return response.json().get("access_token")
    except Exception as e:
        print(f"Erro ao obter token: {e}")
        return None

def get_current_track(access_token):
    try:
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
                return track, False
            return None, None

        data = response.json()
        if "item" in data and data["item"]:
            return data["item"], data["is_playing"]
        return None, None
    except Exception as e:
        print(f"Erro ao obter música: {e}")
        return None, None

def generate_spotify_card(track, is_playing):
    if not track:
        return None

    artist = track["artists"][0]["name"]
    song = track["name"]
    image = track["album"]["images"][0]["url"]
    
    # Cor de fundo e texto
    bg_color = "#121212"
    text_color = "#FFFFFF"
    bar_color = "#1DB954" if is_playing else "#535353"
    
    # Base64 da imagem para embutir no SVG
    try:
        img_data = base64.b64encode(requests.get(image).content).decode()
        img_src = f"data:image/jpeg;base64,{img_data}"
    except:
        img_src = image # Fallback para URL se falhar

    # Animação das barras
    animation = """
    <style>
        .bar { animation: bars 1.2s ease-in-out infinite; }
        @keyframes bars { 0%, 100% { height: 4px; } 50% { height: 14px; } }
        .bar1 { animation-delay: 0s; }
        .bar2 { animation-delay: 0.2s; }
        .bar3 { animation-delay: 0.4s; }
        .bar4 { animation-delay: 0.6s; }
        .bar5 { animation-delay: 0.8s; }
    </style>
    """ if is_playing else ""
    
    bars_svg = f"""
    <g transform="translate(240, 90)">
        <rect class="bar bar1" x="0" y="0" width="3" height="10" fill="{bar_color}" rx="1" />
        <rect class="bar bar2" x="6" y="0" width="3" height="15" fill="{bar_color}" rx="1" />
        <rect class="bar bar3" x="12" y="0" width="3" height="8" fill="{bar_color}" rx="1" />
        <rect class="bar bar4" x="18" y="0" width="3" height="12" fill="{bar_color}" rx="1" />
        <rect class="bar bar5" x="24" y="0" width="3" height="6" fill="{bar_color}" rx="1" />
    </g>
    """

    svg = f"""
<svg width="400" height="120" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
    <rect x="0" y="0" width="400" height="120" rx="12" fill="{bg_color}" stroke="#282828" stroke-width="1"/>
    {animation}
    
    <!-- Album Art -->
    <image x="10" y="10" width="100" height="100" xlink:href="{img_src}" clip-path="url(#clip)" />
    <defs>
        <clipPath id="clip">
            <rect x="10" y="10" width="100" height="100" rx="6" />
        </clipPath>
    </defs>

    <!-- Text Info -->
    <g transform="translate(130, 40)">
        <text x="0" y="0" font-family="Arial, Helvetica, sans-serif" font-size="16" font-weight="bold" fill="{text_color}">{song[:30] + ('...' if len(song)>30 else '')}</text>
        <text x="0" y="25" font-family="Arial, Helvetica, sans-serif" font-size="14" fill="#B3B3B3">{artist[:35]}</text>
    </g>

    <!-- Status Icon/Bars -->
    <g transform="translate(130, 85)">
        <text x="0" y="10" font-family="Arial, Helvetica, sans-serif" font-size="12" fill="{bar_color}">
            {'Tocando agora' if is_playing else 'Última ouvida'}
        </text>
    </g>
    {bars_svg}
    
    <!-- Spotify Logo -->
    <image x="360" y="10" width="30" height="30" xlink:href="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAADAAAAAwBAMAAAClDwvFAAAAG1BMVEUAAAD///8AZv8Aqv8AlP8Aqv8AgP8Anf8Amf9r0JECAAAACHRSTlMA///w///w//8A9wV5AAAAhUlEQVQ4y6XToQ2AMAyF4f+jE3AAlQSwABWjwQIsQJ102S8Bgu/iYsmS9T2frH/qeS9B90eC7o8E3R8Juj8S9PsiQc83CXo/E/T8JOj5S9DzlyR+3tcX2QAAAABJRU5ErkJggg==" />
</svg>
"""
    return svg

def update_readme(track, is_playing):
    if not track:
        return

    svg_content = generate_spotify_card(track, is_playing)
    if not svg_content:
        return

    # Salva o SVG
    with open("spotify_card.svg", "w", encoding="utf-8") as f:
        f.write(svg_content)
        
    # Atualiza o README apenas para apontar para a imagem
    new_content = """
<!-- spotify_readme_start -->
<div align="center">
  <a href="{url}">
    <img src="https://github.com/Clebio2030/Clebio2030/blob/main/spotify_card.svg" alt="Spotify Status" width="400">
  </a>
</div>
<!-- spotify_readme_end -->
""".format(url=track["external_urls"]["spotify"])

    with open("README.md", "r", encoding="utf-8") as f:
        readme = f.read()

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

    token = get_access_token()
    if token:
        track, is_playing = get_current_track(token)
        update_readme(track, is_playing)
        print("Spotify card atualizado!")
