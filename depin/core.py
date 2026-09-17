"""Conservative, local DePIN identity/verification prototype. Not a physical-work proof."""
from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path
from uuid import UUID

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

VERSION = 1
RESOURCES = frozenset({"compute", "storage", "network", "sensor", "research"})
ENROLL_DOMAIN = b"cv1:depin:enroll:v1\0"
REVOKE_DOMAIN = b"cv1:depin:revoke:v1\0"
EVENT_DOMAIN = b"cv1:depin:event:v1\0"
RECEIPT_DOMAIN = b"cv1:depin:receipt:v1\0"
EVENT_KEYS = frozenset({"version", "event_id", "node_id", "sequence", "resource_type", "started_at", "ended_at", "measurement", "evidence_hash", "policy_version"})


class VerificationError(ValueError):
    """Bad signature, schema, authorization, freshness or replay."""


def canonical(record: dict) -> bytes:
    try:
        return json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise VerificationError("record is not canonical JSON") from exc


def public_hex(private_key: Ed25519PrivateKey) -> str:
    return private_key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw
    ).hex()


def _public(hex_key: str) -> Ed25519PublicKey:
    try:
        if not isinstance(hex_key, str) or len(hex_key) != 64:
            raise ValueError("bad public key length")
        return Ed25519PublicKey.from_public_bytes(bytes.fromhex(hex_key))
    except (TypeError, ValueError) as exc:
        raise VerificationError("invalid Ed25519 public key") from exc


def identity(role: str, hex_key: str) -> str:
    if role not in ("operator", "node", "verifier"):
        raise VerificationError("invalid identity role")
    _public(hex_key)
    return hashlib.sha256(f"cv1:depin:{role}:v1\0".encode() + bytes.fromhex(hex_key)).hexdigest()


def signature(private_key: Ed25519PrivateKey, domain: bytes, record: dict) -> str:
    return private_key.sign(domain + canonical(record)).hex()


def check_signature(hex_key: str, domain: bytes, record: dict, sig: str) -> None:
    try:
        if not isinstance(sig, str) or len(sig) != 128:
            raise ValueError("wrong signature length")
        _public(hex_key).verify(bytes.fromhex(sig), domain + canonical(record))
    except (ValueError, InvalidSignature, TypeError) as exc:
        raise VerificationError("signature verification failed") from exc


def evidence_digest(content: bytes) -> str:
    if not isinstance(content, bytes):
        raise VerificationError("evidence must be raw bytes")
    return "sha256:" + hashlib.sha256(content).hexdigest()


def _time(value: str) -> datetime:
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if result.tzinfo is None or result.utcoffset() is None:
            raise ValueError("missing timezone")
        return result.astimezone(timezone.utc)
    except (ValueError, AttributeError, TypeError) as exc:
        raise VerificationError("timestamp must be timezone-aware ISO 8601") from exc


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def enrollment(operator_key: str, node_key: str, resource_type: str) -> dict:
    if not isinstance(resource_type, str) or resource_type not in RESOURCES:
        raise VerificationError("unsupported resource type")
    return {"version": VERSION, "operator_id": identity("operator", operator_key),
            "node_id": identity("node", node_key), "resource_type": resource_type}


class Registry:
    """SQLite-backed registry and replay ledger; one database shared by node and verifier."""

    def __init__(self, path: str | Path):
        self.path = str(path)
        with sqlite3.connect(self.path) as db:
            db.execute("CREATE TABLE IF NOT EXISTS nodes (node_id TEXT PRIMARY KEY, node_key TEXT NOT NULL, operator_id TEXT NOT NULL, operator_key TEXT NOT NULL, resource_type TEXT NOT NULL, revoked INTEGER NOT NULL DEFAULT 0, sequence INTEGER NOT NULL DEFAULT 0)")
            db.execute("CREATE TABLE IF NOT EXISTS receipts (event_id TEXT PRIMARY KEY, node_id TEXT NOT NULL, sequence INTEGER NOT NULL, receipt TEXT NOT NULL, UNIQUE(node_id, sequence))")

    def enroll(self, operator_key: str, node_key: str, resource_type: str,
               operator_signature: str, node_signature: str) -> str:
        payload = enrollment(operator_key, node_key, resource_type)
        check_signature(operator_key, ENROLL_DOMAIN, payload, operator_signature)
        check_signature(node_key, ENROLL_DOMAIN, payload, node_signature)
        with sqlite3.connect(self.path) as db:
            try:
                db.execute("INSERT INTO nodes(node_id,node_key,operator_id,operator_key,resource_type) VALUES(?,?,?,?,?)",
                           (payload["node_id"], node_key, payload["operator_id"], operator_key, resource_type))
            except sqlite3.IntegrityError as exc:
                raise VerificationError("node already enrolled") from exc
        return payload["node_id"]

    def revoke(self, node_id: str, operator_signature: str) -> None:
        with sqlite3.connect(self.path) as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT operator_key, revoked FROM nodes WHERE node_id=?", (node_id,)).fetchone()
            if row is None or row[1]:
                raise VerificationError("unknown or revoked node")
            check_signature(row[0], REVOKE_DOMAIN, {"version": VERSION, "node_id": node_id}, operator_signature)
            db.execute("UPDATE nodes SET revoked=1 WHERE node_id=?", (node_id,))

    def receipt(self, event_id: str) -> dict | None:
        with sqlite3.connect(self.path) as db:
            row = db.execute("SELECT receipt FROM receipts WHERE event_id=?", (event_id,)).fetchone()
            return json.loads(row[0]) if row else None


