from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.audit_log.model import AuditLog


class AuditLogRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, audit_log: AuditLog) -> AuditLog:
        self.db.add(audit_log)
        await self.db.flush()
        return audit_log
