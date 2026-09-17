from datetime import datetime, timezone, timedelta
from uuid import uuid4

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from depin.core import (Registry, Verifier, VerificationError, ENROLL_DOMAIN, REVOKE_DOMAIN,
                        enrollment, evidence_digest, public_hex, signature, signed_event,
                        verify_receipt, utc_now)


def setup(tmp_path):
    operator, node, authority = (Ed25519PrivateKey.generate() for _ in range(3))
    registry = Registry(tmp_path / "pilot.sqlite")
    op_key, node_key = public_hex(operator), public_hex(node)
    payload = enrollment(op_key, node_key, "compute")
    node_id = registry.enroll(op_key, node_key, "compute", signature(operator, ENROLL_DOMAIN, payload),
                              signature(node, ENROLL_DOMAIN, payload))
    verifier = Verifier(registry, authority)
    evidence = b"demo workload artifact (not hardware proof)"
    event = signed_event(node, {"version": 1, "event_id": str(uuid4()), "node_id": node_id,
                                "sequence": 1, "resource_type": "compute", "started_at": utc_now(),
                                "ended_at": utc_now(), "measurement": {"quantity": 1, "unit": "job"},
                                "evidence_hash": evidence_digest(evidence), "policy_version": "pilot-1"})
    return registry, verifier, operator, node, authority, event, evidence


def test_enrollment_requires_both_signatures(tmp_path):
    r, _, operator, node, _, event, _ = setup(tmp_path)
    other = Ed25519PrivateKey.generate()
    p = enrollment(public_hex(operator), public_hex(other), "compute")
    with pytest.raises(VerificationError, match="signature"):
        r.enroll(public_hex(operator), public_hex(other), "compute", signature(operator, ENROLL_DOMAIN, p),
                 signature(node, ENROLL_DOMAIN, p))
    with pytest.raises(VerificationError, match="already enrolled"):
        p = enrollment(public_hex(operator), public_hex(node), "compute")
        r.enroll(public_hex(operator), public_hex(node), "compute", signature(operator, ENROLL_DOMAIN, p),
                 signature(node, ENROLL_DOMAIN, p))


def test_unreviewed_event_quarantined_and_receipt_signed(tmp_path):
    r, v, _, _, authority, event, evidence = setup(tmp_path)
    receipt = v.verify(event, evidence)
    assert receipt["decision"] == "quarantined"
    assert verify_receipt(receipt, public_hex(authority))
    assert r.receipt(event["event_id"]) == receipt
    assert Registry(r.path).receipt(event["event_id"]) == receipt


def test_trusted_evaluator_accepts_and_rejects(tmp_path):
    _, v, _, _, _, event, evidence = setup(tmp_path)
    assert v.verify(event, evidence, evaluator=lambda e, data: data == evidence)["decision"] == "accepted"
    new_event = signed_event(Ed25519PrivateKey.generate(), {k: val for k, val in event.items() if k != "signature"})
    # An unknown signing key cannot assert an independently accepted node contribution.
    with pytest.raises(VerificationError, match="signature"):
        v.verify(new_event, evidence, evaluator=lambda e, data: True)


def test_tampered_event_and_evidence_fail(tmp_path):
    _, v, _, _, _, event, evidence = setup(tmp_path)
    bad = {**event, "measurement": {"quantity": 999, "unit": "job"}}
    with pytest.raises(VerificationError, match="signature"):
        v.verify(bad, evidence)
    with pytest.raises(VerificationError, match="digest"):
        v.verify(event, b"different")


def test_replay_survives_restart_and_sequence_decreases_rejected(tmp_path):
    r, v, _, node, authority, event, evidence = setup(tmp_path)
    v.verify(event, evidence)
    with pytest.raises(VerificationError, match="replayed"):
        Verifier(Registry(r.path), authority).verify(event, evidence)
    older = signed_event(node, {**{k: value for k, value in event.items() if k != "signature"},
                                "event_id": str(uuid4())})
    with pytest.raises(VerificationError, match="replayed"):
        v.verify(older, evidence)


def test_revocation_blocks_events(tmp_path):
    r, v, operator, _, _, event, evidence = setup(tmp_path)
    revoke_payload = {"version": 1, "node_id": event["node_id"]}
    r.revoke(event["node_id"], signature(operator, REVOKE_DOMAIN, revoke_payload))
    with pytest.raises(VerificationError, match="revoked"):
        v.verify(event, evidence)


def test_unauthorized_revoke_and_forged_node_signature(tmp_path):
    r, v, _, _, _, event, evidence = setup(tmp_path)
    attacker = Ed25519PrivateKey.generate()
    with pytest.raises(VerificationError, match="signature"):
        r.revoke(event["node_id"], signature(attacker, REVOKE_DOMAIN, {"version": 1, "node_id": event["node_id"]}))
    with pytest.raises(VerificationError, match="signature"):
        v.verify({**event, "signature": signature(attacker, b"cv1:depin:event:v1\0", {k: val for k, val in event.items() if k != "signature"})}, evidence)


def test_no_bool_sequence_or_measurement(tmp_path):
    _, v, _, node, _, event, evidence = setup(tmp_path)
    for field, value in [("sequence", True), ("measurement", {"quantity": True, "unit": "job"})]:
        payload = {**{k: val for k, val in event.items() if k != "signature"}, field: value}
        with pytest.raises(VerificationError):
            v.verify(signed_event(node, payload), evidence)


def test_stale_future_and_naive_timestamp(tmp_path):
    _, v, _, node, _, event, evidence = setup(tmp_path)
    for timestamp in ["2020-01-01T00:00:00Z", "2999-01-01T00:00:00Z", "2026-01-01T00:00:00"]:
        payload = {**{k: val for k, val in event.items() if k != "signature"}, "ended_at": timestamp}
        with pytest.raises(VerificationError):
            v.verify(signed_event(node, payload), evidence)


def test_receipt_tampering_or_wrong_verifier_fails(tmp_path):
    _, v, _, _, authority, event, evidence = setup(tmp_path)
    receipt = v.verify(event, evidence)
    with pytest.raises(VerificationError):
        verify_receipt({**receipt, "decision": "accepted"}, public_hex(authority))
    with pytest.raises(VerificationError, match="wrong verifier"):
        verify_receipt(receipt, public_hex(Ed25519PrivateKey.generate()))


def test_evaluator_errors_fail_closed(tmp_path):
    _, v, _, _, _, event, evidence = setup(tmp_path)
    def broken(_event, _evidence):
        raise RuntimeError("service unavailable")
    assert v.verify(event, evidence, evaluator=broken)["decision"] == "quarantined"


def test_evaluator_rejection_and_next_sequence(tmp_path):
    _, v, _, node, authority, event, evidence = setup(tmp_path)
    first = v.verify(event, evidence, evaluator=lambda e, data: False)
    assert first["decision"] == "rejected"
    payload = {**{k: value for k, value in event.items() if k != "signature"},
               "event_id": str(uuid4()), "sequence": 2}
    second = v.verify(signed_event(node, payload), evidence)
    assert second["decision"] == "quarantined"
    assert verify_receipt(second, public_hex(authority))
