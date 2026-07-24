import unittest
from unittest.mock import patch, MagicMock

from app.infra.clients.mercado_livre_api import MercadoLivreAPIClient


class TestMercadoLivreAPIClient(unittest.TestCase):

    def test_extract_item_id_valid_urls(self):
        cases = [
            ("https://produto.mercadolivre.com.br/MLB-3388701977-placa-de-video-_JM", "MLB3388701977"),
            ("https://www.mercadolivre.com.br/p/MLB27564070", "MLB27564070"),
            ("https://www.mercadolivre.com.br/p/MLB-27564070", "MLB27564070"),
            ("https://www.mercadolivre.com.br/apple-iphone-15/p/MLB27564070", "MLB27564070"),
        ]
        for url, expected in cases:
            with self.subTest(url=url):
                self.assertEqual(MercadoLivreAPIClient.extract_item_id(url), expected)

    def test_extract_item_id_invalid_urls(self):
        for url in ["https://www.amazon.com.br/dp/B0CHWT49T3", "https://www.google.com", "", None]:
            with self.subTest(url=url):
                self.assertIsNone(MercadoLivreAPIClient.extract_item_id(url))

    @patch("app.infra.clients.mercado_livre_api.settings")
    @patch("app.infra.clients.mercado_livre_api.requests.post")
    def test_get_access_token_success(self, mock_post, mock_settings):
        mock_settings.MERCADO_LIVRE_CLIENT_ID = "test_id"
        mock_settings.MERCADO_LIVRE_CLIENT_SECRET = "test_secret"
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"access_token": "mocked_token"}
        mock_post.return_value = mock_resp

        token = MercadoLivreAPIClient().get_access_token()

        self.assertEqual(token, "mocked_token")
        mock_post.assert_called_once()

    @patch("app.infra.clients.mercado_livre_api.settings")
    def test_get_access_token_no_credentials(self, mock_settings):
        mock_settings.MERCADO_LIVRE_CLIENT_ID = None
        mock_settings.MERCADO_LIVRE_CLIENT_SECRET = None
        self.assertIsNone(MercadoLivreAPIClient().get_access_token())

    @patch.object(MercadoLivreAPIClient, "get_access_token")
    @patch("app.infra.clients.mercado_livre_api.requests.get")
    def test_get_item_price_success(self, mock_get, mock_token):
        mock_token.return_value = "mocked_token"
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "id": "MLB3388701977",
            "title": "Placa de Vídeo RTX 4060",
            "price": 1899.90,
        }
        mock_get.return_value = mock_resp

        price = MercadoLivreAPIClient().get_item_price(
            "https://produto.mercadolivre.com.br/MLB-3388701977-placa-de-video-_JM"
        )
        self.assertEqual(price, 1899.90)
