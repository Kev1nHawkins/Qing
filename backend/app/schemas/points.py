from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import BadgeRuleType
from app.schemas.common import Timestamped


class PointRead(Timestamped):
    user_id: int
    amount: int
    balance_after: int
    reason_type: str
    reason_id: int | None
    business_key: str
    description: str


class PointRedeemRequest(BaseModel):
    product_code: str = Field(min_length=1, max_length=80)
    redemption_id: str = Field(min_length=8, max_length=80)


class BadgeCreate(BaseModel):
    code: str = Field(min_length=1, max_length=80)
    name: str = Field(min_length=1, max_length=80)
    description: str = Field(max_length=500)
    icon_url: str | None = None
    rule_type: BadgeRuleType = BadgeRuleType.MANUAL
    rule_value: int = Field(default=1, ge=1)


class BadgeRead(Timestamped):
    code: str
    name: str
    description: str
    icon_url: str | None
    rule_type: str
    rule_value: int
    is_active: bool


class UserBadgeRead(Timestamped):
    user_id: int
    badge_id: int
    awarded_at: datetime
    reason: str


class AdminPostReview(BaseModel):
    status: str = Field(pattern=r"^(PUBLISHED|REJECTED|OFFLINE)$")


class AdminPointAdjust(BaseModel):
    amount: int = Field(ge=-10000, le=10000)
    description: str = Field(min_length=1, max_length=255)
