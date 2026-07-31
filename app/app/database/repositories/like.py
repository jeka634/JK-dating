from datetime import datetime, timezone
from typing import List, Optional, Sequence

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models import Like, User


class LikeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, from_user_id: int, to_user_id: int) -> Like:
        like = Like(from_user_id=from_user_id, to_user_id=to_user_id)
        self.session.add(like)
        await self.session.flush()
        return like

    async def get_existing(self, from_user_id: int, to_user_id: int) -> Optional[Like]:
        result = await self.session.execute(
            select(Like).where(
                Like.from_user_id == from_user_id,
                Like.to_user_id == to_user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_reverse(self, from_user_id: int, to_user_id: int) -> Optional[Like]:
        result = await self.session.execute(
            select(Like).where(
                Like.from_user_id == to_user_id,
                Like.to_user_id == from_user_id,
            )
        )
        return result.scalar_one_or_none()

    async def mark_mutual(self, like: Like) -> Like:
        like.is_mutual = True
        await self.session.flush()
        return like

    async def count_today_likes(self, user_id: int) -> int:
        today_start = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        result = await self.session.execute(
            select(func.count(Like.id)).where(
                Like.from_user_id == user_id,
                Like.created_at >= today_start,
            )
        )
        return result.scalar_one()

    async def get_received_likes(
        self, user_id: int, offset: int = 0, limit: int = 20
    ) -> Sequence[Like]:
        result = await self.session.execute(
            select(Like)
            .options(
                selectinload(Like.from_user).selectinload(User.photos),
            )
            .where(Like.to_user_id == user_id)
            .order_by(Like.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_sent_likes_history(
        self, user_id: int, offset: int = 0, limit: int = 20
    ) -> Sequence[Like]:
        result = await self.session.execute(
            select(Like)
            .options(
                selectinload(Like.to_user).selectinload(User.photos),
            )
            .where(Like.from_user_id == user_id)
            .order_by(Like.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_liked_user_ids(self, user_id: int) -> List[int]:
        result = await self.session.execute(
            select(Like.to_user_id).where(Like.from_user_id == user_id)
        )
        return list(result.scalars().all())

    async def count_received(self, user_id: int) -> int:
        result = await self.session.execute(
            select(func.count(Like.id)).where(Like.to_user_id == user_id)
        )
        return result.scalar_one()
