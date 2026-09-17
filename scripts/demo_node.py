"""Run a local, non-networked node verification demonstration with ephemeral keys."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from uuid import uuid4

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from depin.core import (ENROLL_DOMAIN, Registry, Verifier, enrollment, evidence_digest,
                        public_hex, signature, signed_event, utc_now, verify_receipt)


def main() -> None:
    operator = Ed25519PrivateKey.generate()
    node = Ed25519PrivateKey.generate()
    verifier_key = Ed25519PrivateKey.generate()
    operator_pub, node_pub = public_hex(operator), public_hex(node)
    registration = enrollment(operator_pub, node_pub, "compute")
    with tempfile.TemporaryDirectory(prefix="cv1-depin-demo-") as folder:
        registry = Registry(Path(folder) / "registry.sqlite")
        node_id = registry.enroll(operator_pub, node_pub, "compute",
                                  signature(operator, ENROLL_DOMAIN, registration),
                                  signature(node, ENROLL_DOMAIN, registration))
        evidence = b"illustrative output, not proof of a physical workload"
        now = utc_now()
        event = signed_event(node, {
            "version": 1, "event_id": str(uuid4()), "node_id": node_id,
            "sequence": 1, "resource_type": "compute", "started_at": now,
            "ended_at": now, "measurement": {"quantity": 1, "unit": "job"},
            "evidence_hash": evidence_digest(evidence), "policy_version": "pilot-1",
        })
        receipt = Verifier(registry, verifier_key).verify(event, evidence)
        verify_receipt(receipt, public_hex(verifier_key))
        print(json.dumps({"node_id": node_id, "decision": receipt["decision"],
                          "receipt_id": receipt["receipt_id"], "signature_valid": True}, indent=2))
        assert receipt["decision"] == "quarantined"  # no independent evaluator


if __name__ == "__main__":
    main()
