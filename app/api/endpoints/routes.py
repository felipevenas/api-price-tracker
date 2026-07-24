from fastapi import APIRouter
from app.domain.auth.routes import router as auth_router
from app.domain.user.routes import router as user_router
from app.domain.product.routes import router as product_router
from app.domain.mercado_livre.routes import router as mercado_livre_router
from app.domain.worker.routes import router as worker_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["Autenticação"])
api_router.include_router(user_router, prefix="/users", tags=["Usuários"])
api_router.include_router(product_router, prefix="/products", tags=["Produtos"])
api_router.include_router(mercado_livre_router, prefix="/mercado-livre", tags=["Mercado Livre"])
api_router.include_router(worker_router, prefix="/worker", tags=["Worker Jobs"])
