import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.domain.mercado_livre.usecase import GetMercadoLivreItemUseCase, GetMercadoLivrePriceByUrlUseCase
from app.domain.mercado_livre.schemas import MercadoLivreItemResponse, MercadoLivrePriceResponse

client = TestClient(app)


class TestMercadoLivreDomain(unittest.TestCase):

    def test_get_item_usecase_success(self):
        mock_client_inst = MagicMock()
        mock_client_inst.get_access_token.return_value = "mock_token"
        mock_client_inst.get_item_data.return_value = {
            "id": "MLB3388701977",
            "title": "Placa de Vídeo RTX 4060",
            "price": 1899.90,
            "original_price": 2199.90,
            "currency_id": "BRL",
            "permalink": "https://produto.mercadolivre.com.br/MLB-3388701977",
            "thumbnail": "http://http2.mlstatic.com/D_123.jpg",
            "status": "active"
        }

        use_case = GetMercadoLivreItemUseCase(api_client=mock_client_inst)
        result = use_case.execute("MLB3388701977")

        self.assertIsInstance(result, MercadoLivreItemResponse)
        self.assertEqual(result.id, "MLB3388701977")
        self.assertEqual(result.price, 1899.90)

    @patch("app.domain.mercado_livre.usecase.GetMercadoLivreItemUseCase")
    def test_get_price_by_url_usecase_success(self, mock_item_uc_cls):
        mock_item_uc_inst = MagicMock()
        mock_item_uc_inst.execute.return_value = MercadoLivreItemResponse(
            id="MLB3388701977",
            title="Placa de Vídeo RTX 4060",
            price=1899.90,
            original_price=2199.90,
            currency_id="BRL"
        )

        use_case = GetMercadoLivrePriceByUrlUseCase(item_use_case=mock_item_uc_inst)
        result = use_case.execute("https://produto.mercadolivre.com.br/MLB-3388701977-placa-de-video-_JM")

        self.assertIsInstance(result, MercadoLivrePriceResponse)
        self.assertEqual(result.item_id, "MLB3388701977")
        self.assertEqual(result.price, 1899.90)

    @patch("app.domain.mercado_livre.routes.GetMercadoLivreItemUseCase")
    def test_route_get_item_by_id(self, mock_uc_cls):
        mock_uc_inst = MagicMock()
        mock_uc_inst.execute.return_value = MercadoLivreItemResponse(
            id="MLB3388701977",
            title="Placa de Vídeo RTX 4060",
            price=1899.90,
            currency_id="BRL"
        )
        mock_uc_cls.return_value = mock_uc_inst

        response = client.get("/api/v1/mercado-livre/items/MLB3388701977")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["id"], "MLB3388701977")
        self.assertEqual(data["price"], 1899.90)

    @patch("app.domain.mercado_livre.routes.GetMercadoLivrePriceByUrlUseCase")
    def test_route_get_price_by_url(self, mock_uc_cls):
        mock_uc_inst = MagicMock()
        mock_uc_inst.execute.return_value = MercadoLivrePriceResponse(
            item_id="MLB3388701977",
            title="Placa de Vídeo RTX 4060",
            price=1899.90,
            currency_id="BRL"
        )
        mock_uc_cls.return_value = mock_uc_inst

        response = client.get("/api/v1/mercado-livre/price?url=https://produto.mercadolivre.com.br/MLB-3388701977")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["item_id"], "MLB3388701977")
        self.assertEqual(data["price"], 1899.90)
