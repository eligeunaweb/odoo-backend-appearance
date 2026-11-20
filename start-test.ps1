param([switch]$Update)

$composeArgs = @('-p', 'codex-odoo-appearance-18', '-f', (Join-Path $PSScriptRoot 'compose.test.yml'))

if ($Update) {
    docker compose @composeArgs run --rm odoo odoo -d appearance_test -u backend_appearance --test-enable --test-tags /backend_appearance --stop-after-init
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

# Clear generated assets before publishing the web port. Odoo rebuilds them
# against the shared filestore when the first login or backend page loads.
"env['ir.attachment'].regenerate_assets_bundles(); env.cr.commit()" |
    docker compose @composeArgs run --rm -T odoo odoo shell -d appearance_test --no-http
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

docker compose @composeArgs run --rm --service-ports odoo odoo -d appearance_test
exit $LASTEXITCODE
