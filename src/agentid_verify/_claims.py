"""Passport claims dataclass."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PassportClaims:
    """Verified passport claims."""

    sub: str
    iss: str
    jti: str
    iat: int
    exp: int
    name: str
    capabilities: list[str]

    def has_capability(self, capability: str) -> bool:
        return capability in self.capabilities
