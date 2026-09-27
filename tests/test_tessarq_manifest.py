import json
from pathlib import Path


def test_tessarq_compatibility_manifest_is_pinned_and_safe():
    manifest = json.loads(Path("integrations/tessarq.json").read_text())

    assert manifest["schema"] == "civilisation-one/depin-tessarq-integration/v1"
    assert manifest["upstream"]["repository"] == "Civilisation-one/Quantum-Chain"
    assert len(manifest["upstream"]["commit"]) == 40
    assert manifest["upstream"]["software_version"] == "0.2.0-dev"

    protocol = manifest["protocol"]
    assert protocol["protocol_version"] == 1
    assert protocol["p2p_version"] == 2
    assert protocol["signature_scheme"] == "ML-DSA-65"
    assert protocol["hash"] == "SHA3-256"

    legacy = manifest["depin_python_mvp"]
    assert legacy["signature_scheme"] == "Ed25519"
    assert legacy["hash"] == "SHA-256"
    assert legacy["native_tessarq_compatible"] is False

    testnet = manifest["testnet_0"]
    assert testnet["validators"] == 4
    assert testnet["p2p_port"] != testnet["rpc_port"]
