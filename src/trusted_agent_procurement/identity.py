"""Demo passport issuing helpers built around the agentid verifier format."""

from __future__ import annotations

import base64
import json
import time
import uuid
from dataclasses import dataclass

import base58
from nacl.signing import SigningKey

_ED25519_MULTICODEC = bytes([0xED, 0x01])


def _base64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def encode_did_key(public_key: bytes) -> str:
    """Encode a raw Ed25519 public key as a did:key identifier."""
    return "did:key:z" + base58.b58encode(_ED25519_MULTICODEC + public_key).decode("ascii")


@dataclass(frozen=True)
class DemoPassportIssuer:
    """Small in-memory issuer for repeatable demo passports."""

    signing_key: SigningKey
    issuer_did: str

    @classmethod
    def create(cls) -> "DemoPassportIssuer":
        signing_key = SigningKey.generate()
        issuer_did = encode_did_key(bytes(signing_key.verify_key))
        return cls(signing_key=signing_key, issuer_did=issuer_did)

    def issue_passport(
        self,
        *,
        name: str,
        capabilities: list[str],
        ttl_seconds: int = 3600,
    ) -> str:
        """Issue an Ed25519-signed JWT compatible with agentid passports."""
        now = int(time.time())
        payload = {
            "sub": self.issuer_did,
            "iss": self.issuer_did,
            "jti": str(uuid.uuid4()),
            "iat": now,
            "exp": now + ttl_seconds,
            "name": name,
            "cap": capabilities,
        }
        header = {"alg": "EdDSA", "typ": "JWT"}

        header_b64 = _base64url_encode(json.dumps(header, separators=(",", ":")).encode())
        payload_b64 = _base64url_encode(json.dumps(payload, separators=(",", ":")).encode())
        message = f"{header_b64}.{payload_b64}".encode("ascii")
        signature_b64 = _base64url_encode(self.signing_key.sign(message).signature)
        return f"{header_b64}.{payload_b64}.{signature_b64}"
