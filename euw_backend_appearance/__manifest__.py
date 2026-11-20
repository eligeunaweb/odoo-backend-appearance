{
    "name": "Backend Appearance",
    "summary": "Configure and preview backend colors and density",
    "author": "Álvaro Martínez",
    "website": "https://alvaromh.com",
    "version": "15.0.1.4.0",
    "license": "LGPL-3",
    "depends": ["web"],
    "data": ["views/appearance.xml"],
    "assets": {
        "web.assets_qweb": [
            "euw_backend_appearance/static/src/appearance.xml",
        ],
        "web.assets_backend": [
            "euw_backend_appearance/static/src/appearance.js",
            "euw_backend_appearance/static/src/appearance.scss",
        ],
    },
    "installable": True,
    "uninstall_hook": "uninstall_hook",
}
