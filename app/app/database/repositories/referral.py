from datetime import datetime, timezone
from typing import Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Referral


class ReferralRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, referrer_id: int, referred_id: int) -> Referral:
        referral = Referral(referrer_id=referrer_id, referred_id=referred_id)
        self.session.add(referral)
        await self.session.flush()
        return referral

    async def get_by_referred_id(self, referred_id: int) -> Optional[Referral]:
        result = await self.session.execute(
            select(Referral).where(Referral.referred_id == referred_id)
        )
        return result.scalar_one_or_none()

    async def count_by_referrer(self, referrer_id: int) -> int:
        result = await self.session.execute(
            select(func.count(Referral.id)).where(
                Referral.referrer_id == referrer_id
            )
        )
        return result.scalar_one()

    async def grant_bonus(self, referral: Referral) -> Referral:
        referral.bonus_granted = True
        referral.bonus_granted_at = datetime.now(timezone.utc)
        await self.session.flush()
        return referral

    async def get_referrer_referrals(
        self, referrer_id: int
    ) -> Sequence[Referral]:
        result = await self.session.execute(
            select(Referral)
            .where(Referral.referrer_id == referrer_id)
            .order_by(Referral.created_at.desc())
        )
        return result.scalars().all()
