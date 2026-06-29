"""JWT passport verification."""

import base64
import json
import time

from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey

from ._claims import PassportClaims
from ._did import decode_did_key
from ._errors import InvalidJwt, PassportExpired, SignatureInvalid


def _base64url_decode(value: str) -> bytes:
    padded = value + "=" * (4 - len(value) % 4) if len(value) % 4 else value
    return base64.urlsafe_b64decode(padded)


def verify_passport(token: str) -> PassportClaims:
    """Verify an Ed25519-signed agent passport JWT."""
    parts = token.split(".")
    if len(parts) != 3:
        raise InvalidJwt(f"expected 3 dot-separated parts, got {len(parts)}")

    header_b64, payload_b64, signature_b64 = parts

    try:
        payload = json.loads(_base64url_decode(payload_b64))
    except Exception as exc:
        raise InvalidJwt(f"payload parse failed: {exc}") from exc

    issuer = payload.get("iss")
    if not issuer:
        raise InvalidJwt("missing iss claim")

    try:
        signature = _base64url_decode(signature_b64)
    except Exception as exc:
        raise InvalidJwt(f"signature decode failed: {exc}") from exc

    if len(signature) != 64:
        raise InvalidJwt(f"signature must be 64 bytes, got {len(signature)}")

    message = f"{header_b64}.{payload_b64}".encode("ascii")
    try:
        VerifyKey(decode_did_key(issuer)).verify(message, signature)
    except BadSignatureError as exc:
        raise SignatureInvalid("Ed25519 signature verification failed") from exc

    expiry = payload.get("exp")
    if expiry is None:
        raise InvalidJwt("missing exp claim")
    if expiry < time.time():
        raise PassportExpired(f"passport expired at {expiry}")

    capabilities = payload.get("cap", [])
    if not isinstance(capabilities, list):
        raise InvalidJwt("cap must be an array")

    return PassportClaims(
        sub=payload.get("sub", ""),
        iss=issuer,
        jti=payload.get("jti", ""),
        iat=payload.get("iat", 0),
        exp=expiry,
        name=payload.get("name", ""),
        capabilities=capabilities,
    )
