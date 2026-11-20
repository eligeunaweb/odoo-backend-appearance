import json
import re

from odoo import _, api, models
from odoo.exceptions import AccessError, ValidationError

KEY = "backend_appearance.profile"
DENSITIES = ("compact", "normal", "spacious")


class BackendAppearance(models.AbstractModel):
    _name = "backend.appearance"
    _description = "Backend appearance settings"

    @api.model
    def _validate(self, values):
        if not isinstance(values, dict) or values.keys() != {"accent", "navbar", "density"}:
            raise ValidationError(_("Invalid appearance profile."))
        for key in ("accent", "navbar"):
            value = values[key]
            if not isinstance(value, str) or (value and not re.fullmatch(r"#[0-9a-fA-F]{6}", value)):
                raise ValidationError(_("Use a color in #RRGGBB format."))
        if values["density"] not in DENSITIES:
            raise ValidationError(_("Invalid density."))
        return {**values, "accent": values["accent"].lower(), "navbar": values["navbar"].lower()}

    @api.model
    def _published(self):
        stored = self.env["ir.config_parameter"].sudo().get_param(KEY)
        if stored:
            try:
                return self._validate(json.loads(stored))
            except (ValueError, ValidationError):
                pass
        return {"accent": "", "navbar": "", "density": "normal"}

    @api.model
    def _check_admin(self):
        if not self.env.user.has_group("base.group_system"):
            raise AccessError(_("Only Settings administrators can change backend appearance."))

    @api.model
    def publish(self, values):
        self._check_admin()
        profile = self._validate(values)
        self.env["ir.config_parameter"].sudo().set_param(KEY, json.dumps(profile))
        return profile

    @api.model
    def restore(self):
        self._check_admin()
        self.env["ir.config_parameter"].sudo().set_param(KEY, False)
        return self._published()
