"""
Base e Factory para scrapers baseados em Selenium WebDriver.

- SeleniumBaseScraper: classe base abstrata com utilitários de Chrome/WebDriver.
  Scrapers concretos herdam esta classe e implementam scrape().

- ScraperFactory: localiza e instancia o scraper correto pelo domínio da URL.
  Mercado Livre NÃO é registrado aqui — é integrado diretamente via API Oficial.

Exemplo de uso futuro:
    class AmazonScraper(SeleniumBaseScraper):
        def scrape(self, url: str) -> Optional[float]:
            driver = self.get_driver()
            ...

    ScraperFactory.register("amazon.com.br", AmazonScraper)
"""

from abc import abstractmethod
from typing import Dict, Optional, Type

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from app.core.config import settings
from app.infra.scrapers.base_scraper import BaseScraper
from app.infra.logging.logger import logger


class SeleniumBaseScraper(BaseScraper):
    """
    Classe base para scrapers que utilizam Selenium WebDriver.
    Fornece get_chrome_options() e get_driver() como utilitários reutilizáveis.
    Subclasses devem implementar apenas scrape().
    """

    @abstractmethod
    def scrape(self, url: str) -> Optional[float]:
        pass

    def get_chrome_options(self) -> Options:
        """Opções do Chrome otimizadas para scraping e anti-detecção."""
        opts = Options()

        if not settings.SELENIUM_HUB_URL:
            opts.add_argument("--headless=new")

        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--window-size=1920,1080")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_experimental_option("excludeSwitches", ["enable-automation"])
        opts.add_experimental_option("useAutomationExtension", False)
        opts.add_argument("--blink-settings=imagesEnabled=false")
        opts.add_argument("--disable-extensions")
        opts.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        )
        opts.add_argument("--lang=pt-BR,pt")
        return opts

    def get_driver(self) -> webdriver.Remote | webdriver.Chrome:
        """Instância do WebDriver com patch anti-detecção aplicado."""
        options = self.get_chrome_options()

        if settings.SELENIUM_HUB_URL:
            driver = webdriver.Remote(command_executor=settings.SELENIUM_HUB_URL, options=options)
            try:
                driver.command_executor._commands["executeCdpCommand"] = (
                    "POST", "/session/$sessionId/chromium/send_command_and_get_result"
                )
                driver.execute("executeCdpCommand", {
                    "cmd": "Page.addScriptToEvaluateOnNewDocument",
                    "params": {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"},
                })
            except Exception as err:
                logger.warning(f"Falha ao injetar CDP no Remote WebDriver: {err}")
        else:
            driver = webdriver.Chrome(options=options)
            try:
                driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                    "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
                })
            except Exception:
                pass

        driver.set_page_load_timeout(25)
        driver.implicitly_wait(5)
        return driver


class ScraperFactory:
    """
    Factory de scrapers Selenium indexada por domínio.
    Retorna a instância concreta do scraper adequado para a URL fornecida.
    """

    _registry: Dict[str, Type[SeleniumBaseScraper]] = {
        # Registre futuros scrapers aqui:
        # "amazon.com.br": AmazonScraper,
    }

    @classmethod
    def get_scraper(cls, url: str) -> SeleniumBaseScraper:
        from app.helpers.url_parser import get_domain_name
        domain = get_domain_name(url)
        for key, scraper_class in cls._registry.items():
            if key in domain:
                return scraper_class()
        raise ValueError(
            f"Nenhum scraper Selenium registrado para o domínio '{domain}'. "
            "Adicione-o em ScraperFactory._registry ou verifique se o domínio "
            "utiliza integração via API (ex: Mercado Livre)."
        )

    @classmethod
    def supports(cls, url: str) -> bool:
        """Retorna True se o domínio possui um scraper Selenium registrado."""
        from app.helpers.url_parser import get_domain_name
        domain = get_domain_name(url)
        return any(key in domain for key in cls._registry)
