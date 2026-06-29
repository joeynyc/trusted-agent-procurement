"""Error types for agentid verification."""


class AgentIdError(Exception):
    """Base error for agentid operations."""


class InvalidDid(AgentIdError):
    """The DID string is malformed or uses an unsupported method."""


class InvalidJwt(AgentIdError):
    """The JWT is structurally invalid."""


class SignatureInvalid(AgentIdError):
    """The Ed25519 signature does not match the payload."""


class PassportExpired(AgentIdError):
    """The passport's exp claim is in the past."""
