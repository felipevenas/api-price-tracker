from fastapi import APIRouter, Query
from app.domain.exceptions import NotFoundError, ServiceUnavailableError, UnprocessableError
from app.domain.mercado_livre.usecase import GetMercadoLivreItemUseCase, GetMercadoLivrePriceByUrlUseCase
from app.core.response import success_response, error_response

router = APIRouter()


@router.get(
    "/items/{item_id}",
    summary="Consultar detalhes de anúncio por ID (MLB...)",
)
def get_item_by_id(item_id: str):
    """Consulta informações de um anúncio na API Oficial do Mercado Livre pelo ID."""
    try:
        result = GetMercadoLivreItemUseCase().execute(item_id)
        return success_response(data=result, message="Item consultado com sucesso")
    except (NotFoundError, UnprocessableError, ServiceUnavailableError) as e:
        return error_response(message="Erro ao consultar detalhes do item no Mercado Livre", details=str(e))
    except Exception as e:
        return error_response(message="Erro inesperado ao consultar item", details=str(e))


@router.get(
    "/price",
    summary="Consultar preço de anúncio por URL",
)
def get_price_by_url(url: str = Query(..., description="URL completa do produto no Mercado Livre")):
    """Extrai o ID da URL e consulta o preço atualizado na API Oficial do Mercado Livre."""
    try:
        result = GetMercadoLivrePriceByUrlUseCase().execute(url)
        return success_response(data=result, message="Preço consultado com sucesso")
    except (NotFoundError, UnprocessableError, ServiceUnavailableError) as e:
        return error_response(message="Erro ao obter preço através da URL no Mercado Livre", details=str(e))
    except Exception as e:
        return error_response(message="Erro inesperado ao consultar preço por URL", details=str(e))
