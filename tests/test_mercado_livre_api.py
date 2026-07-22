import unittest
from unittest.mock import patch, MagicMock
from app.infra.clients.mercado_livre_api import MercadoLivreAPIClient
from app.infra.scrapers.mercado_livre import MercadoLivreScraper


class TestMercadoLivreAPIClient(unittest.TestCase):

    def test_extract_item_id_valid_urls(self):
        urls_and_expected = [
            ("https://produto.mercadolivre.com.br/MLB-3388701977-placa-de-video-_JM", "MLB3388701977"),
            ("https://www.mercadolivre.com.br/p/MLB27564070", "MLB27564070"),
            ("https://www.mercadolivre.com.br/p/MLB-27564070", "MLB27564070"),
            ("https://www.mercadolivre.com.br/apple-iphone-15/p/MLB27564070", "MLB27564070"),
        ]
        for url, expected_id in urls_and_expected:
            extracted = MercadoLivreAPIClient.extract_item_id(url)
            self.assertEqual(extracted, expected_id)

    def test_extract_item_id_invalid_urls(self):
        invalid_urls = [
            "https://www.amazon.com.br/dp/B0CHWT49T3",
            "https://www.google.com",
            "",
            None
        ]
        for url in invalid_urls:
            self.assertIsNone(MercadoLivreAPIClient.extract_item_id(url))

    @patch("app.infra.clients.mercado_livre_api.settings")
    @patch("app.infra.clients.mercado_livre_api.requests.post")
    def test_get_access_token_success(self, mock_post, mock_settings):
        mock_settings.MERCADO_LIVRE_CLIENT_ID = "test_client_id"
        mock_settings.MERCADO_LIVRE_CLIENT_SECRET = "test_client_secret"

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"access_token": "mocked_access_token_123"}
        mock_post.return_value = mock_resp

        client = MercadoLivreAPIClient()
        token = client.get_access_token()

        self.assertEqual(token, "mocked_access_token_123")
        mock_post.assert_called_once()

    @patch("app.infra.clients.mercado_livre_api.settings")
    def test_get_access_token_no_credentials(self, mock_settings):
        mock_settings.MERCADO_LIVRE_CLIENT_ID = None
        mock_settings.MERCADO_LIVRE_CLIENT_SECRET = None

        client = MercadoLivreAPIClient()
        self.assertIsNone(client.get_access_token())

    @patch.object(MercadoLivreAPIClient, "get_access_token")
    @patch("app.infra.clients.mercado_livre_api.requests.get")
    def test_get_item_price_success(self, mock_get, mock_token):
        mock_token.return_value = "mocked_token"
        
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "id": "MLB3388701977",
            "title": "Placa de Vídeo RTX 4060",
            "price": 1899.90
        }
        mock_get.return_value = mock_resp

        client = MercadoLivreAPIClient()
        price = client.get_item_price("https://produto.mercadolivre.com.br/MLB-3388701977-placa-de-video-_JM")

        self.assertEqual(price, 1899.90)

    @patch("app.infra.scrapers.mercado_livre.GetMercadoLivrePriceByUrlUseCase")
    def test_scraper_uses_api_first(self, mock_uc_cls):
        mock_uc_inst = MagicMock()
        mock_uc_inst.execute.return_value = MagicMock(price=1999.90)
        mock_uc_cls.return_value = mock_uc_inst

        scraper = MercadoLivreScraper()
        price = scraper.scrape("https://produto.mercadolivre.com.br/MLB-3388701977-placa-de-video-_JM")

        self.assertEqual(price, 1999.90)
        mock_uc_inst.execute.assert_called_once()

