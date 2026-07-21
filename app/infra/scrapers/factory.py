from typing import Dict, Type
from app.infra.scrapers.base_scraper import BaseScraper
from app.infra.scrapers.mercado_livre import MercadoLivreScraper
from app.helpers.url_parser import get_domain_name


class ScraperFactory:
    # Mapeamento de domínios suportados para suas respectivas classes concretas
    _scrapers: Dict[str, Type[BaseScraper]] = {
        "mercadolivre.com.br": MercadoLivreScraper,
        "mercadolivre.com": MercadoLivreScraper,
        "produto.mercadolivre.com.br": MercadoLivreScraper
    }

    @classmethod
    def get_scraper(cls, url: str) -> BaseScraper:
        """
        Retorna a instância concreta do Scraper com base no domínio da URL fornecida.
        """
        domain = get_domain_name(url)
        
        # Procura por correspondência parcial (ex: "mercadolivre" contido no domínio)
        for key, scraper_class in cls._scrapers.items():
            if key in domain:
                return scraper_class()
                
        raise ValueError(
            f"O domínio '{domain}' não é suportado no momento. "
            "Atualmente monitoramos apenas produtos do Mercado Livre."
        )
