from typing import Optional
from fastapi import HTTPException, status
import requests
from app.infra.clients.mercado_livre_api import MercadoLivreAPIClient
from app.domain.mercado_livre.schemas import MercadoLivreItemResponse, MercadoLivrePriceResponse
from app.infra.logging.logger import logger


class GetMercadoLivreItemUseCase:
    """
    Caso de uso para consultar os detalhes completos de um item no Mercado Livre pelo seu ID (MLB...).
    """

    def __init__(self, api_client: Optional[MercadoLivreAPIClient] = None):
        self.api_client = api_client or MercadoLivreAPIClient()

    def execute(self, item_id: str) -> MercadoLivreItemResponse:
        clean_id = item_id.strip().upper()
        if not clean_id.startswith("MLB"):
            clean_id = f"MLB{clean_id}"

        token = self.api_client.get_access_token()
        if not token:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Credenciais da API do Mercado Livre não configuradas ou token OAuth indisponível."
            )

        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }
        item_url = f"{self.api_client.ITEMS_API_URL}{clean_id}"

        try:
            logger.info(f"Executando GetMercadoLivreItemUseCase para o ID: {clean_id}")
            resp = requests.get(item_url, headers=headers, timeout=10)
            
            if resp.status_code == 404:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Anúncio '{clean_id}' não foi encontrado no Mercado Livre."
                )
            elif resp.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Erro na API do Mercado Livre (Status {resp.status_code}): {resp.text[:200]}"
                )

            data = resp.json()
            price = data.get("price")
            if price is None or float(price) <= 0:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"O anúncio '{clean_id}' não possui um preço válido cadastrado."
                )

            return MercadoLivreItemResponse(
                id=data.get("id", clean_id),
                title=data.get("title", ""),
                price=float(price),
                original_price=float(data["original_price"]) if data.get("original_price") is not None else None,
                currency_id=data.get("currency_id", "BRL"),
                permalink=data.get("permalink"),
                thumbnail=data.get("thumbnail"),
                status=data.get("status")
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erro ao consultar o item {clean_id} no Mercado Livre: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Erro interno ao consultar anúncio do Mercado Livre: {str(e)}"
            )


class GetMercadoLivrePriceByUrlUseCase:
    """
    Caso de uso para consultar o preço de um produto a partir de sua URL do Mercado Livre.
    """

    def __init__(self, item_use_case: Optional[GetMercadoLivreItemUseCase] = None):
        self.item_use_case = item_use_case or GetMercadoLivreItemUseCase()
        self.api_client = MercadoLivreAPIClient()

    def execute(self, url: str) -> MercadoLivrePriceResponse:
        item_id = self.api_client.extract_item_id(url)
        if not item_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A URL informada não é válida ou não possui um ID de anúncio do Mercado Livre (MLB...)."
            )

        item_data = self.item_use_case.execute(item_id)
        return MercadoLivrePriceResponse(
            item_id=item_data.id,
            title=item_data.title,
            price=item_data.price,
            original_price=item_data.original_price,
            currency_id=item_data.currency_id
        )
