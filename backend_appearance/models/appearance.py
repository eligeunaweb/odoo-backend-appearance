import base64
import binascii
import io
import json
import re

from PIL import Image, ImageOps

from odoo import _, api, models
from odoo.exceptions import AccessError, ValidationError

KEY = "backend_appearance.profile"
DENSITIES = ("compact", "normal", "spacious")
PATTERNS = ("solid", "dots", "grid", "diagonal", "waves")
MENU_STYLES = ("standard", "light", "dark")
PHOTO_LIMIT = 4 * 1024 * 1024
PHOTO_PROFILE_LIMIT = 300_000
DEFAULT_PROFILE = {
    "accent": "",
    "navbar": "",
    "density": "normal",
    "navbar_pattern": "solid",
    "pattern_intensity": 45,
    "navbar_photo": "",
    "apps_menu": "standard",
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
        if values["apps_menu"] not in MENU_STYLES:
            raise ValidationError(_("Invalid apps menu style."))
        photo = values["navbar_photo"]
        if not isinstance(photo, str) or len(photo) > PHOTO_PROFILE_LIMIT or (
            photo and (not photo.startswith("/9j/") or not re.fullmatch(r"[A-Za-z0-9+/]+={0,2}", photo))
        ):
            raise ValidationError(_("Invalid top bar photo."))
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
    def normalize_photo(self, encoded):
        self._check_admin()
        return self._normalize_photo(encoded)

    @api.model
    def _normalize_photo(self, encoded):
        if not isinstance(encoded, str) or len(encoded) > ((PHOTO_LIMIT + 2) // 3) * 4:
            raise ValidationError(_("Choose an image of up to 4 MB."))
        try:
            data = base64.b64decode(encoded, validate=True)
            if len(data) > PHOTO_LIMIT:
                raise ValidationError(_("Choose an image of up to 4 MB."))
            formats = ["JPEG", "PNG"]
            if Image.registered_extensions().get(".webp") == "WEBP":
                formats.append("WEBP")
            elif data[:4] == b"RIFF" and data[8:12] == b"WEBP":
                raise ValidationError(_("This server cannot read WebP images. Choose PNG or JPEG."))
            with Image.open(io.BytesIO(data), formats=formats) as source:
                if source.width * source.height > 16_000_000 or getattr(source, "is_animated", False):
                    raise ValidationError(_("Choose a still image of up to 16 megapixels."))
                source.thumbnail((1920, 420))
                photo = ImageOps.exif_transpose(source)
                photo.thumbnail((1920, 420))
                output = io.BytesIO()
                photo.convert("RGB").save(output, "JPEG", quality=78, optimize=True)
        except (ValueError, OSError, binascii.Error, Image.DecompressionBombError) as error:
            raise ValidationError(_("Choose a valid PNG, JPEG or WebP image.")) from error
        result = base64.b64encode(output.getvalue()).decode("ascii")
        if len(result) > PHOTO_PROFILE_LIMIT:
            raise ValidationError(_("Choose a smaller or less detailed image."))
        return result

    @api.model
    def publish(self, values):
        self._check_admin()
        profile = self._validate(values)
        if profile["navbar_photo"] and profile["navbar_photo"] != self._published()["navbar_photo"]:
            profile["navbar_photo"] = self._normalize_photo(profile["navbar_photo"])
        self.env["ir.config_parameter"].sudo().set_param(KEY, json.dumps(profile))
        return profile

    @api.model
    def restore(self):
        self._check_admin()
        self.env["ir.config_parameter"].sudo().set_param(KEY, False)
        return self._published()
