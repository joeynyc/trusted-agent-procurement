"""Verify AI agent passport credentials."""

from ._claims import PassportClaims
from ._errors import AgentIdError, InvalidDid, InvalidJwt, PassportExpired, SignatureInvalid
from ._verify import verify_passport

__all__ = [
    "verify_passport",
    "PassportClaims",
    "AgentIdError",
    "InvalidDid",
    "InvalidJwt",
    "SignatureInvalid",
    "PassportExpired",
]

__version__ = "1.0.0"
