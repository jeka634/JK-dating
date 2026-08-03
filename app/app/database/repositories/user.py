import secrets
from datetime import datetime, timezone
from typing import List, Optional, Sequence

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models import Gender, Language, LookingFor, Photo, User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        result = await self.session.execute(
            select(User)
            .options(selectinload(User.photos))
            .where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> Optional[User]:
        result = await self.session.execute(
            select(User)
            .options(selectinload(User.photos))
            .where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_referral_code(self, code: str) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.referral_code == code)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        referred_by_id: Optional[int] = None,
    ) -> User:
        user = User(
            telegram_id=telegram_id,
            username=username,
            referral_code=secrets.token_urlsafe(8),
            referred_by_id=referred_by_id,
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def update(self, user: User) -> User:
        await self.session.flush()
        return user

    async def reset_profile(self, user_id: int) -> None:
        """Полный сброс анкеты: очищает поля и удаляет фото."""
        user = await self.get_by_id(user_id)
        if user is None:
            return
        user.name = None
        user.age = None
        user.gender = None
        user.looking_for = None
        user.city = None
        user.description = None
        user.is_registered = False
        await self.delete_photos(user_id)
        await self.session.flush()

    async def add_photo(
        self,
        user_id: int,
        file_id: str,
        file_unique_id: str,
        position: int,
    ) -> Photo:
        photo = Photo(
            user_id=user_id,
            file_id=file_id,
            file_unique_id=file_unique_id,
            position=position,
        )
        self.session.add(photo)
        await self.session.flush()
        return photo

    async def delete_photos(self, user_id: int) -> None:
        result = await self.session.execute(
            select(Photo).where(Photo.user_id == user_id)
        )
        for photo in result.scalars().all():
            await self.session.delete(photo)
        await self.session.flush()

    async def get_profiles_for_browsing(
        self,
        viewer: User,
        exclude_ids: List[int],
        limit: int = 1,
    ) -> Sequence[User]:
        conditions = [
            User.is_registered.is_(True),
            User.is_blocked.is_(False),
            User.id != viewer.id,
            User.id.notin_(exclude_ids) if exclude_ids else True,
        ]

        if viewer.looking_for == LookingFor.MALE:
            conditions.append(User.gender == Gender.MALE)
        elif viewer.looking_for == LookingFor.FEMALE:
            conditions.append(User.gender == Gender.FEMALE)

        if viewer.is_premium and viewer.filter_age_min:
            conditions.append(User.age >= viewer.filter_age_min)
        if viewer.is_premium and viewer.filter_age_max:
            conditions.append(User.age <= viewer.filter_age_max)
        if viewer.is_premium and viewer.filter_city:
            conditions.append(User.city.ilike(f"%{viewer.filter_city}%"))

        if not viewer.is_premium:
            conditions.append(User.is_hidden.is_(False))

        # Female profiles must be verified to appear in browse
        conditions.append(
            or_(
                User.gender != Gender.FEMALE,
                User.is_verified.is_(True),
            )
        )

        gender_match = or_(
            User.looking_for == LookingFor.ALL,
            and_(
                viewer.gender == Gender.MALE,
                User.looking_for == LookingFor.MALE,
            ),
            and_(
                viewer.gender == Gender.FEMALE,
                User.looking_for == LookingFor.FEMALE,
            ),
            and_(
                viewer.gender == Gender.OTHER,
                User.looking_for == LookingFor.ALL,
            ),
        )
        conditions.append(gender_match)

        order_by = [
            User.profile_boosted_at.desc().nullslast(),
            User.created_at.desc(),
        ]

        result = await self.session.execute(
            select(User)
            .options(selectinload(User.photos))
            .where(*conditions)
            .order_by(*order_by)
            .limit(limit)
        )
        return result.scalars().all()

    async def count_all(self) -> int:
        result = await self.session.execute(select(func.count(User.id)))
        return result.scalar_one()

    async def count_premium(self) -> int:
        now = datetime.now(timezone.utc)
        result = await self.session.execute(
            select(func.count(User.id)).where(
                User.is_premium.is_(True),
                or_(User.premium_until.is_(None), User.premium_until > now),
            )
        )
        return result.scalar_one()

    async def get_all_paginated(
        self, offset: int = 0, limit: int = 50
    ) -> Sequence[User]:
        result = await self.session.execute(
            select(User)
            .options(selectinload(User.photos))
            .order_by(User.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()

    async def delete_user(self, user_id: int) -> bool:
        user = await self.get_by_id(user_id)
        if not user:
            return False
        await self.session.delete(user)
        await self.session.flush()
        return True

    async def set_blocked(self, user_id: int, blocked: bool) -> Optional[User]:
        user = await self.get_by_id(user_id)
        if not user:
            return None
        user.is_blocked = blocked
        await self.session.flush()
        return user

    async def set_language(self, user: User, language: Language) -> User:
        user.language = language
        await self.session.flush()
        return user
