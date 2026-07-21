import re
from typing import Optional


def clean_price_string(price_str: str) -> Optional[float]:
    """
    Higieniza uma string de preço bruta e converte para float.
    Exemplos de entrada suportados:
      - "R$ 1.599,90" -> 1599.90
      - "R$1.599" -> 1599.00
      - "1599,00" -> 1599.00
      - " 1.250,00 " -> 1250.00
    """
    if not price_str:
        return None
        
    try:
        # Remove espaços nas pontas
        text = price_str.strip()
        
        # Remove caracteres que não são números, pontos ou vírgulas
        # Mantém apenas dígitos, '.' e ','
        text = re.sub(r'[^\d.,]', '', text)
        
        if not text:
            return None
            
        # Caso 1: Tem ponto e vírgula (Ex: "1.590,99")
        if "." in text and "," in text:
            # Padrão brasileiro: ponto de milhar, vírgula decimal
            if text.find(".") < text.find(","):
                text = text.replace(".", "")
                text = text.replace(",", ".")
            # Padrão americano: vírgula de milhar, ponto decimal
            else:
                text = text.replace(",", "")
        
        # Caso 2: Tem apenas vírgula (Ex: "1590,99")
        elif "," in text:
            text = text.replace(",", ".")
            
        # Caso 3: Tem apenas ponto (Ex: "1.590" ou "1590.99")
        elif "." in text:
            parts = text.split(".")
            # Se a última parte tem 3 dígitos, provavelmente é milhar (Ex: 1.000 -> 1000)
            if len(parts[-1]) == 3 and len(parts) > 1:
                text = text.replace(".", "")
            # Caso contrário, tratamos o ponto como decimal (Ex: 1590.99)
            else:
                pass
                
        return float(text)
    except Exception:
        return None
