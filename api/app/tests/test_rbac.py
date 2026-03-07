"""Tests for RBAC role hierarchy and permission checking."""

import pytest

from app.models.user import UserRole
from app.rbac import ROLE_HIERARCHY, has_min_role, require_role, role_level


@pytest.mark.asyncio
async def test_role_hierarchy_order() -> None:
    """Role hierarchy is ordered from least to most privileged."""
    assert ROLE_HIERARCHY == [
        UserRole.FAMILY,
        UserRole.CAREGIVER,
        UserRole.CARE_MANAGER,
        UserRole.AGENCY_ADMIN,
        UserRole.SUPER_ADMIN,
    ]


@pytest.mark.asyncio
async def test_role_level_values() -> None:
    """Each role has a distinct privilege level."""
    assert role_level(UserRole.FAMILY) == 0
    assert role_level(UserRole.CAREGIVER) == 1
    assert role_level(UserRole.CARE_MANAGER) == 2
    assert role_level(UserRole.AGENCY_ADMIN) == 3
    assert role_level(UserRole.SUPER_ADMIN) == 4


@pytest.mark.asyncio
async def test_super_admin_passes_any_check() -> None:
    """Super-admin meets any minimum role requirement."""
    for target_role in UserRole:
        assert has_min_role(UserRole.SUPER_ADMIN, target_role) is True


@pytest.mark.asyncio
async def test_family_fails_admin_check() -> None:
    """Family role does not meet agency_admin requirement."""
    assert has_min_role(UserRole.FAMILY, UserRole.AGENCY_ADMIN) is False


@pytest.mark.asyncio
async def test_caregiver_passes_caregiver_check() -> None:
    """Caregiver meets caregiver minimum role."""
    assert has_min_role(UserRole.CAREGIVER, UserRole.CAREGIVER) is True


@pytest.mark.asyncio
async def test_caregiver_fails_care_manager_check() -> None:
    """Caregiver does not meet care_manager requirement."""
    assert has_min_role(UserRole.CAREGIVER, UserRole.CARE_MANAGER) is False


@pytest.mark.asyncio
async def test_require_role_returns_callable() -> None:
    """require_role() returns a callable dependency."""
    dep = require_role(UserRole.AGENCY_ADMIN)
    assert callable(dep)
