import uuid
from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.api.endpoints.routes import api_router
from app.core.response import success_response, error_response
import app.db.base  # noqa: F401


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


# Exception Handler Global para capturar qualquer exceção não tratada na aplicação
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    from app.infra.logging.logger import logger
    logger.error(f"Erro não tratado capturado pelo handler global: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content=error_response(message="Ocorreu um erro interno no servidor", details=str(exc))
    )


# Exception Handler para capturar erros HTTP (como credenciais inválidas, recurso não encontrado de rotas)
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(message=exc.detail)
    )


# Exception Handler para capturar erros de validação de payload (RequestValidationError)
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content=error_response(
            message="Erro de validação nos dados enviados.",
            details=exc.errors()
        )
    )


# Endpoints de Saúde e Status básicos
@app.get("/")
async def root():
    return success_response(
        data={"version": "1.0.0"},
        message=f"{settings.PROJECT_NAME} está online"
    )


@app.get("/health", tags=["Health"])
async def health_check():
    # Em fases futuras, podemos verificar a saúde das conexões com BD e Redis aqui
    return success_response(
        data={
            "database": "connected_async",
            "cache": "redis_available"
        },
        message="Status de saúde verificado com sucesso"
    )
