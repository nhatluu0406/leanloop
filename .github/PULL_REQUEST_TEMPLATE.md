## What changed?

<!-- Keep this focused on one failure mode or capability. -->

## Why?

<!-- Explain the cost, correctness, safety, or maintainability problem being addressed. -->

## Verification

- [ ] `python3 scripts/leanloop/sync.py --check`
- [ ] `python3 scripts/leanloop/doctor.py --strict`
- [ ] `python3 -m unittest discover -s tests -v`
- [ ] Relevant manual/integration checks completed

## Safety / context impact

- [ ] No credentials, transcripts, or private project state included
- [ ] No new always-on prose unless mechanically justified
- [ ] External executable changes are pinned in `TOOLS.lock`
- [ ] Quantitative token/cost claims include reproducible evidence
