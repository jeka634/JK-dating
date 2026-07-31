from typing import Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Complaint, ComplaintStatus


class ComplaintRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        reporter_id: int,
        reported_user_id: int,
        reason: str,
    ) -> Complaint:
        complaint = Complaint(
            reporter_id=reporter_id,
            reported_user_id=reported_user_id,
            reason=reason,
            status=ComplaintStatus.PENDING,
        )
        self.session.add(complaint)
        await self.session.flush()
        return complaint

    async def get_by_id(self, complaint_id: int) -> Optional[Complaint]:
        result = await self.session.execute(
            select(Complaint).where(Complaint.id == complaint_id)
        )
        return result.scalar_one_or_none()

    async def get_pending(
        self, offset: int = 0, limit: int = 50
    ) -> Sequence[Complaint]:
        result = await self.session.execute(
            select(Complaint)
            .where(Complaint.status == ComplaintStatus.PENDING)
            .order_by(Complaint.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_all(
        self, offset: int = 0, limit: int = 50
    ) -> Sequence[Complaint]:
        result = await self.session.execute(
            select(Complaint)
            .order_by(Complaint.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()

    async def resolve(
        self,
        complaint: Complaint,
        status: ComplaintStatus,
        admin_note: Optional[str] = None,
    ) -> Complaint:
        from datetime import datetime, timezone

        complaint.status = status
        complaint.admin_note = admin_note
        complaint.resolved_at = datetime.now(timezone.utc)
        await self.session.flush()
        return complaint

    async def count_pending(self) -> int:
        result = await self.session.execute(
            select(func.count(Complaint.id)).where(
                Complaint.status == ComplaintStatus.PENDING
            )
        )
        return result.scalar_one()
