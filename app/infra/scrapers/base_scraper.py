from abc import ABC, abstractmethod
from typing import Optional


class BaseScraper(ABC):
    """Interface mínima que todos os scrapers devem implementar."""

    @abstractmethod
    def scrape(self, url: str) -> Optional[float]:
        """Recebe uma URL, extrai e retorna o preço como float. Retorna None em caso de falha."""
        pass
