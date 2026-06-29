import pytest

from agentid_verify import PassportExpired, SignatureInvalid, verify_passport
from trusted_agent_procurement.identity import DemoPassportIssuer, _base64url_encode


def test_demo_passport_verifies_and_exposes_capabilities():
    issuer = DemoPassportIssuer.create()
    token = issuer.issue_passport(name="buyer", capabilities=["purchase:gpu", "budget:5000"])

    claims = verify_passport(token)

    assert claims.name == "buyer"
    assert claims.has_capability("purchase:gpu")
    assert claims.has_capability("budget:5000")


def test_tampered_passport_is_rejected():
    issuer = DemoPassportIssuer.create()
    token = issuer.issue_passport(name="buyer", capabilities=["purchase:gpu"])
    header, payload, signature = token.split(".")
    tampered_payload = _base64url_encode(b'{"iss":"' + issuer.issuer_did.encode() + b'","exp":9999999999,"cap":["purchase:gpu","budget:999999"]}')
    tampered = f"{header}.{tampered_payload}.{signature}"

    with pytest.raises(SignatureInvalid):
        verify_passport(tampered)


def test_expired_passport_is_rejected():
    issuer = DemoPassportIssuer.create()
    token = issuer.issue_passport(name="buyer", capabilities=["purchase:gpu"], ttl_seconds=-1)

    with pytest.raises(PassportExpired):
        verify_passport(token)
