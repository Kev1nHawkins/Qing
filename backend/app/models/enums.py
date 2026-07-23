from enum import StrEnum


class PublishStatus(StrEnum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    OFFLINE = "OFFLINE"


class CreationStatus(StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class TaskStatus(StrEnum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class PostStatus(StrEnum):
    PENDING = "PENDING"
    PUBLISHED = "PUBLISHED"
    REJECTED = "REJECTED"
    OFFLINE = "OFFLINE"


class TaskType(StrEnum):
    CHECK_IN = "CHECK_IN"
    QUIZ = "QUIZ"
    QR_CODE = "QR_CODE"
    SIMULATED_LOCATION = "SIMULATED_LOCATION"


class PointReason(StrEnum):
    TASK_COMPLETE = "TASK_COMPLETE"
    CREATION_PUBLISH = "CREATION_PUBLISH"
    POST_LIKED = "POST_LIKED"
    ADMIN_ADJUST = "ADMIN_ADJUST"


class BadgeRuleType(StrEnum):
    TASK_COUNT = "TASK_COUNT"
    CREATION_COUNT = "CREATION_COUNT"
    POINT_TOTAL = "POINT_TOTAL"
    MANUAL = "MANUAL"

