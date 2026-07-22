from typing import Optional
from app.infra.scrapers.base_scraper import BaseScraper
from app.infra.logging.logger import logger
from app.domain.mercado_livre.usecase import GetMercadoLivrePriceByUrlUseCase


class MercadoLivreScraper(BaseScraper):
    """
    Fachada para obtenção do preço do produto no Mercado Livre através do serviço de domínio oficial.
    """

    def __init__(self):
        self.price_use_case = GetMercadoLivrePriceByUrlUseCase()

    def scrape(self, url: str) -> Optional[float]:
        """
        Consulta o preço do anúncio no Mercado Livre através do domínio de integração oficial.
        """
        logger.info(f"Delegando consulta de preço do Mercado Livre para o domínio de integração: {url}")
        res = self.price_use_case.execute(url)
        return res.price
