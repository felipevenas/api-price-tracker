import uuid
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.domain.worker.repository import WorkerJobRepository
from app.domain.worker.model import JobStatus
from app.domain.worker.schemas import WorkerJobResponse
from app.core.response import success_response, error_response

router = APIRouter(prefix="/worker", tags=["Worker Jobs"])


@router.get(
    "/jobs",
    summary="Listar jobs do worker",
)
async def list_jobs(
    status: Optional[JobStatus] = Query(None, description="Filtrar por status"),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    """
    Lista os jobs recentes do worker, com filtro opcional por status.
    Retorna em ordem decrescente de enfileiramento.
    """
    try:
        repo = WorkerJobRepository(db)
        jobs = await repo.get_recent(status=status, limit=limit)
        return success_response(
            data=[WorkerJobResponse.model_validate(j) for j in jobs],
            message="Jobs recentes listados com sucesso"
        )
    except Exception as e:
        return error_response(message="Erro ao listar jobs recentes", details=str(e))


@router.get(
    "/jobs/{job_id}",
    summary="Obter detalhes de um job",
)
async def get_job(
    job_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna o detalhe de um job específico pelo seu ID.
    """
    try:
        repo = WorkerJobRepository(db)
        job = await repo.get_by_id(job_id)
        if not job:
            return error_response(message="Job não encontrado", details=f"Job com ID {job_id} não existe.")
        return success_response(
            data=WorkerJobResponse.model_validate(job),
            message="Detalhes do job recuperados com sucesso"
        )
    except Exception as e:
        return error_response(message="Erro ao recuperar detalhes do job", details=str(e))


@router.get(
    "/jobs/product/{product_id}",
    summary="Listar jobs associados a um produto",
)
async def list_jobs_by_product(
    product_id: uuid.UUID,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """
    Lista o histórico de jobs de um produto específico.
    """
    try:
        repo = WorkerJobRepository(db)
        jobs = await repo.get_by_product(product_id=product_id, limit=limit)
        return success_response(
            data=[WorkerJobResponse.model_validate(j) for j in jobs],
            message="Histórico de jobs do produto listado com sucesso"
        )
    except Exception as e:
        return error_response(message="Erro ao listar jobs do produto", details=str(e))
