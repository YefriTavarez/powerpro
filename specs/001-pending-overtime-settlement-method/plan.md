# Implementation Plan: Pending Overtime Settlement Method

## Technical Context

`Overtime Authorization.settlement_method` is a read-only Select with no blank option. Frappe renders the first option, Cash, when the stored value is empty. The settlement controller correctly writes Cash or Compensatory Rest only after confirmation.

## Milestone 1: Metadata contract

- Add an empty Select option before the two actual settlement methods.
- Preserve all existing field properties and settlement controller behavior.

## Milestone 2: Regression verification

- Add a metadata test proving the field supports an unset pending state.
- Run the focused overtime authorization and settlement tests.
- Validate JSON, Python syntax, and the final diff.

## Risk and rollback

Risk is low: the change affects presentation of null values only. Rollback consists of reverting the metadata and test commit. No data migration is required because confirmed settlements already store explicit values.

<!-- NOTION_SYNC: 2026-09-09 - planned metadata-only correction and regression verification -->
