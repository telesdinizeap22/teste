import os
from datetime import datetime
from typing import Dict, List

import requests

from .cache import TTLCache
from .provider_base import SportsDataProvider


class ApiFootballProvider(SportsDataProvider):
    """
    Provider real baseado na API-FOOTBALL.
    - Puxa fixtures (jogos) de uma liga/temporada
    - Puxa statistics por fixture
    - Normaliza no formato do T&T
    """

    def __init__(self, cache: TTLCache, ttl_seconds: int = 300) -> None:
        self.cache = cache
        self.ttl_seconds = ttl_seconds

        self.base_url = os.getenv("API_FOOTBALL_BASE_URL", "https://v3.football.api-sports.io")
        self.league = int(os.getenv("API_FOOTBALL_LEAGUE", "39"))   # 39 = Premier League
        self.season = int(os.getenv("API_FOOTBALL_SEASON", "2024"))

        self.key = os.getenv("API_FOOTBALL_KEY", "5b4e43cd783ae4254b26b50a4b032494").strip()
        if not self.key:
            raise RuntimeError("API_FOOTBALL_KEY não configurada.")

        # Se você usar RapidAPI, defina API_FOOTBALL_USE_RAPIDAPI=1 no Render
        self.use_rapidapi = os.getenv("API_FOOTBALL_USE_RAPIDAPI", "0") == "1"

    def _headers(self) -> Dict[str, str]:
        if self.use_rapidapi:
            return {
                "x-rapidapi-key": self.key,
                "x-rapidapi-host": "v3.football.api-sports.io",
            }
        # modo API-Sports direto
        return {"x-apisports-key": self.key}

    @staticmethod
    def _safe_int(value) -> int:
        if value is None:
            return 0
        if isinstance(value, (int, float)):
            return int(value)
        try:
            return int(str(value).strip())
        except Exception:
            return 0

    @staticmethod
    def _stats_to_map(stats_list: List[Dict]) -> Dict[str, int]:
        """
        Converte lista [{type:..., value:...}] em dict {type: value_int}
        """
        out: Dict[str, int] = {}
        if not isinstance(stats_list, list):
            return out
        for s in stats_list:
            t = (s.get("type") or "").strip()
            v = s.get("value")
            out[t] = ApiFootballProvider._safe_int(v)
        return out

    @staticmethod
    def _minmax_probs(items: List[Dict], metric_keys: List[str]) -> None:
        """
        Gera *_prob (60..100) por min-max dentro da amostra.
        Só pra UI continuar com "prob" enquanto você não implementa modelo real.
        """
        for k in metric_keys:
            values = [int(it.get(k, 0)) for it in items]
            if not values:
                continue
            mn, mx = min(values), max(values)
            if mx == mn:
                for it in items:
                    it[f"{k}_prob"] = 75
                continue
            for it in items:
                v = int(it.get(k, 0))
                p = 60 + int((v - mn) * 40 / (mx - mn))
                it[f"{k}_prob"] = max(60, min(100, p))

    def get_jogos(self, days: int = 25) -> List[Dict]:
        cache_key = f"api_football:jogos:{self.league}:{self.season}:{days}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        # 1) Pega fixtures concluídos
        fixtures_url = f"{self.base_url}/fixtures"
        params = {
            "league": self.league,
            "season": self.season,
            "status": "FT-AET-PEN",  # concluídos
        }
        r = requests.get(fixtures_url, headers=self._headers(), params=params, timeout=30)
        r.raise_for_status()
        data = r.json()

        fixtures = data.get("response", [])
        if not isinstance(fixtures, list):
            fixtures = []

        # pega os últimos N fixtures
        fixtures = fixtures[-days:]

        jogos_out: List[Dict] = []

        # 2) Para cada fixture, busca statistics (mais 1 request por jogo)
        stats_url = f"{self.base_url}/fixtures/statistics"

        for item in fixtures:
            fixture = item.get("fixture", {}) or {}
            league = item.get("league", {}) or {}
            teams = item.get("teams", {}) or {}
            goals = item.get("goals", {}) or {}

            fixture_id = (fixture.get("id") or 0)
            home = (teams.get("home") or {}).get("name") or "Home"
            away = (teams.get("away") or {}).get("name") or "Away"

            # data ISO -> YYYY-MM-DD
            date_iso = fixture.get("date")
            date_str = date_iso[:10] if isinstance(date_iso, str) and len(date_iso) >= 10 else ""
            if not date_str:
                date_str = datetime.utcnow().strftime("%Y-%m-%d")

            comp = league.get("name") or f"League {self.league}"

            # placar final
            g_home = self._safe_int(goals.get("home"))
            g_away = self._safe_int(goals.get("away"))
            g_total = g_home + g_away

            # busca estatísticas do fixture
            stats_resp = []
            if fixture_id:
                rr = requests.get(stats_url, headers=self._headers(), params={"fixture": fixture_id}, timeout=30)
                rr.raise_for_status()
                stats_json = rr.json()
                stats_resp = stats_json.get("response", [])
                if not isinstance(stats_resp, list):
                    stats_resp = []

            # stats_resp normalmente tem 2 itens (home/away)
            home_stats = {}
            away_stats = {}
            if len(stats_resp) >= 1:
                home_stats = self._stats_to_map((stats_resp[0] or {}).get("statistics", []))
            if len(stats_resp) >= 2:
                away_stats = self._stats_to_map((stats_resp[1] or {}).get("statistics", []))

            def metric_sum(name: str) -> int:
                return int(home_stats.get(name, 0) + away_stats.get(name, 0))

            shots_on_goal = metric_sum("Shots on Goal")
            shots_off_goal = metric_sum("Shots off Goal")
            total_shots = metric_sum("Total Shots")
            if total_shots == 0 and (shots_on_goal + shots_off_goal) > 0:
                total_shots = shots_on_goal + shots_off_goal

            corners = metric_sum("Corner Kicks")
            fouls = metric_sum("Fouls")

            yellow = metric_sum("Yellow Cards")
            red = metric_sum("Red Cards")
            cards = yellow + red

            # Nem sempre existem laterais/tiros_meta na API, então deixamos 0 por enquanto
            laterais = metric_sum("Throw-ins")
            tiros_meta = 0

            jogos_out.append({
                "time_casa": home,
                "time_fora": away,
                "data": date_str,
                "competicao": comp,
                "metricas": {
                    "chutes": total_shots,
                    "chutes_ao_gol": shots_on_goal,
                    "gols": g_total,
                    "faltas": fouls,
                    "cartoes": cards,
                    "laterais": laterais,
                    "escanteios": corners,
                    "tiros_meta": tiros_meta,
                }
            })

        # cria *_prob pra manter seu site funcionando como hoje
        metric_keys = ["chutes", "chutes_ao_gol", "gols", "faltas", "cartoes", "laterais", "escanteios", "tiros_meta"]
        flat = []
        for j in jogos_out:
            d = {}
            d.update(j["metricas"])
            flat.append(d)
        self._minmax_probs(flat, metric_keys)
        for j, probs in zip(jogos_out, flat):
            for k in metric_keys:
                j["metricas"][f"{k}_prob"] = probs.get(f"{k}_prob", 75)

        self.cache.set(cache_key, jogos_out, self.ttl_seconds)
        return jogos_out

    def get_ranking_equipes(self) -> List[Dict]:
        # por enquanto simples: conta ocorrências dos times nos jogos
        jogos = self.get_jogos(days=25)
        count = {}
        for j in jogos:
            for t in [j["time_casa"], j["time_fora"]]:
                count[t] = count.get(t, 0) + 1
        return [{"equipe": k, "score": v} for k, v in sorted(count.items(), key=lambda x: x[1], reverse=True)]

    def get_ranking_jogadores(self) -> List[Dict]:
        # Jogadores exigem endpoints específicos (muitas chamadas / depende do plano).
        # Para o "teste de liga fake" com estatísticas de jogo, deixamos vazio por enquanto.
        return []
