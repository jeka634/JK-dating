from app.database.repositories.complaint import ComplaintRepository
from app.database.repositories.like import LikeRepository
from app.database.repositories.match import MatchRepository
from app.database.repositories.payment import PaymentRepository
from app.database.repositories.premium import PremiumRepository
from app.database.repositories.referral import ReferralRepository
from app.database.repositories.user import UserRepository

__all__ = [
    "UserRepository",
    "LikeRepository",
    "MatchRepository",
    "PremiumRepository",
    "PaymentRepository",
    "ComplaintRepository",
    "ReferralRepository",
]
