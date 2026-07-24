from typing import Optional

from app.infra.clients.mercado_livre_api import MercadoLivreAPIClient
from app.domain.mercado_livre.schemas import MercadoLivreItemResponse, MercadoLivrePriceResponse
from app.domain.exceptions import NotFoundError, ServiceUnavailableError, UnprocessableError
from app.infra.logging.logger import logger


class GetMercadoLivreItemUseCase:
    """Consulta os detalhes de um item ou produto de catálogo pelo ID (MLB...)."""

    def __init__(self, api_client: Optional[MercadoLivreAPIClient] = None):
        self.api_client = api_client or MercadoLivreAPIClient()

    def execute(self, item_id: str) -> MercadoLivreItemResponse:
        clean_id = item_id.strip().upper()
        if not clean_id.startswith("MLB"):
            clean_id = f"MLB{clean_id}"

        if not self.api_client.get_access_token():
            raise ServiceUnavailableError(
                "Credenciais da API do Mercado Livre não configuradas ou token indisponível."
            )

        logger.info(f"Consultando item {clean_id} na API Oficial do Mercado Livre.")
        data = self.api_client.get_item_data(clean_id)

        if not data:
            raise NotFoundError(
                f"O anúncio ou produto de catálogo '{clean_id}' não foi encontrado na API do Mercado Livre."
            )

        price = data.get("price")
        if price is None or float(price) <= 0:
            raise UnprocessableError(
                f"O produto '{clean_id}' foi encontrado, porém não possui um preço ativo de venda."
            )

        return MercadoLivreItemResponse(
            id=data.get("id", clean_id),
            title=data.get("title") or data.get("name", ""),
            price=float(price),
            original_price=float(data["original_price"]) if data.get("original_price") is not None else None,
            currency_id=str(data.get("currency_id") or "BRL"),
            permalink=data.get("permalink"),
            thumbnail=data.get("thumbnail"),
            status=data.get("status"),
        )


class GetMercadoLivrePriceByUrlUseCase:
    """Consulta o preço de um produto a partir da sua URL do Mercado Livre."""

    def __init__(self, item_use_case: Optional[GetMercadoLivreItemUseCase] = None):
        self.item_use_case = item_use_case or GetMercadoLivreItemUseCase()
        self.api_client = MercadoLivreAPIClient()

    def execute(self, url: str) -> MercadoLivrePriceResponse:
        item_id = self.api_client.extract_item_id(url)
        if not item_id:
            raise UnprocessableError(
                "A URL informada não é válida ou não possui um ID de anúncio do Mercado Livre (MLB...)."
            )

        item = self.item_use_case.execute(item_id)
        return MercadoLivrePriceResponse(
            item_id=item.id,
            title=item.title,
            price=item.price,
            original_price=item.original_price,
            currency_id=item.currency_id,
        )
