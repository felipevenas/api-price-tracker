import re
from urllib.parse import urlparse


def get_domain_name(url: str) -> str:
    """
    Retorna o nome do domínio limpo de uma URL (ex: mercadolivre.com.br)
    """
    try:
        parsed_url = urlparse(url)
        netloc = parsed_url.netloc or parsed_url.path
        # Remove "www."
        domain = re.sub(r'^www\.', '', netloc)
        return domain.lower()
    except Exception:
        return ""


def is_valid_url(url: str) -> bool:
    """
    Verifica se a URL possui formato HTTP ou HTTPS válido.
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc]) and result.scheme in ("http", "https")
    except Exception:
        return False
