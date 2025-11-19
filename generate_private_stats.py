import os
import requests
from datetime import datetime, timedelta
from collections import defaultdict

GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
USERNAME = "Clebio2030"

def get_user_info():
    """Busca informações do usuário autenticado"""
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get("https://api.github.com/user", headers=headers)
    if response.status_code == 200:
        user = response.json()
        print(f"✓ Autenticado como: {user['login']}")
        return user
    else:
        print(f"❌ Erro na autenticação: {response.status_code}")
        return None

def get_all_repos():
    """Busca todos os repositórios incluindo privados"""
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    repos = []
    page = 1
    
    while True:
        url = f"https://api.github.com/user/repos?per_page=100&page={page}&visibility=all&affiliation=owner"
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            print(f"Erro ao buscar repos: {response.status_code}")
            break
            
        data = response.json()
        
        if not data:
            break
            
        repos.extend(data)
        page += 1
        
        if len(data) < 100:
            break
    
    return repos

def get_user_events(username, days=30):
    """Busca eventos públicos e privados do usuário"""
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    commits_by_day = defaultdict(int)
    total_commits = 0
    
    # Buscar eventos do usuário (inclui atividade privada quando autenticado)
    page = 1
    since = datetime.now() - timedelta(days=days)
    
    while page <= 10:  # Limitar a 10 páginas (300 eventos)
        url = f"https://api.github.com/users/{username}/events?per_page=100&page={page}"
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            print(f"Erro ao buscar eventos: {response.status_code}")
            break
        
        events = response.json()
        
        if not events:
            break
        
        for event in events:
            # Verificar data do evento
            event_date = datetime.strptime(event['created_at'], '%Y-%m-%dT%H:%M:%SZ')
            
            if event_date < since:
                break
            
            # Contar commits em PushEvents
            if event['type'] == 'PushEvent':
                commits = event['payload'].get('commits', [])
                date_str = event['created_at'][:10]
                commits_by_day[date_str] += len(commits)
                total_commits += len(commits)
        
        # Se o último evento é muito antigo, parar
        if events and datetime.strptime(events[-1]['created_at'], '%Y-%m-%dT%H:%M:%SZ') < since:
            break
            
        page += 1
    
    return total_commits, commits_by_day

def get_commit_stats_from_search(days=30):
    """Busca commits usando a API de search (alternativa)"""
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    since = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    
    # Buscar commits do usuário
    url = f"https://api.github.com/search/commits?q=author:{USERNAME}+author-date:>={since}&per_page=100&sort=author-date"
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        total = data.get('total_count', 0)
        
        commits_by_day = defaultdict(int)
        for item in data.get('items', []):
            date = item['commit']['author']['date'][:10]
            commits_by_day[date] += 1
        
        return total, commits_by_day
    else:
        print(f"Aviso: Search API retornou {response.status_code}")
        return 0, {}

def generate_stats_svg(stats_7days, stats_30days, commits_by_day, total_repos):
    """Gera SVG com estatísticas"""
    
    # Calcular última semana
    last_7_days = sorted(commits_by_day.keys())[-7:] if commits_by_day else []
    commits_last_week = sum(commits_by_day[day] for day in last_7_days)
    
    # Gerar barras do gráfico (últimos 30 dias)
    all_days = sorted(commits_by_day.keys())[-30:] if commits_by_day else []
    max_commits = max([commits_by_day[day] for day in all_days]) if all_days else 1
    
    bars = []
    if all_days:
        for i, day in enumerate(all_days):
            count = commits_by_day[day]
            height = (count / max_commits) * 60 if max_commits > 0 else 5
            x = 50 + (i * 25)
            y = 140 - height
            
            bars.append(f'<rect x="{x}" y="{y}" width="20" height="{max(height, 5)}" fill="#1DB954" rx="2" />')
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
    {''.join(bars) if bars else '<text x="400" y="155" font-size="10" fill="#888" text-anchor="middle">Buscando dados de atividade recente...</text>'}
</svg>
"""
    return svg

if __name__ == "__main__":
    if not GITHUB_TOKEN:
        print("❌ Erro: GITHUB_TOKEN não configurado")
        exit(1)
    
    try:
        print("🔐 Verificando autenticação...")
        user = get_user_info()
        
        if not user:
            exit(1)
        
        print("\n🔍 Buscando repositórios (incluindo privados)...")
        repos = get_all_repos()
        print(f"✓ Encontrados {len(repos)} repositórios")
        
        # Mostrar alguns repos para debug
        if repos:
            print(f"  Exemplos: {', '.join([r['name'] for r in repos[:3]])}")
        
        print("\n📊 Buscando atividade recente (método 1: eventos)...")
        stats_30days, commits_by_day = get_user_events(USERNAME, days=30)
        print(f"✓ Commits encontrados via eventos: {stats_30days}")
        
        # Se não encontrou nada, tentar método alternativo
        if stats_30days == 0:
            print("\n📊 Tentando método alternativo (search API)...")
            stats_30days, commits_by_day = get_commit_stats_from_search(days=30)
            print(f"✓ Commits encontrados via search: {stats_30days}")
        
        # Calcular 7 dias
        last_7_days = sorted(commits_by_day.keys())[-7:] if commits_by_day else []
        stats_7days = sum(commits_by_day[day] for day in last_7_days)
        print(f"✓ Commits (7 dias): {stats_7days}")
        
        print("\n🎨 Gerando SVG de estatísticas...")
        svg = generate_stats_svg(stats_7days, stats_30days, commits_by_day, len(repos))
        
        with open("private-stats.svg", "w", encoding="utf-8") as f:
            f.write(svg)
        
        print("✅ Estatísticas geradas em private-stats.svg")
        
    except Exception as e:
        print(f"❌ Erro crítico: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
