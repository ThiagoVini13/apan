from enum import StrEnum

from apan.core.schemas import ApiModel


class HealthStatus(StrEnum):
    OK = "ok"
    UNAVAILABLE = "unavailable"


class HealthRead(ApiModel):
    status: HealthStatus
