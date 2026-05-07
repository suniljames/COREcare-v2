"""Care plan schemas — Client and staff variants (issue #125).

The Client schema (`ClientCarePlanRead`) excludes `clinical_detail`
structurally. RLS enforces *which row* the Client may read; the schema
enforces *which fields* are exposed in the response payload. Belt and
suspenders.
"""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ClientCarePlanRead(BaseModel):
    """Care plan response for the Client persona — plain-language fields only.

    `clinical_detail` is intentionally absent. Adding it here would defeat
    the structural separation Data Engineer §3 spec'd.
    """

    id: uuid.UUID
    version_no: int
    plain_summary: str
    care_team_blob: dict[str, Any]
    weekly_support_blob: dict[str, Any]
    allergies: list[str]
    emergency_contact_blob: dict[str, Any]
    updated_at: datetime

    model_config = {"from_attributes": True}


class StaffCarePlanRead(ClientCarePlanRead):
    """Care plan response for staff — includes `clinical_detail` and audit fields."""

    clinical_detail: dict[str, Any]
    authored_by_user_id: uuid.UUID
    is_active: bool
    supersedes_version_id: uuid.UUID | None = None

    model_config = {"from_attributes": True}
