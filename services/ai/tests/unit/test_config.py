"""Unit tests for sovereign-mode configuration policy."""

import pytest

from app.config import Settings


def test_loopback_endpoint_is_local() -> None:
    s = Settings(ai_base_url="http://localhost:11434/v1", _env_file=None)
    assert s.is_local_endpoint
    assert s.validate_sovereign_mode() == []


def test_private_subnet_is_local() -> None:
    s = Settings(ai_base_url="http://192.168.1.10:1234/v1", _env_file=None)
    assert s.is_local_endpoint


@pytest.mark.parametrize(
    "url",
    [
        "https://api.openai.com/v1",
        "https://api.anthropic.com/v1",
        "http://example.com/v1",
    ],
)
def test_remote_endpoint_violates_sovereign_mode(url: str) -> None:
    s = Settings(ai_base_url=url, ai_allow_cloud=False, _env_file=None)
    assert not s.is_local_endpoint
    problems = s.validate_sovereign_mode()
    assert len(problems) == 1
    assert "not a local endpoint" in problems[0]


def test_cloud_allowed_silences_violation() -> None:
    s = Settings(
        ai_base_url="https://api.openai.com/v1", ai_allow_cloud=True, _env_file=None
    )
    assert s.validate_sovereign_mode() == []
