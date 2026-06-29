"""W3C did:key decoding for Ed25519."""

import base58

from ._errors import InvalidDid

_ED25519_MULTICODEC = bytes([0xED, 0x01])


def decode_did_key(did: str) -> bytes:
    """Decode a did:key string to a raw 32-byte Ed25519 public key."""
    if not did.startswith("did:key:z"):
        raise InvalidDid(f"expected did:key:z prefix, got: {did[:20]}")

    encoded = did[len("did:key:z"):]
    try:
        decoded = base58.b58decode(encoded)
    except Exception as exc:
        raise InvalidDid(f"base58 decode failed: {exc}") from exc

    if len(decoded) != 34:
        raise InvalidDid(f"expected 34 bytes, got {len(decoded)}")

    if decoded[:2] != _ED25519_MULTICODEC:
        raise InvalidDid("expected Ed25519 multicodec prefix")

    return decoded[2:]
