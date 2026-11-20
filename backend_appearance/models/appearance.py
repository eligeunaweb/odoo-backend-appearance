import json
import re

from odoo import _, api, models
from odoo.exceptions import AccessError, ValidationError

KEY = "backend_appearance.profile"
DENSITIES = ("compact", "normal", "spacious")
PATTERNS = ("solid", "dots", "grid", "diagonal", "waves")
DEFAULT_PROFILE = {
    "accent": "",
    "navbar": "",
    "density": "normal",
    "navbar_pattern": "solid",
    "pattern_intensity": 45,
}


class BackendAppearance(models.AbstractModel):
    _name = "backend.appearance"
    _description = "Backend appearance settings"

    @api.model
    def _validate(self, values):
        required = {"accent", "navbar", "density"}
        if not isinstance(values, dict) or not required <= values.keys() <= DEFAULT_PROFILE.keys():
            raise ValidationError(_("Invalid appearance profile."))
        values = {**DEFAULT_PROFILE, **values}
        for key in ("accent", "navbar"):
            value = values[key]
            if not isinstance(value, str) or (value and not re.fullmatch(r"#[0-9a-fA-F]{6}", value)):
                raise ValidationError(_("Use a color in #RRGGBB format."))
        if values["density"] not in DENSITIES:
            raise ValidationError(_("Invalid density."))
        if values["navbar_pattern"] not in PATTERNS:
            raise ValidationError(_("Invalid top bar pattern."))
        intensity = values["pattern_intensity"]
        if type(intensity) is not int or not 0 <= intensity <= 100:
            raise ValidationError(_("Pattern intensity must be between 0 and 100."))
        return {**values, "accent": values["accent"].lower(), "navbar": values["navbar"].lower()}

    @api.model
    def _published(self):
        stored = self.env["ir.config_parameter"].sudo().get_param(KEY)
        if stored:
            try:
                return self._validate(json.loads(stored))
            except (ValueError, ValidationError):
                pass
        return dict(DEFAULT_PROFILE)

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
