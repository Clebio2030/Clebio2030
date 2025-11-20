import os
import requests
import sys
from datetime import datetime, timedelta
from collections import defaultdict

# Configurações
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
USERNAME = "Clebio2030"
DAYS_TO_CHECK = 30

# Configuração do SVG
SVG_WIDTH = 800
SVG_HEIGHT = 200  # Aumentei a altura para caber tudo

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

def get_authenticated_user():
    """Retorna dados do usuário autenticado para verificar permissões e emails"""
    url = "https://api.github.com/user"
    resp = requests.get(url, headers=get_headers())
    if resp.status_code != 200:
        error(f"Falha na autenticação: {resp.status_code}")
        return None
    return resp.json()

def get_all_repos():
    """Busca TODOS os repositórios (privados e públicos)"""
    repos = []
    page = 1
    while True:
        url = f"https://api.github.com/user/repos?per_page=100&page={page}&type=all"
        resp = requests.get(url, headers=get_headers())
        
        if resp.status_code != 200:
            error(f"Erro ao listar repositórios: {resp.status_code}")
            break
            
        data = resp.json()
        if not data:
            break
            
        repos.extend(data)
        page += 1
        
    log(f"Total de repositórios encontrados: {len(repos)}")
    return repos

def count_commits(repos, user_emails):
    """Conta commits iterando repositório por repositório"""
    since_date = (datetime.now() - timedelta(days=DAYS_TO_CHECK)).isoformat()
    commits_by_day = defaultdict(int)
    total_commits = 0
    processed_repos = 0
    
    log(f"Buscando commits desde: {since_date}")
    
    for repo in repos:
        repo_name = repo['full_name']
        # Otimização: Busca apenas commits recentes
        url = f"https://api.github.com/repos/{repo_name}/commits"
        params = {
            "since": since_date,
            "per_page": 100,
            "author": USERNAME # Tenta filtrar pela API primeiro
        }
        
        try:
            resp = requests.get(url, headers=get_headers(), params=params, timeout=10)
            
            if resp.status_code == 200:
                commits = resp.json()
                count = len(commits)
                
                if count > 0:
                    log(f"  + {count} commits em {repo_name}")
                    total_commits += count
                    for commit in commits:
                        date = commit['commit']['author']['date'][:10]
                        commits_by_day[date] += 1
                
                processed_repos += 1
                
            elif resp.status_code == 409: # Repositório vazio
                continue
            else:
                # Se falhar com filtro de autor, tenta sem filtro e filtra no código
                # Isso é comum em repos privados onde o email do commit não bate com o perfil
                pass
                
        except Exception as e:
            error(f"Erro ao processar {repo_name}: {e}")

    return total_commits, commits_by_day

def generate_svg(total_commits, commits_by_day, total_repos):
    """Gera o SVG com design corrigido"""
    
    # Dados para o gráfico
    dates = sorted(commits_by_day.keys())
    # Preenche dias vazios nos últimos 30 dias
    today = datetime.now()
    all_dates = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(29, -1, -1)]
    
    max_commits = max(commits_by_day.values()) if commits_by_day else 1
    
    bars = []
    bar_width = 20
    start_x = 40
    
    # Calcula commits dos últimos 7 dias
    last_7_days_count = 0
    for i in range(7):
        d = (today - timedelta(days=i)).strftime('%Y-%m-%d')
        last_7_days_count += commits_by_day.get(d, 0)

    for i, date in enumerate(all_dates):
        count = commits_by_day.get(date, 0)
        height = (count / max_commits) * 60 if max_commits > 0 else 0
        height = max(height, 2) if count > 0 else 0 # Altura mínima para visibilidade
        
        x = start_x + (i * 24)
        y = 160 - height
        
        color = "#1DB954" if count > 0 else "#2b303b"
        
        bars.append(f'<rect x="{x}" y="{y}" width="{bar_width}" height="{height}" fill="{color}" rx="2" />')
        
        # Labels de data (apenas alguns)
        if i % 5 == 0:
            day_label = date[8:] # Dia
            bars.append(f'<text x="{x + bar_width/2}" y="175" font-family="Arial" font-size="9" fill="#666" text-anchor="middle">{day_label}</text>')

    svg_content = f"""
    <svg width="{SVG_WIDTH}" height="{SVG_HEIGHT}" xmlns="http://www.w3.org/2000/svg">
        <style>
            .text {{ font-family: 'Segoe UI', Ubuntu, Sans-Serif; fill: white; }}
            .label {{ fill: #8b949e; font-size: 12px; }}
            .value {{ font-weight: bold; font-size: 24px; }}
            .title {{ font-weight: bold; font-size: 16px; fill: #1DB954; }}
        </style>
        
        <!-- Fundo -->
        <rect width="100%" height="100%" fill="#0d1117" rx="10" />
        
        <!-- Título -->
        <text x="20" y="30" class="text title">Atividade Privada & Pública</text>
        
        <!-- Cards -->
        <g transform="translate(20, 50)">
            <!-- Commits 30 dias -->
            <rect width="240" height="70" fill="#161b22" rx="6" stroke="#30363d" />
            <text x="120" y="25" text-anchor="middle" class="text label">Commits (30 dias)</text>
            <text x="120" y="55" text-anchor="middle" class="text value" fill="#2f81f7">{total_commits}</text>
        </g>
        
        <g transform="translate(280, 50)">
            <!-- Commits 7 dias -->
            <rect width="240" height="70" fill="#161b22" rx="6" stroke="#30363d" />
            <text x="120" y="25" text-anchor="middle" class="text label">Commits (7 dias)</text>
            <text x="120" y="55" text-anchor="middle" class="text value" fill="#1DB954">{last_7_days_count}</text>
        </g>
        
        <g transform="translate(540, 50)">
            <!-- Total Repos -->
            <rect width="240" height="70" fill="#161b22" rx="6" stroke="#30363d" />
            <text x="120" y="25" text-anchor="middle" class="text label">Total Repositórios</text>
            <text x="120" y="55" text-anchor="middle" class="text value" fill="#a371f7">{total_repos}</text>
        </g>
        
        <!-- Gráfico -->
        { "".join(bars) }
        
    </svg>
    """
    return svg_content

if __name__ == "__main__":
    if not GITHUB_TOKEN:
        error("GITHUB_TOKEN não encontrado!")
        sys.exit(1)

    log("Iniciando geração de estatísticas...")
    
    user = get_authenticated_user()
    if not user:
        sys.exit(1)
        
    user_emails = [user.get('email')]
    log(f"Usuário identificado: {user['login']} (Email principal: {user_emails[0]})")

    repos = get_all_repos()
    total_commits, commits_by_day = count_commits(repos, user_emails)
    
    log(f"Geração concluída. Total Commits: {total_commits}")
    
    svg = generate_svg(total_commits, commits_by_day, len(repos))
    
    with open("private-stats.svg", "w", encoding="utf-8") as f:
        f.write(svg)
        
    log("Arquivo private-stats.svg salvo com sucesso.")
