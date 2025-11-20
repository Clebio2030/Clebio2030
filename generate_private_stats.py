import os
import requests
import sys
from datetime import datetime, timedelta
from collections import defaultdict

# ================= CONFIGURAÇÕES =================
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
DAYS = 30
# =================================================

def log(msg):
    print(f"[INFO] {msg}")
    sys.stdout.flush()

def error(msg):
    print(f"[ERRO] {msg}")
    sys.stdout.flush()

def get_headers():
    return {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

def check_token_scopes():
    """Verifica as permissões do token"""
    try:
        resp = requests.head("https://api.github.com/user", headers=get_headers())
        scopes = resp.headers.get('X-OAuth-Scopes', '')
        log(f"Permissões do Token: {scopes}")
        
        if 'repo' not in scopes:
            error("⚠️ O TOKEN NÃO TEM PERMISSÃO 'REPO'! ELE NÃO VAI LER REPOSITÓRIOS PRIVADOS.")
            error("Vá em Developer Settings > Personal Access Tokens > Tokens (Classic) e marque 'repo'.")
        else:
            log("✅ Permissão 'repo' detectada.")
            
    except Exception as e:
        error(f"Não foi possível verificar permissões: {e}")

def run_analysis():
    if not GITHUB_TOKEN:
        error("GITHUB_TOKEN não encontrado.")
        return

    check_token_scopes()

    # 1. Pegar usuário
    user_resp = requests.get("https://api.github.com/user", headers=get_headers())
    if user_resp.status_code != 200:
        error("Falha ao pegar usuário")
        return
    
    user_data = user_resp.json()
    username = user_data['login']
    log(f"Usuário: {username}")

    # 2. Pegar todos os repositórios (paginado)
    repos = []
    page = 1
    while True:
        r = requests.get(f"https://api.github.com/user/repos?per_page=100&page={page}&type=all", headers=get_headers())
        data = r.json()
        if not data: break
        repos.extend(data)
        page += 1
    
    log(f"Total de repositórios encontrados: {len(repos)}")
    
    # 3. Contar commits
    since_date = (datetime.now() - timedelta(days=DAYS)).isoformat()
    total_commits = 0
    commits_by_day = defaultdict(int)
    repos_with_activity = 0

    log(f"Analisando commits desde {since_date[:10]}...")

    for repo in repos:
        repo_name = repo['full_name']
        is_private = repo['private']
        
        # Pega commits recentes
        commits_url = f"https://api.github.com/repos/{repo_name}/commits"
        params = {'since': since_date, 'per_page': 100}
        
        try:
            c_resp = requests.get(commits_url, headers=get_headers(), params=params, timeout=10)
            
            if c_resp.status_code == 200:
                commits = c_resp.json()
                repo_count = 0
                
                for c in commits:
                    # Filtro simplificado: Tenta bater o login ou nome
                    author = c.get('author') # Dados do GitHub User
                    commit_author = c.get('commit', {}).get('author', {}) # Dados do git config
                    
                    match = False
                    # Check 1: Login do GitHub (mais forte)
                    if author and author.get('login', '').lower() == username.lower():
                        match = True
                    # Check 2: Email (se contém o nome do usuário ou noreply)
                    elif username.lower() in commit_author.get('email', '').lower():
                        match = True
                    # Check 3: Nome exato
                    elif commit_author.get('name', '').lower() == username.lower():
                        match = True
                        
                    if match:
                        repo_count += 1
                        date = commit_author.get('date')[:10]
                        commits_by_day[date] += 1
                
                if repo_count > 0:
                    total_commits += repo_count
                    repos_with_activity += 1
                    privacy_tag = "[PRIVADO]" if is_private else "[PÚBLICO]"
                    log(f"  Found {repo_count} commits in {repo_name} {privacy_tag}")
                    
        except Exception as e:
            pass

    log(f"RESULTADO FINAL: {total_commits} commits em {repos_with_activity} repositórios.")
    
    # 4. Gerar SVG Simples e Robusto
    generate_svg(total_commits, commits_by_day, len(repos))

def generate_svg(total_commits, commits_by_day, total_repos):
    # Prepara dados
    dates = sorted(commits_by_day.keys())
    today = datetime.now()
    
    # Gráfico de barras
    bars = ""
    max_val = max(commits_by_day.values()) if commits_by_day else 1
    
    for i in range(30):
        d = (today - timedelta(days=29-i)).strftime('%Y-%m-%d')
        count = commits_by_day.get(d, 0)
        
        height = (count / max_val) * 40 if max_val > 0 else 0
        if count > 0 and height < 2: height = 2 # Mínimo visível
        
        x = 40 + (i * 24)
        y = 140 - height
        color = "#1DB954" if count > 0 else "#21262d"
        
        bars += f'<rect x="{x}" y="{y}" width="18" height="{height}" fill="{color}" rx="2" />'
        
        # Datas (a cada 5 dias)
        if i % 5 == 0:
            day_str = d[8:]
            bars += f'<text x="{x+9}" y="155" font-family="Arial" font-size="9" fill="#6e7681" text-anchor="middle">{day_str}</text>'

    last_7_total = sum(commits_by_day.get((today - timedelta(days=i)).strftime('%Y-%m-%d'), 0) for i in range(7))

    svg = f"""
<svg width="800" height="180" xmlns="http://www.w3.org/2000/svg">
    <style>
        .bg {{ fill: #0d1117; }}
        .card {{ fill: #161b22; stroke: #30363d; }}
        .text-main {{ font-family: 'Segoe UI', sans-serif; fill: #e6edf3; font-weight: bold; }}
        .text-sub {{ font-family: 'Segoe UI', sans-serif; fill: #7d8590; font-size: 12px; }}
        .num {{ font-size: 24px; font-weight: bold; font-family: 'Segoe UI', sans-serif; }}
    </style>
    
    <rect width="100%" height="100%" class="bg" rx="10" />
    
    <text x="20" y="30" class="text-main" font-size="16">Atividade Recente (Privada & Pública)</text>
    
    <!-- Cards -->
    <g transform="translate(20, 50)">
        <rect width="240" height="70" class="card" rx="6" />
        <text x="120" y="25" text-anchor="middle" class="text-sub">Total Commits (30d)</text>
        <text x="120" y="55" text-anchor="middle" class="num" fill="#2f81f7">{total_commits}</text>
    </g>
    
    <g transform="translate(280, 50)">
        <rect width="240" height="70" class="card" rx="6" />
        <text x="120" y="25" text-anchor="middle" class="text-sub">Últimos 7 dias</text>
        <text x="120" y="55" text-anchor="middle" class="num" fill="#1DB954">{last_7_total}</text>
    </g>
    
    <g transform="translate(540, 50)">
        <rect width="240" height="70" class="card" rx="6" />
        <text x="120" y="25" text-anchor="middle" class="text-sub">Repositórios</text>
        <text x="120" y="55" text-anchor="middle" class="num" fill="#a371f7">{total_repos}</text>
    </g>
    
    {bars}
</svg>
"""
    
    with open("private-stats.svg", "w", encoding="utf-8") as f:
        f.write(svg)
    log("SVG gerado com sucesso.")

if __name__ == "__main__":
    run_analysis()
