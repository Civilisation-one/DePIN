import copy
import json
from pathlib import Path

VECTORS = Path("conformance/tessarq-v1.json")
MANIFEST = Path("integrations/tessarq.json")


def load():
    return json.loads(VECTORS.read_text()), json.loads(MANIFEST.read_text())


def materialize(doc, vector):
    if "base" not in vector:
        return copy.deepcopy(vector["state"]), copy.deepcopy(vector["event"])
    base = next(v for v in doc["vectors"] if v["id"] == vector["base"])
    state, event = materialize(doc, base)
    state.update(vector.get("mutate_state", {}))
    event.update(vector.get("mutate", {}))
    return state, event


def semantic_admission(state, event):
    if not state["registered"]:
        return "reject", "unregistered node"
    if state["revoked"]:
        return "reject", "node revoked"
    if state["enrolled_resource"] != event["resource"]:
        return "reject", "resource class not authorised for node"
    if state["policy_version"] != event["policy_version"]:
        return "reject", "policy version mismatch"
    unit_len = len(event["unit"].encode())
    if event["quantity"] == 0 or unit_len == 0 or unit_len > 32:
        return "reject", "invalid measurement"
    now = state["now_ms"]
    if (
        event["started_at_ms"] > event["ended_at_ms"]
        or event["ended_at_ms"] + state["event_max_age_ms"] < now
        or event["ended_at_ms"] > now + state["event_max_future_ms"]
    ):
        return "reject", "event outside freshness window"
    if event["sequence"] <= state["last_sequence"]:
        return "reject", "replayed or out-of-order sequence"
    if state["duplicate_event"]:
        return "reject", "duplicate event"
    if not state["signature_valid"]:
        return "reject", "node event signature invalid"
    return "accept", None


def test_profile_matches_pinned_manifest():
    doc, manifest = load()
    assert doc["reviewed_upstream_commit"] == manifest["upstream"]["commit"]
    assert doc["software_version"] == manifest["upstream"]["software_version"]
    assert doc["protocol_version"] == manifest["protocol"]["protocol_version"]
    assert doc["profile"]["serialization"] == manifest["protocol"]["encoding"]
    assert doc["profile"]["signature_scheme"] == manifest["protocol"]["signature_scheme"]
    assert doc["profile"]["contribution_signature_context"] == manifest["protocol"]["signature_contexts"]["contribution_event"]
    assert doc["profile"]["evidence_hash"]["domain"] == manifest["protocol"]["hash_domains"]["evidence"]
    assert doc["profile"]["event_id"]["domain"] == manifest["protocol"]["hash_domains"]["event_id"]


def test_native_field_order_is_explicit_and_stable():
    doc, _ = load()
    assert doc["profile"]["field_order"] == [
        "node_id",
        "sequence",
        "resource",
        "started_at_ms",
        "ended_at_ms",
        "quantity",
        "unit",
        "evidence_hash",
        "policy_version",
        "observation",
    ]


def test_resource_classes_match_native_profile():
    doc, _ = load()
    assert doc["profile"]["resource_classes"] == [
        "compute",
        "storage",
        "network",
        "sensor",
        "research",
    ]


def test_semantic_vectors_match_admission_rules():
    doc, _ = load()
    for vector in doc["vectors"]:
        state, event = materialize(doc, vector)
        admission, reason = semantic_admission(state, event)
        assert admission == vector["expected"]["admission"], vector["id"]
        if admission == "reject":
            assert reason == vector["expected"]["reason"], vector["id"]
        else:
            assert vector["expected"]["initial_status"] == "quarantined"


def test_vectors_use_32_byte_hex_ids_and_hashes():
    doc, _ = load()
    for vector in doc["vectors"]:
        _, event = materialize(doc, vector)
        for field in ("node_id", "evidence_hash"):
            value = event[field]
            assert len(value) == 64
            int(value, 16)
