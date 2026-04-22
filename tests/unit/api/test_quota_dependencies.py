"""Tests for quota dependency defaults on protected API routes."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from src.api.auth.models import User


class TestQuotaDependencyDefaults:
    """Quota dependency behavior in local and cloud modes."""

    def test_local_mode_bypasses_quota_enforcement(self) -> None:
        """Local mode should return the current user without checking quota."""
        from src.api.auth.middleware import LocalUser

        from src.api.auth.dependencies import check_usage_quota

        dependency = check_usage_quota("simulations")
        current_user = LocalUser()
        db = MagicMock()

        with (
            patch("src.api.auth.dependencies.is_local_mode", return_value=True),
            patch("src.api.auth.dependencies.usage_tracker.check_quota") as check_quota,
            patch(
                "src.api.auth.dependencies.usage_tracker.increment_usage"
            ) as increment_usage,
        ):
            result = dependency(current_user=current_user, db=db)

        assert result is current_user
        check_quota.assert_not_called()
        increment_usage.assert_not_called()

    def test_cloud_mode_enforces_quota(self) -> None:
        """Cloud mode should raise 429 when quota is exhausted."""
        from src.api.auth.dependencies import check_usage_quota

        dependency = check_usage_quota("simulations")
        current_user = MagicMock(spec=User)
        current_user.role = "free"
        current_user.simulations_this_month = 10
        current_user.api_calls_this_month = 0
        current_user.video_analyses_this_month = 0
        db = MagicMock()

        with (
            patch("src.api.auth.dependencies.is_local_mode", return_value=False),
            patch(
                "src.api.auth.dependencies.usage_tracker.check_quota",
                return_value=False,
            ),
            pytest.raises(HTTPException) as excinfo,
        ):
            dependency(current_user=current_user, db=db)

        assert excinfo.value.status_code == 429
        assert "Usage quota exceeded" in str(excinfo.value.detail)
