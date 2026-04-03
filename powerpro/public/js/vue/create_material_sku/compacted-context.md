# Compact Context

Current work is in `index.js`.

The dialog now supports derived sheet creation without using `derived_from_item` or `derived_dimension_option`. It uses transient dialog fields:

- `parent_material_sku`
- `derived_dimension_choice`

## Key Behavior

- `material_format === "Sheet"` and `standard_sheet_size === "Derivado"` shows the derived helper UI.
- The selected parent SKU is mapped into hidden `standard_sheets` before submit, so backend persistence is unchanged.
- Parent SKU fetch populates and enforces:
  - `gsm`
  - `raw_material_type`
  - `roll_width`
  - `sheet_width`
  - `sheet_height`

## Dimension Behavior

- Parent `Sheet`: generated sheet-size options auto-fill both dimensions; both `sheet_width` and `sheet_height` become read-only.
- Parent `Roll`: one side must match a roll-derived proportion; the intended constrained side is enforced client-side.
- Field state logic avoids `read_only` and `reqd` being true at the same time.

## GSM Behavior

- On parent SKU selection, GSM auto-populates from the parent.
- In derived mode, GSM is locked to the parent and validated before submit.

## Localization

- Main dialog labels were translated to Spanish.
- Visible option `Estándar` is mapped back to backend value `Standard` on submit.

## Verification

- `node --check` passes on the file.

## Known Note

- Most field and section labels are in Spanish, but several alerts and confirmation messages are still in English if a full localization pass is needed.
