from abc import ABC, abstractmethod
from typing import Dict, List

class SportsDataProvider(ABC):
    @abstractmethod
    def get_jogos(self, days: int = 25) -> List[Dict]:
        ...

    @abstractmethod
    def get_ranking_equipes(self) -> List[Dict]:
        ...

    @abstractmethod
    def get_ranking_jogadores(self) -> List[Dict]:
        ...
