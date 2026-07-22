import re
import requests
from typing import Optional, Dict, Any
from app.core.config import settings
from app.infra.logging.logger import logger


class MercadoLivreAPIClient:
    """
    Cliente para integração com a API Oficial do Mercado Livre (Developers API).
    Realiza requisições autenticadas via OAuth 2.0 (Client Credentials).
    """

    OAUTH_TOKEN_URL = "https://api.mercadolibre.com/oauth/token"
    ITEMS_API_URL = "https://api.mercadolibre.com/items/"
    PRODUCTS_API_URL = "https://api.mercadolibre.com/products/"

    @staticmethod
    def extract_item_id(url: str) -> Optional[str]:
        """
        Extrai o ID do item ou produto de catálogo (ex: MLB3388701977 ou MLB27564070) a partir de URLs do Mercado Livre.
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

    def get_item_data(self, item_id: str) -> Optional[Dict[str, Any]]:
        """
        Consulta dados do item/produto na API do Mercado Livre.
        Suporta tanto anúncios diretos (/items/{id}) quanto produtos de catálogo (/products/{id}).
        """
        token = self.get_access_token()
        if not token:
            logger.debug("Token de acesso nulo. Pulando consulta via API Oficial.")
            return None

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }

        # Tentativa 1: Endpoint de Item Direto (/items/{id})
        item_url = f"{self.ITEMS_API_URL}{item_id}"
        try:
            logger.info(f"Consultando item {item_id} em /items/ na API Oficial do Mercado Livre...")
            resp = requests.get(item_url, headers=headers, timeout=10)
            if resp.status_code == 200:
                return resp.json()
            else:
                logger.info(f"Consulta /items/{item_id} retornou status {resp.status_code}. Tentando fallback /products/{item_id}...")
        except Exception as err:
            logger.debug(f"Erro ao consultar /items/{item_id}: {err}")

        # Tentativa 2: Endpoint de Produto de Catálogo (/products/{id})
        product_url = f"{self.PRODUCTS_API_URL}{item_id}"
        try:
            logger.info(f"Consultando produto {item_id} em /products/ na API Oficial do Mercado Livre...")
            resp = requests.get(product_url, headers=headers, timeout=10)
            if resp.status_code == 200:
                p_data = resp.json()
                box_winner = p_data.get("buy_box_winner") or {}
                price = box_winner.get("price") if isinstance(box_winner, dict) else p_data.get("price")
                
                return {
                    "id": p_data.get("id", item_id),
                    "title": p_data.get("name") or p_data.get("title", ""),
                    "price": price,
                    "original_price": box_winner.get("original_price") if isinstance(box_winner, dict) else None,
                    "currency_id": box_winner.get("currency_id") if isinstance(box_winner, dict) else p_data.get("currency_id", "BRL"),
                    "permalink": p_data.get("permalink", ""),
                    "thumbnail": p_data.get("thumbnail", ""),
                    "status": p_data.get("status", "active")
                }
            else:
                logger.warning(f"Consulta /products/{item_id} retornou status {resp.status_code}: {resp.text[:200]}")
        except Exception as err:
            logger.error(f"Erro ao consultar /products/{item_id}: {err}")

        return None

    def get_item_price(self, url: str) -> Optional[float]:
        """
        Consulta o preço principal do item na API Oficial do Mercado Livre a partir da URL.
        """
        item_id = self.extract_item_id(url)
        if not item_id:
            logger.debug(f"Não foi possível extrair um ID do Mercado Livre (MLB...) da URL: {url}")
            return None

        data = self.get_item_data(item_id)
        if not data:
            return None

        price = data.get("price")
        if price is not None and float(price) > 0:
            val = float(price)
            logger.info(f"Preço obtido via API Oficial ML para ID '{item_id}': R$ {val:.2f}")
            return val

        return None
