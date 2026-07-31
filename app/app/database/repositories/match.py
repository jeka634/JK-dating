from typing import Optional

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Match


class MatchRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, user1_id: int, user2_id: int) -> Match:
        first_id = min(user1_id, user2_id)
        second_id = max(user1_id, user2_id)
        match = Match(user1_id=first_id, user2_id=second_id)
        self.session.add(match)
        await self.session.flush()
        return match

    async def get_existing(self, user1_id: int, user2_id: int) -> Optional[Match]:
        first_id = min(user1_id, user2_id)
        second_id = max(user1_id, user2_id)
        result = await self.session.execute(
            select(Match).where(
                Match.user1_id == first_id,
                Match.user2_id == second_id,
            )
        )
        return result.scalar_one_or_none()

    async def count_all(self) -> int:
        from sqlalchemy import func

        result = await self.session.execute(select(func.count(Match.id)))
        return result.scalar_one()

    async def get_user_matches(self, user_id: int) -> list[Match]:
        result = await self.session.execute(
            select(Match).where(
                or_(Match.user1_id == user_id, Match.user2_id == user_id)
            )
        )
        return list(result.scalars().all())