def signed_event(private_key: Ed25519PrivateKey, payload: dict) -> dict:
    if frozenset(payload) != EVENT_KEYS:
        raise VerificationError("event keys differ from schema")
    return {**payload, "signature": signature(private_key, EVENT_DOMAIN, payload)}


def verify_receipt(receipt: dict, verifier_key: str) -> bool:
    expected = {"version", "receipt_id", "event_id", "node_id", "sequence", "event_hash", "decision", "policy_version", "verified_at", "verifier_id", "signature"}
    if not isinstance(receipt, dict) or set(receipt) != expected:
        raise VerificationError("invalid receipt schema")
    if receipt["verifier_id"] != identity("verifier", verifier_key):
        raise VerificationError("wrong verifier")
    payload = {k: v for k, v in receipt.items() if k not in ("signature", "receipt_id")}
    receipt_id = hashlib.sha256(RECEIPT_DOMAIN + canonical(payload)).hexdigest()
    if receipt["receipt_id"] != receipt_id:
        raise VerificationError("receipt digest mismatch")
    check_signature(verifier_key, RECEIPT_DOMAIN, {**payload, "receipt_id": receipt_id}, receipt["signature"])
    return True


class Verifier:
    """An externally configured evaluator is required for acceptance; self-attestation quarantines."""

    def __init__(self, registry: Registry, private_key: Ed25519PrivateKey, *, policy_version: str = "pilot-1"):
        self.registry = registry
        self.private_key = private_key
        self.policy_version = policy_version

    def verify(self, event: dict, evidence: bytes, *, evaluator=None, now: datetime | None = None) -> dict:
        if not isinstance(event, dict) or set(event) != EVENT_KEYS | {"signature"}:
            raise VerificationError("invalid event schema")
        payload = {k: v for k, v in event.items() if k != "signature"}
        if type(payload["version"]) is not int or payload["version"] != VERSION:
            raise VerificationError("unsupported event version")
        try:
            UUID(payload["event_id"])
        except (ValueError, TypeError, AttributeError) as exc:
            raise VerificationError("invalid event UUID") from exc
        if not isinstance(payload["node_id"], str) or len(payload["node_id"]) != 64:
            raise VerificationError("invalid node ID")
        if type(payload["sequence"]) is not int or payload["sequence"] < 1:
            raise VerificationError("invalid sequence")
        if (not isinstance(payload["resource_type"], str) or payload["resource_type"] not in RESOURCES
                or not isinstance(payload["policy_version"], str) or payload["policy_version"] != self.policy_version):
            raise VerificationError("invalid resource or policy")
        measurement = payload["measurement"]
        if (not isinstance(measurement, dict) or set(measurement) != {"quantity", "unit"}
                or type(measurement["quantity"]) is not int or measurement["quantity"] <= 0
                or not isinstance(measurement["unit"], str) or not 1 <= len(measurement["unit"]) <= 32):
            raise VerificationError("invalid measurement")
        started, ended = _time(payload["started_at"]), _time(payload["ended_at"])
        if now is None:
            now = datetime.now(timezone.utc)
        if now.tzinfo is None or now.utcoffset() is None:
            raise VerificationError("now must be timezone-aware")
        if (started > ended or started < now - timedelta(minutes=5)
                or ended < now - timedelta(minutes=5) or ended > now + timedelta(seconds=30)):
            raise VerificationError("invalid event time window")
        if payload["evidence_hash"] != evidence_digest(evidence):
            raise VerificationError("evidence digest mismatch")
        with sqlite3.connect(self.registry.path) as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT node_key, resource_type, revoked, sequence FROM nodes WHERE node_id=?", (payload["node_id"],)).fetchone()
            if row is None or row[2] or row[1] != payload["resource_type"]:
                raise VerificationError("unregistered, revoked or unauthorized node")
            check_signature(row[0], EVENT_DOMAIN, payload, event["signature"])
            if payload["sequence"] <= row[3] or db.execute("SELECT 1 FROM receipts WHERE event_id=?", (payload["event_id"],)).fetchone():
                raise VerificationError("replayed or out-of-order event")
            # Evidence bytes and node signatures establish integrity, NOT physical-service truth.
            # Only a trusted verifier-supplied evaluator may release a claim from quarantine.
            decision = "quarantined"
            if evaluator is not None:
                try:
                    decision = "accepted" if evaluator(payload, evidence) is True else "rejected"
                except Exception:
                    decision = "quarantined"  # fail closed on evaluator errors
            receipt_payload = {"version": VERSION, "event_id": payload["event_id"],
                               "node_id": payload["node_id"], "sequence": payload["sequence"],
                               "event_hash": hashlib.sha256(EVENT_DOMAIN + canonical(event)).hexdigest(),
                               "decision": decision, "policy_version": self.policy_version,
                               "verified_at": utc_now(), "verifier_id": identity("verifier", public_hex(self.private_key))}
            receipt_id = hashlib.sha256(RECEIPT_DOMAIN + canonical(receipt_payload)).hexdigest()
            signed_payload = {**receipt_payload, "receipt_id": receipt_id}
            receipt = {**signed_payload, "signature": signature(self.private_key, RECEIPT_DOMAIN, signed_payload)}
            db.execute("INSERT INTO receipts(event_id,node_id,sequence,receipt) VALUES(?,?,?,?)",
                       (payload["event_id"], payload["node_id"], payload["sequence"], canonical(receipt).decode()))
            db.execute("UPDATE nodes SET sequence=? WHERE node_id=?", (payload["sequence"], payload["node_id"]))
            return receipt
