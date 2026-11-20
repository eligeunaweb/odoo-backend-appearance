# Backend Appearance for Odoo 19

Visual settings for the internal Odoo client. See [Español](README.es.md).

## Install and verify

On a disposable Odoo 19 database, add the repository to the server's add-ons path, refresh the app list in developer mode and install **Backend Appearance**. Clear the Apps filter if needed. Open **Settings → Backend Appearance**.

Pick an accent, a navigation bar color and a density. Select **Preview** and open a real contact list and form in the same tab. Return to Settings to apply or discard. Reload a second session to verify publication. Use **Restore defaults** to restore the Odoo baseline. The profile is shared by all companies in the database.

To run the installation and automated tests against an isolated Docker database, open a terminal in this repository:

```sh
docker compose -p codex-odoo-appearance -f compose.test.yml run --rm odoo odoo -d appearance_test -i backend_appearance --test-enable --test-tags /backend_appearance --stop-after-init
```

For an existing disposable test server, retain its database connection and add-ons settings:

```sh
odoo -d appearance_test -i backend_appearance --test-enable --test-tags /backend_appearance --stop-after-init
```

For the manual acceptance test, install Contacts, Sales and Inventory. Create and edit a contact, save a quotation with a product and open an inventory list. Verify search and filters, regular-user access and narrow layouts. Upgrade the module, then uninstall it through Apps on the test database. Reload the client and reopen the records from the test. Check that the appearance returns to the Odoo baseline and that the published profile is removed.

Compatibility target: Odoo 19.0 Community. The runtime and coexistence matrix is pending. License: LGPL-3.
