"""EvidencePack — reproducible receipts for claim checks.

A sealed pack records *what* was checked, by *which tool*, with *what verdict*,
plus two deterministic hashes:

  * certificate_hash   — fingerprint of the VERIFIED RESULT
                         (tool, version, normalized input, status, result body).
                         The timestamp is deliberately NOT part of it, so the
                         same check sealed twice yields the same certificate.
  * evidence_pack_hash — fingerprint of the whole pack (everything except the
                         evidence_pack_hash field itself).

EvidencePack records what was checked and whether it can be replayed. It does
not prove scientific truth or replace experiment, simulation or peer review.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, List, Optional

SCHEMA_VERSION = "evidencepack/v0.1"
PUBLIC_WORDING = (
    "EvidencePack records what was checked, by which tool, with what verdict, "
    "and whether the result can be reproduced. It does not prove scientific "
    "truth or replace experiment, simulation or peer review."
)

# Fields excluded from the certificate hash (a certificate is the *result*
# fingerprint, independent of when/where it was sealed).
_CERT_EXCLUDE = {"timestamp", "pack_id", "certificate_hash", "evidence_pack_hash"}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, default=str)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass
class EvidencePack:
    tool_name: str
    raw_input: str
    status: str
    tool_version: str = "0"
    normalized_input: str = ""
    result_body: Any = None
    replay_command: str = ""
    limitations: List[str] = field(default_factory=list)
    next_required_validation: str = ""
    schema_version: str = SCHEMA_VERSION
    public_wording: str = PUBLIC_WORDING
    timestamp: str = ""
    pack_id: str = ""
    certificate_hash: str = ""
    evidence_pack_hash: str = ""

    def __post_init__(self):
        if not self.normalized_input:
            self.normalized_input = " ".join(str(self.raw_input).split()).lower()
        if not self.timestamp:
            self.timestamp = now_iso()

    # --- hashing ----------------------------------------------------------
    def _cert_payload(self) -> dict:
        d = asdict(self)
        return {k: v for k, v in d.items() if k not in _CERT_EXCLUDE}

    def compute_certificate_hash(self) -> str:
        return _sha256(_canonical(self._cert_payload()))

    def compute_evidence_pack_hash(self) -> str:
        d = asdict(self)
        d.pop("evidence_pack_hash", None)
        return _sha256(_canonical(d))

    def seal(self) -> "EvidencePack":
        if not self.pack_id:
            self.pack_id = "ev_" + self.compute_certificate_hash()[:16]
        self.certificate_hash = self.compute_certificate_hash()
        self.evidence_pack_hash = self.compute_evidence_pack_hash()
        return self

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "EvidencePack":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in d.items() if k in known})


def verify(pack_dict: dict) -> dict:
    """Re-derive both hashes and check the seal. Returns a verdict dict."""
    p = EvidencePack.from_dict(pack_dict)
    cert = p.compute_certificate_hash()
    pack = p.compute_evidence_pack_hash()
    cert_ok = (cert == pack_dict.get("certificate_hash"))
    pack_ok = (pack == pack_dict.get("evidence_pack_hash"))
    if cert_ok and pack_ok:
        status = "SEALED_OK"
    elif not cert_ok:
        status = "CERTIFICATE_MISMATCH"
    else:
        status = "PACK_HASH_MISMATCH"
    return {"tool": "evidencepack", "status": status,
            "pack_id": pack_dict.get("pack_id"),
            "certificate_ok": cert_ok, "pack_hash_ok": pack_ok,
            "expected_certificate_hash": cert, "expected_evidence_pack_hash": pack,
            "public_wording": PUBLIC_WORDING}


def diff(a: dict, b: dict) -> dict:
    """Compare two packs. Same certificate hash => MATCH, else DRIFT (+ fields)."""
    drift_fields = []
    for k in ("tool_name", "tool_version", "normalized_input", "status", "result_body"):
        if a.get(k) != b.get(k):
            drift_fields.append({"field": k, "a": a.get(k), "b": b.get(k)})
    match = a.get("certificate_hash") == b.get("certificate_hash") and not drift_fields
    return {"tool": "evidencepack", "status": "MATCH" if match else "DRIFT",
            "a_certificate_hash": a.get("certificate_hash"),
            "b_certificate_hash": b.get("certificate_hash"),
            "drift_fields": drift_fields, "public_wording": PUBLIC_WORDING}
