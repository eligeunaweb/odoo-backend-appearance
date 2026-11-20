{
    "name": "Backend Appearance",
    "summary": "Configure and preview backend colors and density",
    "author": "Backend Appearance contributors",
    "version": "19.0.1.4.0",
    "license": "LGPL-3",
    "images": ["static/description/banner.png"],
    "depends": ["web"],
    "data": ["views/appearance.xml"],
    "assets": {
        "web.assets_backend": [
            "backend_appearance/static/src/appearance.js",
            "backend_appearance/static/src/appearance.xml",
            "backend_appearance/static/src/appearance.scss",
        ],
    },
    "installable": True,
    "uninstall_hook": "uninstall_hook",
}
