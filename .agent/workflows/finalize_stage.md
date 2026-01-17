---
description: Finalize Project Stage (Cleanup & Document)
---

This workflow cleans up temporary debugging scripts and ensures documentation is up to date when a development stage is considered "Finished".

# 1. Update Documentation
- [ ] Create or Update a specialized doc in `docs/` summarizing the breakthroughs (e.g., `docs/feature_xyz.md`).
- [ ] Update `walkthrough.md` with final screenshots or metrics.

# 2. Cleanup Temporary Scripts
// turbo
Delete the following temporary debugging files if they exist:
- `tests/scripts/debug_*.py` (unless useful for long-term regression)
- `tests/scripts/compare_*.py`
- `scripts/identify_*.py`
- `scripts/query_temp_db.py`
- `scripts/fetch_db.py`
- `scripts/check_metrics.py`
- `instance/temp_*.db`

# 3. Final Verification
- [ ] Verify `task.md` items are all checked `[x]`.
- [ ] Run a final `git status` to ensure working directory is clean.
