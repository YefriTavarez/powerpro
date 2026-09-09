# Feature Specification: Pending Overtime Settlement Method

**Feature Branch**: `fix/overtime-settlement-method-display`  
**Created**: 2026-09-09  
**Status**: Complete

## User Scenario

An approved overtime authorization retains the work call's planned settlement preference, but its actual settlement method is not determined until attendance has been reconciled and a user confirms the settlement preview.

## Requirements

- **FR-001**: A pending overtime authorization MUST display no actual Settlement Method.
- **FR-002**: Planned Settlement MUST continue to show either Cash or Compensatory Rest as selected on the authorization or inherited from its work call.
- **FR-003**: Settlement Method MUST be populated only by the confirmed settlement operation.
- **FR-004**: Existing cash and compensatory settlement creation behavior MUST remain unchanged.

## Acceptance Scenarios

1. Given an authorization planned for Compensatory Rest with settlement status Pending, when the form is displayed, then Settlement Method is blank.
2. Given an authorization planned for Cash with settlement status Pending, when the form is displayed, then Settlement Method is blank.
3. Given a confirmed cash settlement, Settlement Method remains Cash.
4. Given a confirmed compensatory-rest settlement, Settlement Method remains Compensatory Rest.

## Scope

This correction changes the pending-state metadata and adds regression coverage. It does not migrate settled records or alter settlement accounting.

<!-- NOTION_SYNC: 2026-09-09 - documented the pending overtime settlement-method display contract -->
<!-- NOTION_SYNC: 2026-09-09 - marked the settlement-method display specification complete -->
