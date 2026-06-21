import copy
import unittest
from evidencepack import EvidencePack, verify, diff


def _pack(**kw):
    base = dict(tool_name="unitgate", tool_version="0.1.0", raw_input="E = m * a",
                status="DIMENSIONALLY_INVALID", result_body={"lhs": "M*L^2*T^-2"})
    base.update(kw)
    return EvidencePack(**base).seal()


class TestEvidencePack(unittest.TestCase):
    def test_seal_populates_hashes_and_id(self):
        p = _pack()
        self.assertTrue(p.certificate_hash and len(p.certificate_hash) == 64)
        self.assertTrue(p.evidence_pack_hash and p.pack_id.startswith("ev_"))

    def test_certificate_hash_is_timestamp_independent(self):
        a = _pack(); b = _pack()
        b.timestamp = "1999-01-01T00:00:00+00:00"
        b.seal()
        self.assertEqual(a.certificate_hash, b.certificate_hash)  # timestamp not in cert

    def test_verify_ok(self):
        self.assertEqual(verify(_pack().to_dict())["status"], "SEALED_OK")

    def test_verify_detects_tamper(self):
        d = _pack().to_dict()
        d["status"] = "DIMENSIONALLY_VALID"   # tamper without resealing
        self.assertEqual(verify(d)["status"], "CERTIFICATE_MISMATCH")

    def test_diff_match_and_drift(self):
        a = _pack().to_dict(); b = _pack().to_dict()
        self.assertEqual(diff(a, b)["status"], "MATCH")
        c = _pack(status="DIMENSIONALLY_VALID").to_dict()
        self.assertEqual(diff(a, c)["status"], "DRIFT")

    def test_same_input_same_certificate(self):
        self.assertEqual(_pack().certificate_hash, _pack().certificate_hash)


if __name__ == "__main__":
    unittest.main()
