from datetime import datetime, timezone
from typing import Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Premium


class PremiumRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        user_id: int,
        expires_at: datetime,
        source: str = "stars",
    ) -> Premium:
        premium = Premium(
            user_id=user_id,
            expires_at=expires_at,
            source=source,
            is_active=True,
        )
        self.session.add(premium)
        await self.session.flush()
        return premium

    async def get_active(self, user_id: int) -> Optional[Premium]:
        now = datetime.now(timezone.utc)
        result = await self.session.execute(
            select(Premium)
            .where(
                Premium.user_id == user_id,
                Premium.is_active.is_(True),
                Premium.expires_at > now,
            )
            .order_by(Premium.expires_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def deactivate_all(self, user_id: int) -> None:
        result = await self.session.execute(
            select(Premium).where(
                Premium.user_id == user_id,
                Premium.is_active.is_(True),
            )
        )
        for record in result.scalars().all():
            record.is_active = False
        await self.session.flush()

    async def count_active(self) -> int:
        now = datetime.now(timezone.utc)
        result = await self.session.execute(
            select(func.count(Premium.id)).where(
                Premium.is_active.is_(True),
                Premium.expires_at > now,
            )
        )
        return result.scalar_one()

    async def get_history(
        self, user_id: int, limit: int = 10
    ) -> Sequence[Premium]:
        result = await self.session.execute(
            select(Premium)
            .where(Premium.user_id == user_id)
            .order_by(Premium.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
