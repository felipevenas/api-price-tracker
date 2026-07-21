import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.api.endpoints.routes import api_router

# Inicializa o FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Inclui as rotas unificadas v1
app.include_router(api_router, prefix=settings.API_V1_STR)

# Configuração de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especifique os domínios reais
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware para injetar Correlation ID nas requisições HTTP e no contexto
@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    from app.infra.logging.logger import logger, correlation_id_ctx
    
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    request.state.correlation_id = correlation_id
    
    # Define a variável de contexto para o ciclo de vida da requisição assíncrona
    token = correlation_id_ctx.set(correlation_id)
    
    logger.info(f"Início de requisição: {request.method} {request.url.path}")
    
    try:
        response = await call_next(request)
        logger.info(f"Fim de requisição: {request.method} {request.url.path} - Status: {response.status_code}")
        response.headers["X-Correlation-ID"] = correlation_id
        return response
    except Exception as e:
        logger.error(f"Erro não tratado na requisição: {str(e)}")
        raise
    finally:
        # Limpa o contexto ao finalizar a requisição
        correlation_id_ctx.reset(token)


# Endpoints de Saúde e Status básicos
@app.get("/")
async def root():
    return JSONResponse(
        content={
            "app": settings.PROJECT_NAME,
            "status": "online",
            "version": "1.0.0"
        }
    )


@app.get("/health", tags=["Health"])
async def health_check():
    # Em fases futuras, podemos verificar a saúde das conexões com BD e Redis aqui
    return JSONResponse(
        content={
            "status": "healthy",
            "database": "connected_async",
            "cache": "redis_available"
        }
    )
