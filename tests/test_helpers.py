from app.helpers.price_cleaner import clean_price_string
from app.helpers.url_parser import get_domain_name, is_valid_url


def test_price_cleaner_br_format():
    assert clean_price_string("R$ 1.599,90") == 1599.90
    assert clean_price_string("R$ 1.250") == 1250.00
    assert clean_price_string(" 89,99 ") == 89.99
    assert clean_price_string("R$ 10.250,55") == 10250.55


def test_price_cleaner_us_format():
    assert clean_price_string("1,599.90") == 1599.90
    assert clean_price_string("89.99") == 89.99


def test_price_cleaner_invalid():
    assert clean_price_string("") is None
    assert clean_price_string("Preço Sob Consulta") is None


def test_url_parser_domain_extraction():
    assert get_domain_name("https://www.mercadolivre.com.br/produto-xyz") == "mercadolivre.com.br"
    assert get_domain_name("http://produto.mercadolivre.com.br/MLB-1234") == "produto.mercadolivre.com.br"
    assert get_domain_name("mercadolivre.com") == "mercadolivre.com"


def test_url_parser_validation():
    assert is_valid_url("https://mercadolivre.com.br") is True
    assert is_valid_url("http://localhost:8000/health") is True
    assert is_valid_url("invalid_url_string") is False
    assert is_valid_url("ftp://ftp.example.com") is False
