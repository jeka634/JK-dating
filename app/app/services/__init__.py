from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.database.models import Language, User
from app.database.repositories.complaint import ComplaintRepository
from app.database.repositories.like import LikeRepository
from app.database.repositories.match import MatchRepository
from app.database.repositories.premium import PremiumRepository
from app.database.repositories.referral import ReferralRepository
from app.database.repositories.user import UserRepository
from app.utils.redis_cache import redis_cache
from app.utils.texts import format_profile, get_text


class UserService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repo = UserRepository(session)
        self.referral_repo = ReferralRepository(session)

    async def get_or_create(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        referral_code: Optional[str] = None,
    ) -> User:
        user = await self.user_repo.get_by_telegram_id(telegram_id)
        if user:
            return user

        referred_by_id = None
        if referral_code:
            referrer = await self.user_repo.get_by_referral_code(referral_code)
            if referrer and referrer.telegram_id != telegram_id:
                referred_by_id = referrer.id

        user = await self.user_repo.create(
            telegram_id=telegram_id,
            username=username,
            referred_by_id=referred_by_id,
        )

        if referred_by_id:
            await self.referral_repo.create(referred_by_id, user.id)

        return user

    async def complete_registration(self, user: User) -> User:
        user.is_registered = True
        return await self.user_repo.update(user)

    async def get_referral_stats(self, user: User) -> Tuple[str, int]:
        count = await self.referral_repo.count_by_referrer(user.id)
        return user.referral_code, count


class BrowseService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repo = UserRepository(session)
        self.like_repo = LikeRepository(session)

    async def get_next_profile(self, viewer: User) -> Optional[User]:
        liked_ids = await self.like_repo.get_liked_user_ids(viewer.id)
        exclude_ids = list(set(liked_ids))

        if not viewer.is_premium:
            redis_exclude = await redis_cache.get_browse_exclude(viewer.id)
            exclude_ids.extend(redis_exclude)
            exclude_ids = list(set(exclude_ids))

        profiles = await self.user_repo.get_profiles_for_browsing(
            viewer=viewer,
            exclude_ids=exclude_ids,
            limit=1,
        )
        if not profiles:
            if viewer.is_premium:
                await redis_cache.clear_browse_exclude(viewer.id)
                profiles = await self.user_repo.get_profiles_for_browsing(
                    viewer=viewer,
                    exclude_ids=liked_ids,
                    limit=1,
                )
            if not profiles:
                return None

        profile = profiles[0]
        await redis_cache.set_current_profile(viewer.id, profile.id)
        return profile

    async def skip_profile(self, viewer: User) -> None:
        current_id = await redis_cache.get_current_profile(viewer.id)
        if current_id:
            await redis_cache.add_browse_exclude(viewer.id, current_id)


class LikeService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.like_repo = LikeRepository(session)
        self.match_repo = MatchRepository(session)
        self.user_repo = UserRepository(session)

    async def can_like(self, user: User) -> bool:
        if user.is_premium:
            return True
        today_count = await self.like_repo.count_today_likes(user.id)
        return today_count < settings.free_daily_likes

    async def send_like(
        self, from_user: User, to_user_id: int
    ) -> Tuple[bool, Optional[User]]:
        existing = await self.like_repo.get_existing(from_user.id, to_user_id)
        if existing:
            return False, None

        if not await self.can_like(from_user):
            return False, None

        like = await self.like_repo.create(from_user.id, to_user_id)
        reverse = await self.like_repo.get_reverse(from_user.id, to_user_id)

        matched_user = None
        if reverse:
            await self.like_repo.mark_mutual(like)
            await self.like_repo.mark_mutual(reverse)
            existing_match = await self.match_repo.get_existing(
                from_user.id, to_user_id
            )
            if not existing_match:
                await self.match_repo.create(from_user.id, to_user_id)
            matched_user = await self.user_repo.get_by_id(to_user_id)

        return True, matched_user


