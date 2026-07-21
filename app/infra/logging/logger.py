import logging
import sys
from contextvars import ContextVar
from typing import Optional

# Variáveis de contexto para armazenar Correlation ID (FastAPI) e Task ID (Celery)
correlation_id_ctx: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)
task_id_ctx: ContextVar[Optional[str]] = ContextVar("task_id", default=None)


class StructuredFilter(logging.Filter):
    """
    Filtro que injeta dinamicamente o Correlation ID e o Task ID do contexto
    atual em cada registro de log.
    """
    def filter(self, record):
        c_id = correlation_id_ctx.get()
        t_id = task_id_ctx.get()
        
        # Define identificadores padrões caso não estejam no contexto
        record.correlation_id = c_id if c_id else "N/A"
        record.task_id = t_id if t_id else "N/A"
        
        # Define o rótulo de contexto unificado [REQ-id] ou [TASK-id] ou [SYS]
        if c_id:
            record.context = f"REQ-{c_id[:8]}"
        elif t_id:
            record.context = f"TSK-{t_id[:8]}"
        else:
            record.context = "SYSTEM"
            
        return True


def setup_logging():
    """
    Configura o sistema de logging global da aplicação.
    Define formato de saída objetivo e limpo.
    """
    log_format = "[%(asctime)s] [%(levelname)s] [%(context)s] [%(filename)s:%(lineno)d] - %(message)s"
    
    # Logger raiz
    root_logger = logging.getLogger()
    
    # Se já tiver handlers configurados (evita duplicação no uvicorn)
    if root_logger.handlers:
        for handler in root_logger.handlers:
            root_logger.removeHandler(handler)
            
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")
    
    handler.setFormatter(formatter)
    handler.addFilter(StructuredFilter())
    
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)
    
    # Suprime logs excessivos de bibliotecas terceiras
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("selenium").setLevel(logging.WARNING)
    logging.getLogger("pika").setLevel(logging.WARNING)


# Inicializa o logging
setup_logging()
logger = logging.getLogger("price_monitor")
