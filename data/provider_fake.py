import random
from datetime import datetime, timedelta
from typing import Dict, List

from .cache import TTLCache
from .provider_base import SportsDataProvider

EQUIPES = ["Real Madrid", "Barcelona", "Manchester United", "Liverpool", "Bayern", "PSG"]
JOGADORES = ["Jogador A", "Jogador B", "Jogador C", "Jogador D", "Jogador E", "Jogador F"]

class FakeProvider(SportsDataProvider):
    def __init__(self, cache: TTLCache, ttl_seconds: int = 60) -> None:
        self.cache = cache
        self.ttl_seconds = ttl_seconds

    def get_jogos(self, days: int = 25) -> List[Dict]:
        key = f"fake:jogos:{days}"
        cached = self.cache.get(key)
        if cached is not None:
            return cached

        jogos: List[Dict] = []
        for i in range(days):
            t1, t2 = random.sample(EQUIPES, 2)
            jogos.append({
                "time_casa": t1,
                "time_fora": t2,
                "data": (datetime.today() - timedelta(days=i)).strftime("%Y-%m-%d"),
                "competicao": random.choice(["La Liga", "Premier League", "Bundesliga", "Serie A", "Ligue 1"]),
                "metricas": {
                    "chutes": random.randint(5, 20),
                    "chutes_prob": random.randint(60, 100),
                    "chutes_ao_gol": random.randint(2, 15),
                    "chutes_ao_gol_prob": random.randint(60, 100),
                    "gols": random.randint(0, 5),
                    "gols_prob": random.randint(60, 100),
                    "faltas": random.randint(5, 20),
                    "faltas_prob": random.randint(60, 100),
                    "cartoes": random.randint(0, 5),
                    "cartoes_prob": random.randint(60, 100),
                    "laterais": random.randint(0, 10),
                    "laterais_prob": random.randint(60, 100),
                    "escanteios": random.randint(0, 10),
                    "escanteios_prob": random.randint(60, 100),
                    "tiros_meta": random.randint(0, 10),
                    "tiros_meta_prob": random.randint(60, 100),
                }
            })

        self.cache.set(key, jogos, self.ttl_seconds)
        return jogos

    def get_ranking_equipes(self) -> List[Dict]:
        key = "fake:rank_equipes"
        cached = self.cache.get(key)
        if cached is not None:
            return cached

        # Ranking simples por "score"
        ranking = [{"equipe": e, "score": random.randint(60, 100)} for e in EQUIPES]
        self.cache.set(key, ranking, self.ttl_seconds)
        return ranking

    def get_ranking_jogadores(self) -> List[Dict]:
        """
        Retorna jogadores com as mesmas métricas que seu ranking atual espera:
        - chutes, chutes_prob
        - chutes_ao_gol, chutes_ao_gol_prob
        - faltas, faltas_prob
        - desarmes, desarmes_prob
        """
        key = "fake:rank_jogadores_detalhado"
        cached = self.cache.get(key)
        if cached is not None:
            return cached

        lista: List[Dict] = []
        for nome in JOGADORES:
            lista.append({
                "nome": nome,
                "chutes": random.randint(0, 10),
                "chutes_prob": random.randint(60, 100),
                "chutes_ao_gol": random.randint(0, 8),
                "chutes_ao_gol_prob": random.randint(60, 100),
                "faltas": random.randint(0, 5),
                "faltas_prob": random.randint(60, 100),
                "desarmes": random.randint(0, 10),
                "desarmes_prob": random.randint(60, 100),
            })

        self.cache.set(key, lista, self.ttl_seconds)
        return lista
