# app/db/base.py
# Importa a Base declarativa e todos os modelos da aplicação
# para garantir que sejam registrados no Base.metadata antes do mapeamento de relacionamentos.

from app.db.base_class import Base  # noqa: F401
from app.domain.user.model import User  # noqa: F401
from app.domain.product.model import ProductMonitored  # noqa: F401
from app.domain.price_history.model import PriceHistory  # noqa: F401
from app.domain.audit_log.model import AuditLog  # noqa: F401
from app.domain.worker.model import WorkerJob  # noqa: F401