class PremiumService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.user_repo = UserRepository(session)
        self.premium_repo = PremiumRepository(session)
        self.referral_repo = ReferralRepository(session)

    async def activate_premium(
        self, user: User, days: Optional[int] = None, source: str = "stars"
    ) -> User:
        duration = days or settings.premium_duration_days
        now = datetime.now(timezone.utc)

        if user.is_premium and user.premium_until and user.premium_until > now:
            expires_at = user.premium_until + timedelta(days=duration)
        else:
            expires_at = now + timedelta(days=duration)

        await self.premium_repo.deactivate_all(user.id)
        await self.premium_repo.create(user.id, expires_at, source)

        user.is_premium = True
        user.premium_until = expires_at
        await self.user_repo.update(user)

        referral = await self.referral_repo.get_by_referred_id(user.id)
        if referral and not referral.bonus_granted:
            referrer = await self.user_repo.get_by_id(referral.referrer_id)
            if referrer:
                bonus_days = settings.referral_bonus_days
                if referrer.is_premium and referrer.premium_until:
                    referrer.premium_until = referrer.premium_until + timedelta(
                        days=bonus_days
                    )
                else:
                    referrer.is_premium = True
                    referrer.premium_until = now + timedelta(days=bonus_days)
                await self.user_repo.update(referrer)
                await self.referral_repo.grant_bonus(referral)

        return user

    async def boost_profile(self, user: User) -> Tuple[bool, str]:
        if not user.is_premium:
            return False, "premium_required"

        now = datetime.now(timezone.utc)
        if user.profile_boosted_at:
            cooldown = user.profile_boosted_at + timedelta(hours=24)
            if cooldown > now:
                return False, "cooldown"

        user.profile_boosted_at = now
        await self.user_repo.update(user)
        return True, "boosted"

    async def toggle_hidden(self, user: User) -> User:
        if not user.is_premium:
            return user
        user.is_hidden = not user.is_hidden
        return await self.user_repo.update(user)

    async def check_premium_expiry(self, user: User) -> User:
        now = datetime.now(timezone.utc)
        if user.is_premium and user.premium_until and user.premium_until <= now:
            user.is_premium = False
            user.premium_until = None
            user.is_hidden = False
            await self.user_repo.update(user)
        return user


class ComplaintService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.complaint_repo = ComplaintRepository(session)

    async def file_complaint(
        self, reporter_id: int, reported_user_id: int, reason: str
    ) -> None:
        await self.complaint_repo.create(reporter_id, reported_user_id, reason)


class NotificationService:
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    async def notify_match(
        self, user: User, matched_user: User
    ) -> None:
        for recipient, partner in [(user, matched_user), (matched_user, user)]:
            text = get_text(
                "mutual_like_notify",
                recipient.language,
                name=partner.name or "",
                age=partner.age or "",
                city=partner.city or "",
            )
            try:
                await self.bot.send_message(recipient.telegram_id, text)
            except Exception:
                pass

    async def send_profile(
        self,
        chat_id: int,
        profile: User,
        language: Language,
        reply_markup: object = None,
    ) -> None:
        text = format_profile(profile, language)
        photos = sorted(profile.photos, key=lambda p: p.position)
        if photos:
            if len(photos) == 1:
                await self.bot.send_photo(
                    chat_id,
                    photo=photos[0].file_id,
                    caption=text,
                    reply_markup=reply_markup,
                )
            else:
                from aiogram.types import InputMediaPhoto

                media = [
                    InputMediaPhoto(
                        media=photos[0].file_id,
                        caption=text,
                    )
                ]
                for photo in photos[1:]:
                    media.append(InputMediaPhoto(media=photo.file_id))
                await self.bot.send_media_group(chat_id, media=media)
                if reply_markup:
                    await self.bot.send_message(
                        chat_id,
                        get_text("main_menu", language),
                        reply_markup=reply_markup,
                    )
        else:
            await self.bot.send_message(
                chat_id, text, reply_markup=reply_markup
            )
