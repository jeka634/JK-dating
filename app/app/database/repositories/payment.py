from datetime import datetime, timezone
from typing import Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Payment, PaymentMethod, PaymentStatus


class PaymentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        user_id: int,
        amount: int,
        payload: str,
        method: PaymentMethod = PaymentMethod.STARS,
    ) -> Payment:
        payment = Payment(
            user_id=user_id,
            amount=amount,
            method=method,
            status=PaymentStatus.PENDING,
            payload=payload,
        )
        self.session.add(payment)
        await self.session.flush()
        return payment

    async def get_by_id(self, payment_id: int) -> Optional[Payment]:
        result = await self.session.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        return result.scalar_one_or_none()

    async def get_by_payload(self, payload: str) -> Optional[Payment]:
        result = await self.session.execute(
            select(Payment).where(Payment.payload == payload)
        )
        return result.scalar_one_or_none()

    async def complete(
        self,
        payment: Payment,
        telegram_charge_id: str,
        provider_charge_id: str,
    ) -> Payment:
        payment.status = PaymentStatus.COMPLETED
        payment.telegram_payment_charge_id = telegram_charge_id
        payment.provider_payment_charge_id = provider_charge_id
        payment.completed_at = datetime.now(timezone.utc)
        await self.session.flush()
        return payment

    async def count_all(self) -> int:
        result = await self.session.execute(select(func.count(Payment.id)))
        return result.scalar_one()

    async def count_completed(self) -> int:
        result = await self.session.execute(
            select(func.count(Payment.id)).where(
                Payment.status == PaymentStatus.COMPLETED
            )
        )
        return result.scalar_one()

    async def total_revenue(self) -> int:
        result = await self.session.execute(
            select(func.coalesce(func.sum(Payment.amount), 0)).where(
                Payment.status == PaymentStatus.COMPLETED
            )
        )
        return result.scalar_one()

    async def get_recent(
        self, offset: int = 0, limit: int = 50
    ) -> Sequence[Payment]:
        result = await self.session.execute(
            select(Payment)
            .order_by(Payment.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_user_payments(
        self, user_id: int, limit: int = 10
    ) -> Sequence[Payment]:
        result = await self.session.execute(
            select(Payment)
            .where(Payment.user_id == user_id)
            .order_by(Payment.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
