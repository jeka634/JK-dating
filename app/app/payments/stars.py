import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.database.models import PaymentMethod, PaymentStatus, User
from app.database.repositories.payment import PaymentRepository
from app.services import PremiumService


class StarsPaymentService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.payment_repo = PaymentRepository(session)
        self.premium_service = PremiumService(session)

    def generate_payload(self, user_id: int) -> str:
        return f"premium_{user_id}_{uuid.uuid4().hex[:12]}"

    async def create_payment(self, user: User) -> tuple[int, str]:
        payload = self.generate_payload(user.id)
        payment = await self.payment_repo.create(
            user_id=user.id,
            amount=settings.premium_price_stars,
            payload=payload,
            method=PaymentMethod.STARS,
        )
        return payment.id, payload

    async def process_successful_payment(
        self,
        payload: str,
        telegram_charge_id: str,
        provider_charge_id: str,
        total_amount: int,
    ) -> Optional[User]:
        payment = await self.payment_repo.get_by_payload(payload)
        if not payment:
            return None

        if payment.status == PaymentStatus.COMPLETED:
            from app.database.repositories.user import UserRepository

            user_repo = UserRepository(self.session)
            return await user_repo.get_by_id(payment.user_id)

        await self.payment_repo.complete(
            payment, telegram_charge_id, provider_charge_id
        )

        from app.database.repositories.user import UserRepository

        user_repo = UserRepository(self.session)
        user = await user_repo.get_by_id(payment.user_id)
        if not user:
            return None

        return await self.premium_service.activate_premium(user, source="stars")
