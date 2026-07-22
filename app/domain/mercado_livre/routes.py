from fastapi import APIRouter, Query, status
from app.domain.mercado_livre.schemas import MercadoLivreItemResponse, MercadoLivrePriceResponse
from app.domain.mercado_livre.usecase import GetMercadoLivreItemUseCase, GetMercadoLivrePriceByUrlUseCase

router = APIRouter()


@router.get(
    "/items/{item_id}",
    response_model=MercadoLivreItemResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar detalhes de anúncio por ID (MLB...)",
    description="Consulta as informações detalhadas de um anúncio diretamente na API Oficial do Mercado Livre pelo seu ID de item (ex: MLB3388701977)."
)
def get_item_by_id(item_id: str):
    use_case = GetMercadoLivreItemUseCase()
    return use_case.execute(item_id)


@router.get(
    "/price",
    response_model=MercadoLivrePriceResponse,
    status_code=status.HTTP_200_OK,
    summary="Consultar preço de anúncio por URL do produto",
    description="Extrai o ID do anúncio a partir da URL do produto e consulta o seu preço atualizado em tempo real na API Oficial do Mercado Livre."
)
def get_price_by_url(url: str = Query(..., description="URL completa do produto no Mercado Livre")):
    use_case = GetMercadoLivrePriceByUrlUseCase()
    return use_case.execute(url)
