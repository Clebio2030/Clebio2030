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
        response = requests.get(
            "https://api.spotify.com/v1/me/player/currently-playing",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        
        if response.status_code == 204 or not response.text:
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
            "https://api.spotify.com/v1/me/player/recently-played?limit={limit}",
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
    """Versão 3: Estilo Glassmorphism"""
    if not track:
        return None

    artist = track["artists"][0]["name"]
    song = track["name"]
    image = track["album"]["images"][0]["url"]
    
    song = song.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    artist = artist.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    
    try:
        img_content = requests.get(image).content
        img_b64 = base64.b64encode(img_content).decode()
        img_src = f"data:image/jpeg;base64,{img_b64}"
    except:
        img_src = image

    glow = ""
    if is_playing:
        glow = """
        <style>
            .glow { animation: glow 2s ease-in-out infinite; }
            @keyframes glow { 0%, 100% { filter: drop-shadow(0 0 5px #1DB954); } 
                             50% { filter: drop-shadow(0 0 15px #1DB954); } }
        </style>
        """

    svg = f"""
<svg width="450" height="150" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
    <defs>
        <linearGradient id="grad2" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#1ed760;stop-opacity:0.4" />
            <stop offset="50%" style="stop-color:#1DB954;stop-opacity:0.6" />
            <stop offset="100%" style="stop-color:#121212;stop-opacity:0.9" />
        </linearGradient>
        <clipPath id="clip3">
            <rect x="15" y="15" width="120" height="120" rx="15" />
        </clipPath>
        <filter id="blur">
            <feGaussianBlur in="SourceGraphic" stdDeviation="1" />
        </filter>
    </defs>
    {glow}
    
    <!-- Background -->
    <rect width="450" height="150" fill="url(#grad2)" rx="20"/>
    <rect width="450" height="150" fill="#000000" opacity="0.3" rx="20"/>
    
    <!-- Glass effect -->
    <rect x="10" y="10" width="430" height="130" fill="#FFFFFF" opacity="0.05" rx="15"/>
    <rect x="10" y="10" width="430" height="130" fill="none" stroke="#FFFFFF" stroke-width="1" opacity="0.2" rx="15"/>
    
    <!-- Album Art with glow -->
    <g class="{'glow' if is_playing else ''}">
        <image x="15" y="15" width="120" height="120" xlink:href="{img_src}" clip-path="url(#clip3)" />
        <rect x="15" y="15" width="120" height="120" rx="15" fill="none" stroke="#1DB954" stroke-width="2" opacity="0.6"/>
    </g>
    
    <!-- Content -->
    <text x="155" y="50" font-family="'Segoe UI', Arial, sans-serif" font-size="22" font-weight="bold" fill="#FFFFFF" 
          style="text-shadow: 0 2px 4px rgba(0,0,0,0.5);">
        {song[:22] + ('...' if len(song)>22 else '')}
    </text>
    <text x="155" y="80" font-family="'Segoe UI', Arial, sans-serif" font-size="16" fill="#E0E0E0" 
          style="text-shadow: 0 1px 2px rgba(0,0,0,0.5);">
        {artist[:28] + ('...' if len(artist)>28 else '')}
    </text>
    
    <!-- Status pill -->
    <rect x="155" y="95" width="{"120" if is_playing else "110"}" height="28" fill="#1DB954" rx="14" opacity="0.9"/>
    <text x="{"215" if is_playing else "210"}" y="113" font-family="'Segoe UI', Arial, sans-serif" 
          font-size="13" font-weight="bold" fill="#000000" text-anchor="middle">
        {'🎵 AO VIVO' if is_playing else '⏸️ PAUSADO'}
    </text>
    
    <!-- Spotify branding -->
    <text x="420" y="135" font-family="'Segoe UI', Arial, sans-serif" font-size="10" fill="#FFFFFF" opacity="0.6" text-anchor="end">
        Spotify
    </text>
</svg>
"""
    return svg.strip()

def generate_recent_track_card(track, index):
    """Gera um card compacto para cada música recente"""
    artist = track["artists"][0]["name"]
    song = track["name"]
    image = track["album"]["images"][-1]["url"]
    
    song = song.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    artist = artist.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    
    try:
        img_content = requests.get(image).content
        img_b64 = base64.b64encode(img_content).decode()
        img_src = f"data:image/jpeg;base64,{img_b64}"
    except:
        img_src = image
    
    svg = f"""
<svg width="190" height="60" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
    <rect x="0" y="0" width="190" height="60" rx="8" fill="#181818" stroke="#282828" stroke-width="1"/>
    
    <defs>
        <clipPath id="clip{index}">
            <rect x="8" y="8" width="44" height="44" rx="4" />
        </clipPath>
    </defs>
    <image x="8" y="8" width="44" height="44" xlink:href="{img_src}" clip-path="url(#clip{index})" />

    <g transform="translate(60, 22)">
        <text x="0" y="0" font-family="'Segoe UI', Ubuntu, Sans-Serif" font-size="12" font-weight="bold" fill="#FFFFFF">{song[:18] + ('...' if len(song)>18 else '')}</text>
        <text x="0" y="18" font-family="'Segoe UI', Ubuntu, Sans-Serif" font-size="10" fill="#B3B3B3">{artist[:20] + ('...' if len(artist)>20 else '')}</text>
    </g>
</svg>
"""
    return svg.strip()

def update_readme(current_track, is_playing, recent_tracks):
    if not current_track:
        return

    # Gerar e salvar SVG principal
    svg_content = generate_spotify_card(current_track, is_playing)
    if svg_content:
        # Agora salva em stats/
        with open("stats/spotify_card.svg", "w", encoding="utf-8") as f:
            f.write(svg_content)

    # Gerar SVGs para cada música recente
    recent_html = ""
    if recent_tracks:
        recent_cards = []
        for i, track in enumerate(recent_tracks[:4], 1):
            track_svg = generate_recent_track_card(track, i)
            filename = f"recent_{i}.svg"
            # Agora salva em stats/
            with open(f"stats/{filename}", "w", encoding="utf-8") as f:
                f.write(track_svg)
            
            url = track["external_urls"]["spotify"]
            # Atualizar link para pasta stats
            recent_cards.append(f'<a href="{url}"><img src="https://raw.githubusercontent.com/Clebio2030/Clebio2030/main/stats/{filename}" alt="Track {i}" width="190"></a>')
        
        recent_html = f"""
<p align="center"><strong>Outras Recentes</strong></p>

<div align="center">
  <table>
    <tr>
      <td>{recent_cards[0] if len(recent_cards) > 0 else ''}</td>
      <td>{recent_cards[1] if len(recent_cards) > 1 else ''}</td>
    </tr>
    <tr>
      <td>{recent_cards[2] if len(recent_cards) > 2 else ''}</td>
      <td>{recent_cards[3] if len(recent_cards) > 3 else ''}</td>
    </tr>
  </table>
</div>
"""

    # Atualizar README
    new_content = f"""<!-- spotify_readme_start -->
<div align="center">
  <a href="{current_track['external_urls']['spotify']}">
    <img src="https://raw.githubusercontent.com/Clebio2030/Clebio2030/main/stats/spotify_card.svg" alt="Spotify Status" width="450">
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
            print("Spotify card atualizado com design Glassmorphism!")
        else:
            print("Erro ao obter token de acesso.")
    except Exception as e:
        print(f"Erro: {e}")
