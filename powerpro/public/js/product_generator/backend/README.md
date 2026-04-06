This folder stores local mirrors of Site-level Server Scripts (API) used by Product Generator client scripts.

Purpose:
- Document backend behavior that does not exist in the app repository.
- Enable code review/versioning of site scripts.

Suggested organization:
- Keep client scripts in `../` (this folder's parent).
- Keep API Server Scripts in `./` with this naming:
  - `<api_method>.api_server_script.py`
- Keep DocType Event Server Scripts in `./` with this naming:
  - `<script_name>.doctype_event_server_script.py`

Source site:
- `igcaribe.fortabs.com`

Notes:
- These files are mirrors, not automatically loaded by Frappe.
- Real execution source remains `Server Script` records in the site database.
