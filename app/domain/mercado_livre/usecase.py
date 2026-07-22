from typing import Optional
from fastapi import HTTPException, status
from app.infra.clients.mercado_livre_api import MercadoLivreAPIClient
from app.domain.mercado_livre.schemas import MercadoLivreItemResponse, MercadoLivrePriceResponse
from app.infra.logging.logger import logger


class GetMercadoLivreItemUseCase:
    """
    Caso de uso para consultar os detalhes completos de um item ou produto de catálogo no Mercado Livre pelo seu ID (MLB...).
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
                detail="Credenciais da API do Mercado Livre não configuradas no .env ou token OAuth indisponível."
            )

        logger.info(f"Executando GetMercadoLivreItemUseCase para o ID: {clean_id}")
        data = self.api_client.get_item_data(clean_id)

        if not data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"O anúncio ou produto de catálogo '{clean_id}' não foi encontrado na API Oficial do Mercado Livre."
            )

        price = data.get("price")
        if price is None or float(price) <= 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"O anúncio ou produto '{clean_id}' foi encontrado, porém não possui um preço ativo de venda no momento."
            )

        currency = data.get("currency_id") or "BRL"

        return MercadoLivreItemResponse(
            id=data.get("id", clean_id),
            title=data.get("title") or data.get("name", ""),
            price=float(price),
            original_price=float(data["original_price"]) if data.get("original_price") is not None else None,
            currency_id=str(currency),
            permalink=data.get("permalink"),
            thumbnail=data.get("thumbnail"),
            status=data.get("status")
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
