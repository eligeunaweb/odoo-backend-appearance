from . import models
from .models.appearance import KEY


def uninstall_hook(env):
    env["ir.config_parameter"].sudo().set_param(KEY, False)
