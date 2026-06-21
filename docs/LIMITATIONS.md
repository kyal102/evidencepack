# EvidencePack limitations

- A pack records *that a tool returned a verdict*; it does not independently re-verify the claim (use ReplayGate to re-run the check).
- `certificate_hash` covers tool, version, normalized input, status, and result body — not the timestamp, pack_id, or the hashes themselves.
- Canonical JSON (sorted keys) makes hashes stable across machines, but two tools must agree on `normalized_input` and `result_body` shape to compare cleanly.
- It does not prove scientific truth or replace experiment, simulation or peer review.
