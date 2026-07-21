from typing import Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from app.infra.scrapers.base_scraper import BaseScraper
from app.helpers.price_cleaner import clean_price_string
from app.infra.logging.logger import logger


class MercadoLivreScraper(BaseScraper):
    
    def scrape(self, url: str) -> Optional[float]:
        """
        Acessa a página do produto do Mercado Livre e extrai o preço.
        Tenta primeiro via Meta tags estruturadas (mais resiliente) e,
        caso falhe, tenta via seletores visuais do DOM de catálogo e anúncios.
        """
        driver = self.get_driver()
        try:
            logger.info(f"Navegando para a URL do produto...")
            driver.get(url)
            
            # Aguarda até 10 segundos para que os elementos principais da oferta sejam carregados
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "meta[itemprop='price'], #price .andes-money-amount"))
                )
            except Exception as wait_err:
                logger.warning(f"Timeout ao aguardar carregamento dos seletores de preço: {str(wait_err)}. Tentando raspar mesmo assim.")

            # Estratégia 1: Meta-tags estruturadas itemprop de Ofertas (Altamente estável)
            meta_selectors = [
                "span[itemprop='offers'] meta[itemprop='price']",
                "meta[itemprop='price']",
                "meta[property='og:price:amount']"
            ]
            
            for selector in meta_selectors:
                try:
                    element = driver.find_element(By.CSS_SELECTOR, selector)
                    content = element.get_attribute("content")
                    if content:
                        price = clean_price_string(content)
                        if price and price > 0:
                            logger.info(f"Preço obtido com sucesso via Meta-tag '{selector}': R$ {price:.2f}")
                            return price
                except Exception:
                    continue

            # Estratégia 2: Seletores de DOM Visual (Focado no bloco de preço #price ou cabeçalho)
            dom_price_configs = [
                # Bloco de preço de catálogo: fração e centavos
                {
                    "fraction": "#price .andes-money-amount:not(.ui-pdp-price__original-value) .andes-money-amount__fraction",
                    "cents": "#price .andes-money-amount:not(.ui-pdp-price__original-value) .andes-money-amount__cents"
                },
                # Bloco de preço padrão de anúncio: fração e centavos
                {
                    "fraction": ".ui-pdp-price__part:not(.ui-pdp-price__original-value) .andes-money-amount__fraction",
                    "cents": ".ui-pdp-price__part:not(.ui-pdp-price__original-value) .andes-money-amount__cents"
                }
            ]
            
            for config in dom_price_configs:
                try:
                    fraction_el = driver.find_element(By.CSS_SELECTOR, config["fraction"])
                    if fraction_el:
                        fraction_text = fraction_el.text.strip()
                        cents_text = "00"
                        
                        # Tenta buscar centavos se o seletor estiver definido
                        try:
                            cents_el = driver.find_element(By.CSS_SELECTOR, config["cents"])
                            if cents_el:
                                cents_text = cents_el.text.strip()
                        except Exception:
                            pass
                            
                        full_price_text = f"{fraction_text},{cents_text}"
                        price = clean_price_string(full_price_text)
                        if price and price > 0:
                            logger.info(f"Preço obtido com sucesso via DOM visual: R$ {price:.2f}")
                            return price
                except Exception:
                    continue
            
            # Se tudo falhar, tenta pegar qualquer elemento andes-money-amount que não seja original
            try:
                fallback_el = driver.find_element(By.CSS_SELECTOR, ".andes-money-amount:not(.ui-pdp-price__original-value)")
                price = clean_price_string(fallback_el.text)
                if price and price > 0:
                    logger.info(f"Preço obtido via fallback geral de classe: R$ {price:.2f}")
                    return price
            except Exception:
                pass

            logger.error("Todos os seletores de preço falharam na página do Mercado Livre.")
            return None
            
        except Exception as e:
            raise RuntimeError(f"Erro ao extrair preço do Mercado Livre: {str(e)}")
            
        finally:
            driver.quit()
