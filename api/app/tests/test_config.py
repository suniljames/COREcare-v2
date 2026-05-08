"""Tests for application configuration helpers."""

from unittest.mock import patch

import pytest

from app.config import settings


@pytest.mark.parametrize("value", ["development", "Development", "DEVELOPMENT", "DeVeLoPmEnT"])
def test_is_dev_mode_case_insensitive(value: str) -> None:
    """Settings.is_dev_mode treats any casing of 'development' as dev — see #257."""
    with patch.object(settings, "environment", value):
        assert settings.is_dev_mode


@pytest.mark.parametrize("value", ["production", "Production", "STAGING", "preview", ""])
def test_is_dev_mode_false_for_non_development(value: str) -> None:
    """Anything other than 'development' (any casing) is not dev mode."""
    with patch.object(settings, "environment", value):
        assert not settings.is_dev_mode
