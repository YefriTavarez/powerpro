# Documentary closure of historical work

Use **Solo registro histórico** on a draft Retroactive Overtime Adjustment when
the purpose is to document previously paid work or retain an ordinary-work entry
from an old source document. This is not overtime approval for a new payment.

1. Keep the source work date and start/end times. Select `Already Paid` or
   `Ordinary Work` as appropriate; neither selection invents payable hours.
2. Attach the historical source file to this adjustment and select it in
   **Documento histórico de respaldo**. Record its page, the operator's historical
   payment confirmation where applicable, and any assumptions in the reference.
3. Enter the break's start/end, if applicable. Mark estimated timing explicitly.
   The net declared duration must be positive and within Maximum Adjusted Hours.
   The break is not saved as an Employee Checkin.
4. Keep Settlement Payroll Date as the historical payroll reference. It does not
   schedule another earning. A new monetary amount is not inferred from this date.
5. The assigned employee overtime approver confirms the documentary-only purpose
   and submits through the normal document action.

The resulting document has `docstatus=1`, `status=Documented`, and
`settlement_status=Not Applicable`. The immutable documentary snapshot retains
declared intervals/hours, disposition, reference, source File identity and SHA256,
break estimate, historical payroll date, and the current approver/time. Verified
and payable hour fields remain zero; the declared duration appears separately.

This path does not certify weekly attendance, reclassify overtime, invent an
employee election, generate Additional Salary, or credit compensatory leave.
Existing verified payroll/evidence paths retain their validations. Active linked
salary inputs, elections, or credits prevent conversion. Manually linking an
Additional Salary to a documentary record is also rejected server-side.

Only drafts can enter this mode. Previously approved or settled records are not
converted. Correct a submitted documentary record by cancelling and amending it;
cancellation retains the documentary snapshot and does not reverse money.

## Deployment and verification

Deploy the custom-app commit using the site's normal application/DocType sync
process. No data-conversion patch is included, and no existing record is changed
by deployment. The new fields/Select options must be installed before use.

After deployment, save and submit a scoped documentary draft as its assigned
approver, reload it, and verify its snapshot, declared duration, status and
`Not Applicable` settlement. Verify that no linked Additional Salary or credit
was created. The source PDF and original checkins must remain intact.

Development verification includes site-free service/controller and UI tests plus
`tests/dev_retroactive_documentation.py`, which runs native `validate` and
`before_submit` against a synthetic employee/File, prohibits commits/outbound
effects, and verifies rollback. It does not install the new metadata or test the
final persisted save/readback; that remains the deployment acceptance check.

## Rollback

Before any documentary closure is submitted, reverting the commit and syncing
the previous DocType restores the previous UI/controller. After use, retain this
reader/guard code or cancel the documentary closures through the native UI first;
do not remove the `Documentary`/`Documented` metadata while submitted records use
it. Never rewrite `docstatus`, `Paid`, or historical audit fields with direct SQL.
