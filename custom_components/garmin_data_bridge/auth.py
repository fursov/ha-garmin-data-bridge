"""Small, dependency-free helpers for the independent Garmin API token."""

from hashlib import sha256
from hmac import compare_digest
from secrets import token_urlsafe


def generate_token() -> str:
    """Generate a high-entropy token to display once at enrollment."""
    return token_urlsafe(32)


def token_digest(token: str) -> str:
    """Return the SHA-256 digest of a random, high-entropy token."""
    return sha256(token.encode("utf-8")).hexdigest()


def verify_bearer_header(header: str, expected_digest: str) -> bool:
    """Authenticate a bearer token without exposing its plaintext."""
    if not header.startswith("Bearer "):
        return False

    token = header.removeprefix("Bearer ")
    if not token or len(token) > 128:
        return False

    return compare_digest(token_digest(token), expected_digest)
