"""Credential boundaries without loading Home Assistant."""

import importlib.util
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / (
    "custom_components/garmin_data_bridge/auth.py"
)
SPEC = importlib.util.spec_from_file_location("garmin_auth", MODULE)
assert SPEC is not None and SPEC.loader is not None
auth = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(auth)


def test_generated_tokens_are_distinct_and_high_entropy() -> None:
    """Each client must receive an independent unpredictable key."""
    first = auth.generate_token()
    second = auth.generate_token()
    assert first != second
    assert len(first) >= 40
    assert auth.token_digest(first) != first


def test_bearer_authentication_rejects_invalid_requests() -> None:
    """No token, another profile token, or a malformed header may pass."""
    secret = auth.generate_token()
    digest = auth.token_digest(secret)
    assert auth.verify_bearer_header(f"Bearer {secret}", digest)
    assert not auth.verify_bearer_header("", digest)
    assert not auth.verify_bearer_header(f"Basic {secret}", digest)
    assert not auth.verify_bearer_header("Bearer ", digest)
    assert not auth.verify_bearer_header(f"Bearer {auth.generate_token()}", digest)
    assert not auth.verify_bearer_header(f"Bearer {secret}extra", digest)
    assert not auth.verify_bearer_header(f"Bearer {'x' * 200}", digest)
