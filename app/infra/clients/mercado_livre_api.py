import re
import requests
from typing import Optional
from app.core.config import settings
from app.infra.logging.logger import logger


class MercadoLivreAPIClient:
    """
    Cliente para integração com a API Oficial do Mercado Livre (Developers API).
    Realiza requisições autenticadas via OAuth 2.0 (Client Credentials).
    """

    OAUTH_TOKEN_URL = "https://api.mercadolibre.com/oauth/token"
    ITEMS_API_URL = "https://api.mercadolibre.com/items/"

    @staticmethod
    def extract_item_id(url: str) -> Optional[str]:
        """
        Extrai o ID do item (ex: MLB3388701977) a partir de URLs do Mercado Livre.
        Exemplos suportados:
          - https://produto.mercadolivre.com.br/MLB-3388701977-placa-de-video...
          - https://www.mercadolivre.com.br/p/MLB27564070
          - https://www.mercadolivre.com.br/p/MLB-27564070
        """
        if not url:
            return None
            
        match = re.search(r"MLB-?(\d+)", url, re.IGNORECASE)
        if match:
            return f"MLB{match.group(1)}"
        return None

    def get_access_token(self) -> Optional[str]:
        """
        Obtém um token de acesso OAuth 2.0 usando o fluxo Client Credentials.
        """
        client_id = settings.MERCADO_LIVRE_CLIENT_ID
        client_secret = settings.MERCADO_LIVRE_CLIENT_SECRET

        if not client_id or not client_secret:
            logger.debug("Credenciais da API do Mercado Livre não configuradas no .env.")
            return None

        payload = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret
        }

        try:
            logger.info("Solicitando Token de Acesso à API Oficial do Mercado Livre...")
            response = requests.post(self.OAUTH_TOKEN_URL, data=payload, timeout=10)
            if response.status_code == 200:
                data = response.json()
                token = data.get("access_token")
                logger.info("Token de acesso obtido com sucesso.")
                return token
            else:
                logger.warning(f"Falha ao obter token OAuth do Mercado Livre. Status: {response.status_code}, Erro: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Erro de conexão ao solicitar token OAuth do Mercado Livre: {str(e)}")
            return None

    def get_item_price(self, url: str) -> Optional[float]:
        """
        Consulta o preço principal do item na API Oficial do Mercado Livre.
        Retorna o valor numérico (float) ou None se não for possível obter via API.
        """
        item_id = self.extract_item_id(url)
        if not item_id:
            logger.debug(f"Não foi possível extrair um ID do Mercado Livre (MLB...) da URL: {url}")
            return None

        token = self.get_access_token()
        if not token:
            logger.debug("Token de acesso nulo. Pulando consulta via API Oficial.")
            return None

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }

        item_url = f"{self.ITEMS_API_URL}{item_id}"
        try:
            logger.info(f"Consultando item {item_id} na API Oficial do Mercado Livre...")
            resp = requests.get(item_url, headers=headers, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                price = data.get("price")
                title = data.get("title", "")
                
                if price is not None and float(price) > 0:
                    val = float(price)
                    logger.info(f"Preço obtido via API Oficial ML para '{title[:40]}...': R$ {val:.2f}")
                    return val
                else:
                    logger.warning(f"API Oficial do ML retornou preço inválido para o item {item_id}: {price}")
                    return None
            else:
                logger.warning(f"Consulta ao item {item_id} na API Oficial retornou status {resp.status_code}: {resp.text[:200]}")
                return None
        except Exception as e:
            logger.error(f"Erro ao consultar item {item_id} na API Oficial do Mercado Livre: {str(e)}")
            return None
