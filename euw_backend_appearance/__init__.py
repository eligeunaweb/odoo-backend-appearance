from . import models
from .models.appearance import KEY, THEMES_KEY


def uninstall_hook(env):
    env["ir.config_parameter"].sudo().set_param(KEY, False)
    env["ir.config_parameter"].sudo().set_param(THEMES_KEY, False)
    env["res.company"].sudo().with_context(active_test=False).search([
        ("euw_backend_appearance_profile", "!=", False),
    ]).write({"euw_backend_appearance_profile": False})
