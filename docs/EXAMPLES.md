# EvidencePack examples

```bash
# seal a unitgate result into a receipt
python -m evidencepack seal --tool unitgate --input "E = m * a" \
  --status DIMENSIONALLY_INVALID --version 0.1.0 > pack.json

# verify the seal (recomputes both hashes)
python -m evidencepack verify pack.json        # -> SEALED_OK

# tamper detection: change "status" in pack.json by hand, then:
python -m evidencepack verify pack.json        # -> CERTIFICATE_MISMATCH

# compare two receipts
python -m evidencepack diff pack_a.json pack_b.json   # -> MATCH or DRIFT
```
The `certificate_hash` is timestamp-independent: sealing the same check twice gives the same certificate.
