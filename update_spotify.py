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

def get_recently_played(access_token, limit=4):
    try:
        response = requests.get(
            f"https://api.spotify.com/v1/me/player/recently-played?limit={limit}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        data = response.json()
        if "items" in data:
            return [item["track"] for item in data["items"]]
        return []
    except Exception as e:
        print(f"Erro ao obter histórico: {e}")
        return []

def generate_spotify_card(track, is_playing):
    if not track:
        return None

    artist = track["artists"][0]["name"]
    song = track["name"]
    image = track["album"]["images"][0]["url"]
    
    # Escapar caracteres XML especiais
    song = song.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    artist = artist.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    
    # Cor de fundo e texto
    bg_color = "#121212"
    text_color = "#FFFFFF"
    bar_color = "#1DB954" if is_playing else "#535353"
    
    # Base64 da imagem para embutir no SVG
    try:
        img_content = requests.get(image).content
        img_b64 = base64.b64encode(img_content).decode()
        img_src = f"data:image/jpeg;base64,{img_b64}"
    except:
        img_src = image # Fallback

    # Animação das barras (CSS)
    animation_styles = ""
    if is_playing:
        animation_styles = """
        <style>
            .bar { animation: bars 1.2s ease-in-out infinite; }
            @keyframes bars { 0%, 100% { height: 4px; } 50% { height: 14px; } }
            .bar1 { animation-delay: 0s; }
            .bar2 { animation-delay: 0.2s; }
            .bar3 { animation-delay: 0.4s; }
            .bar4 { animation-delay: 0.6s; }
            .bar5 { animation-delay: 0.8s; }
        </style>
        """
    
    bars_svg = f"""
    <g transform="translate(240, 85)">
        <rect class="bar bar1" x="0" y="0" width="3" height="10" fill="{bar_color}" rx="1" />
        <rect class="bar bar2" x="6" y="0" width="3" height="15" fill="{bar_color}" rx="1" />
        <rect class="bar bar3" x="12" y="0" width="3" height="8" fill="{bar_color}" rx="1" />
        <rect class="bar bar4" x="18" y="0" width="3" height="12" fill="{bar_color}" rx="1" />
        <rect class="bar bar5" x="24" y="0" width="3" height="6" fill="{bar_color}" rx="1" />
    </g>
    """

    status_text = 'Tocando agora' if is_playing else 'Última ouvida'

    svg = f"""
<svg width="400" height="120" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
    <rect x="0" y="0" width="400" height="120" rx="12" fill="{bg_color}" stroke="#282828" stroke-width="1"/>
    {animation_styles}
    
    <!-- Album Art -->
    <defs>
        <clipPath id="clip">
            <rect x="15" y="15" width="90" height="90" rx="6" />
        </clipPath>
    </defs>
    <image x="15" y="15" width="90" height="90" xlink:href="{img_src}" clip-path="url(#clip)" />

    <!-- Text Info -->
    <g transform="translate(120, 45)">
        <text x="0" y="0" font-family="'Segoe UI', Ubuntu, Sans-Serif" font-size="16" font-weight="bold" fill="{text_color}">{song[:30] + ('...' if len(song)>30 else '')}</text>
        <text x="0" y="25" font-family="'Segoe UI', Ubuntu, Sans-Serif" font-size="14" fill="#B3B3B3">{artist[:35]}</text>
    </g>

    <!-- Status & Bars -->
    <g transform="translate(120, 90)">
        <text x="0" y="5" font-family="'Segoe UI', Ubuntu, Sans-Serif" font-size="11" fill="{bar_color}" font-weight="bold">
            {status_text.upper()}
        </text>
    </g>
    {bars_svg}
</svg>
"""
    return svg.strip()

def update_readme(current_track, is_playing, recent_tracks):
    if not current_track:
        return

    # 1. Gerar e salvar SVG principal
    svg_content = generate_spotify_card(current_track, is_playing)
    if svg_content:
        with open("spotify_card.svg", "w", encoding="utf-8") as f:
            f.write(svg_content)

    # 2. Criar lista markdown das últimas ouvidas (apenas texto, compatível com GitHub)
    recent_html = ""
    if recent_tracks:
        recent_items = []
        for i, track in enumerate(recent_tracks[:4], 1):
            song = track["name"]
            artist = track["artists"][0]["name"]
            url = track["external_urls"]["spotify"]
            
            recent_items.append(f"{i}. 🎵 [{song}]({url}) - *{artist}*")
        
        recent_html = f"""

<details>
<summary>📼 Últimas Ouvidas</summary>

{chr(10).join(recent_items)}

</details>
"""

    # 3. Atualizar README
    new_content = f"""<!-- spotify_readme_start -->
<div align="center">
  <a href="{current_track['external_urls']['spotify']}">
    <img src="https://github.com/Clebio2030/Clebio2030/blob/main/spotify_card.svg" alt="Spotify Status" width="100%">
  </a>
  {recent_html}
</div>
<!-- spotify_readme_end -->"""

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

    try:
        token = get_access_token()
        if token:
            current_track, is_playing = get_current_track(token)
            recent_tracks = get_recently_played(token, limit=4)
            update_readme(current_track, is_playing, recent_tracks)
            print("Spotify card atualizado com histórico!")
        else:
            print("Erro ao obter token de acesso.")
    except Exception as e:
        print(f"Erro: {e}")
