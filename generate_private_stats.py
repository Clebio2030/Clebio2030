import os
import requests
from datetime import datetime, timedelta
from collections import defaultdict

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
USERNAME = "Clebio2030"

def get_all_repos():
    """Busca todos os repositórios incluindo privados"""
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    repos = []
    page = 1
    
    while True:
        url = f"https://api.github.com/user/repos?per_page=100&page={page}&affiliation=owner,collaborator,organization_member&type=all"
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            print(f"Erro ao buscar repos: {response.status_code}")
            print(f"Response: {response.text}")
            break
            
        data = response.json()
        
        if not data:
            break
            
        repos.extend(data)
        page += 1
        
        if len(data) < 100:
            break
    
    return repos

def get_commits_stats(repos, days=30):
    """Conta commits dos últimos N dias em todos os repos"""
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    since = (datetime.now() - timedelta(days=days)).isoformat()
    
    total_commits = 0
    commits_by_day = defaultdict(int)
    
    for repo in repos:
        repo_name = repo['full_name']
        url = f"https://api.github.com/repos/{repo_name}/commits?author={USERNAME}&since={since}&per_page=100"
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                commits = response.json()
                total_commits += len(commits)
                
                for commit in commits:
                    date = commit['commit']['author']['date'][:10]
                    commits_by_day[date] += 1
            elif response.status_code == 409:  # Empty repository
                continue
            else:
                print(f"Aviso: Erro {response.status_code} ao buscar commits de {repo_name}")
        except Exception as e:
            print(f"Aviso: Erro ao processar {repo_name}: {e}")
            continue
    
    return total_commits, commits_by_day

def generate_stats_svg(stats_7days, stats_30days, commits_by_day, total_repos):
    """Gera SVG com estatísticas"""
    
    # Calcular última semana
    last_7_days = sorted(commits_by_day.keys())[-7:] if commits_by_day else []
    commits_last_week = sum(commits_by_day[day] for day in last_7_days)
    
    # Gerar barras do gráfico (últimos 30 dias)
    all_days = sorted(commits_by_day.keys())[-30:] if commits_by_day else []
    max_commits = max([commits_by_day[day] for day in all_days]) if all_days else 1
    
    bars = []
    for i, day in enumerate(all_days):
        count = commits_by_day[day]
        height = (count / max_commits) * 60 if max_commits > 0 else 0
        x = 50 + (i * 25)
        y = 140 - height
        
        bars.append(f'<rect x="{x}" y="{y}" width="20" height="{height}" fill="#1DB954" rx="2" />')
        bars.append(f'<text x="{x+10}" y="155" font-size="8" fill="#888" text-anchor="middle">{day[-2:]}</text>')
    
    svg = f"""
<svg width="800" height="180" xmlns="http://www.w3.org/2000/svg">
    <rect width="800" height="180" fill="#0d1117" rx="10"/>
    
    <!-- Título -->
    <text x="400" y="25" font-family="'Segoe UI', Ubuntu, sans-serif" font-size="16" font-weight="bold" fill="#fff" text-anchor="middle">
        📊 Estatísticas Completas (Incluindo Repositórios Privados)
    </text>
    
    <!-- Cards de estatísticas -->
    <g>
        <!-- Card 7 dias -->
        <rect x="50" y="40" width="220" height="70" fill="#161b22" rx="8" stroke="#30363d" stroke-width="1"/>
        <text x="160" y="65" font-family="'Segoe UI', Ubuntu, sans-serif" font-size="12" fill="#8b949e" text-anchor="middle">
            Commits (7 dias)
        </text>
        <text x="160" y="95" font-family="'Segoe UI', Ubuntu, sans-serif" font-size="28" font-weight="bold" fill="#1DB954" text-anchor="middle">
            {commits_last_week}
        </text>
    </g>
    
    <g>
        <!-- Card 30 dias -->
        <rect x="290" y="40" width="220" height="70" fill="#161b22" rx="8" stroke="#30363d" stroke-width="1"/>
        <text x="400" y="65" font-family="'Segoe UI', Ubuntu, sans-serif" font-size="12" fill="#8b949e" text-anchor="middle">
            Commits (30 dias)
        </text>
        <text x="400" y="95" font-family="'Segoe UI', Ubuntu, sans-serif" font-size="28" font-weight="bold" fill="#E535AB" text-anchor="middle">
            {stats_30days}
        </text>
    </g>
    
    <g>
        <!-- Card total -->
        <rect x="530" y="40" width="220" height="70" fill="#161b22" rx="8" stroke="#30363d" stroke-width="1"/>
        <text x="640" y="65" font-family="'Segoe UI', Ubuntu, sans-serif" font-size="12" fill="#8b949e" text-anchor="middle">
            Total de Repositórios
        </text>
        <text x="640" y="95" font-family="'Segoe UI', Ubuntu, sans-serif" font-size="28" font-weight="bold" fill="#7159c1" text-anchor="middle">
            {total_repos}
        </text>
    </g>
    
    <!-- Gráfico de atividade (últimos 30 dias) -->
    <text x="50" y="135" font-family="'Segoe UI', Ubuntu, sans-serif" font-size="12" fill="#8b949e">
        Atividade (últimos 30 dias)
    </text>
    {''.join(bars) if bars else '<text x="400" y="155" font-size="10" fill="#888" text-anchor="middle">Sem dados de commits nos últimos 30 dias</text>'}
</svg>
"""
    return svg

if __name__ == "__main__":
    if not GITHUB_TOKEN:
        print("❌ Erro: GITHUB_TOKEN não configurado")
        exit(1)
    
    try:
        print("🔍 Buscando repositórios (incluindo privados)...")
        repos = get_all_repos()
        print(f"✓ Encontrados {len(repos)} repositórios")
        
        print("📊 Calculando commits dos últimos 7 dias...")
        stats_7days, _ = get_commits_stats(repos, days=7)
        print(f"✓ Commits (7 dias): {stats_7days}")
        
        print("📊 Calculando commits dos últimos 30 dias...")
        stats_30days, commits_by_day = get_commits_stats(repos, days=30)
        print(f"✓ Commits (30 dias): {stats_30days}")
        
        print("🎨 Gerando SVG de estatísticas...")
        svg = generate_stats_svg(stats_7days, stats_30days, commits_by_day, len(repos))
        
        with open("private-stats.svg", "w", encoding="utf-8") as f:
            f.write(svg)
        
        print("✅ Estatísticas geradas em private-stats.svg")
        
    except Exception as e:
        print(f"❌ Erro crítico: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
