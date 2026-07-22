from typing import Optional
from app.infra.scrapers.base_scraper import BaseScraper
from app.infra.logging.logger import logger
from app.infra.clients.mercado_livre_api import MercadoLivreAPIClient


class MercadoLivreScraper(BaseScraper):
    """
    Obtém o preço do produto no Mercado Livre utilizando exclusivamente a API Oficial (Developers API).
    """

    def __init__(self):
        self.api_client = MercadoLivreAPIClient()

    def scrape(self, url: str) -> Optional[float]:
        """
        Extrai o preço do anúncio no Mercado Livre através da API Oficial.
        """
        logger.info(f"Iniciando consulta de preço via API Oficial do Mercado Livre para a URL: {url}")
        
        item_id = self.api_client.extract_item_id(url)
        if not item_id:
            logger.error(f"URL inválida ou ID de anúncio do Mercado Livre (MLB...) não identificado na URL: {url}")
            raise ValueError(f"Não foi possível extrair o ID do anúncio (MLB...) a partir da URL informada: {url}")

        price = self.api_client.get_item_price(url)
        if price is not None and price > 0:
            logger.info(f"Preço obtido com SUCESSO via API Oficial do Mercado Livre: R$ {price:.2f}")
            return price
            
        logger.error(f"Falha ao obter o preço do produto via API Oficial para a URL: {url}")
        raise RuntimeError("Não foi possível obter o preço do produto através da API Oficial do Mercado Livre. Verifique se as credenciais MERCADO_LIVRE_CLIENT_ID e MERCADO_LIVRE_CLIENT_SECRET estão corretas no .env.")
