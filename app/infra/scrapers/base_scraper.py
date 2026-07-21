from abc import ABC, abstractmethod
from typing import Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from app.core.config import settings


class BaseScraper(ABC):
    
    @abstractmethod
    def scrape(self, url: str) -> Optional[float]:
        """
        Método abstrato que deve ser implementado por scrapers concretos.
        Carrega a URL, raspa o preço, higieniza e retorna.
        """
        pass

    def get_chrome_options(self) -> Options:
        """
        Gera as opções do Chrome WebDriver otimizadas para scraping e anti-detecção.
        """
        chrome_options = Options()
        
        # Só ativa headless fora do Docker (se não houver hub remoto).
        # No Docker, a imagem Selenium Standalone tem display virtual Xvfb, permitindo modo headful.
        if not settings.SELENIUM_HUB_URL:
            chrome_options.add_argument("--headless=new")
            
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Desativa a flag de automação que aciona a maior parte dos anti-bots (Performance Optimizer)
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Otimizações de banda e processamento (desativa imagens para agilizar carregamento)
        chrome_options.add_argument("--blink-settings=imagesEnabled=false")
        chrome_options.add_argument("--disable-extensions")
        
        # User-agent realista para simular um browser de usuário real
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        return chrome_options

    def get_driver(self) -> webdriver.Remote | webdriver.Chrome:
        """
        Obtém uma instância do Selenium WebDriver aplicando patches contra detecção.
        """
        options = self.get_chrome_options()
        
        if settings.SELENIUM_HUB_URL:
            driver = webdriver.Remote(
                command_executor=settings.SELENIUM_HUB_URL,
                options=options
            )
        else:
            driver = webdriver.Chrome(options=options)
            
        # Oculta a flag navigator.webdriver injetando script em todas as novas páginas
        try:
            driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            })
        except Exception:
            # Em chamadas WebDriver remotas muito antigas o cdp_cmd pode falhar, ignoramos se ocorrer
            pass
            
        driver.set_page_load_timeout(25)
        driver.implicitly_wait(5)
        return driver
