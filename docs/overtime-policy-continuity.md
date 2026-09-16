# Equivalent policy coverage across midnight

An overtime interval may cross consecutive approved Overtime Pay Policy periods when all calculation and compensatory rules are equivalent. Coverage must have no missing dates or overlapping periods and must belong to the source company. Changes in rates, night basis, weekly threshold, weekly-rest treatment or compensatory rules still require separate treatment.

The effective snapshot retains the first real policy name for existing Link fields and includes `policy_versions` with the complete original policy values, dates and approvals. The top-level date range describes aggregate coverage; no policy document is extended or rewritten. The review dialog lists each original version and date range. Submitted sources resolve all versions from their persisted snapshot and require every version to remain approved. Subsequent policy revisions do not silently reprice them. Single-policy snapshots and hashes retain their previous representation.

Ordinary night automation requires opt-in on every participating policy. Its independently evaluated coverage must select the same policy-version chain as the authorization.

No schema migration, policy edit, rate change, salary creation or adjustment submission is performed by this patch. After deployment, review the affected drafts through the usual historical-evidence workflow. Evidence, holiday-base, election and settlement prerequisites still apply.

## Validation

- `python -m unittest discover -s tests -p 'test_overtime*.py'`
- `node tests/test_checkin_review_ui.cjs`
- Development-only: `tests/dev_overtime_policy_coverage.py` and `tests/dev_overtime_policy_settings.py`, executed from the confirmed Development site's `sites/` directory with its environment Python and this checkout on the import path. Both scripts require `igcaribe.fortabs.com` with developer mode, prohibit commits/mail/jobs, roll back fixtures and verify counts afterward. Never run these scripts on production.

The policy regression covers a shift from 18:00 through 06:00 excluding 21:00–22:00: 11 worked hours and 8 overlapping night-premium hours. It also checks gaps, overlaps, rule mismatches, exact-midnight endings, saved-version pinning, a cancelled participating version, forged client snapshots and unchanged legacy hashes.

## Rollback

Before any multi-policy adjustment is approved, the code can be reverted normally. Once a submitted source contains `policy_versions`, reverting only the selector would make that source fail coverage validation. Restore the compatible code or resolve those sources through the native audited cancellation/amendment process after checking linked documents. Do not remove snapshot versions or extend approved policy dates directly.
