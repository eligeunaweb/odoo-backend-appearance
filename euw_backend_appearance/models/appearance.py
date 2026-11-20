import base64
import binascii
import io
import json
import re

from PIL import Image, ImageOps

from odoo import _, api, models
from odoo.exceptions import AccessError, ValidationError

KEY = "euw_backend_appearance.profile"
THEMES_KEY = "euw_backend_appearance.themes"
IMAGE_FIELDS = ("navbar_photo", "logo", "favicon")
DENSITIES = ("compact", "normal", "spacious")
PATTERNS = ("solid", "dots", "grid", "diagonal", "waves")
MENU_STYLES = ("standard", "light", "dark", "custom")
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
    "apps_menu_background": "#182337",
    "apps_menu_highlight": "#34465f",
    "navbar_mode": "color",
    "photo_position": 50,
    "text_size": "standard",
    "logo": "",
    "favicon": "",
}


class BackendAppearance(models.AbstractModel):
    _name = "euw.backend.appearance"
    _description = "Backend appearance settings"

    @api.model
    def _validate(self, values):
        required = {"accent", "navbar", "density"}
        if not isinstance(values, dict) or not required <= values.keys() <= DEFAULT_PROFILE.keys():
            raise ValidationError(_("Invalid appearance profile."))
        legacy_background = "navbar_mode" not in values
        values = {**DEFAULT_PROFILE, **values}
        for key in ("accent", "navbar", "apps_menu_background", "apps_menu_highlight"):
            value = values[key]
            if not isinstance(value, str) or (
                (value or key.startswith("apps_menu_")) and not re.fullmatch(r"#[0-9a-fA-F]{6}", value)
            ):
                raise ValidationError(_("Use a color in #RRGGBB format."))
            values[key] = value.lower()
        if values["density"] not in DENSITIES:
            raise ValidationError(_("Invalid density."))
        if values["navbar_pattern"] not in PATTERNS:
            raise ValidationError(_("Invalid top bar pattern."))
        intensity = values["pattern_intensity"]
        if type(intensity) is not int or not 0 <= intensity <= 100:
            raise ValidationError(_("Pattern intensity must be between 0 and 100."))
        if values["apps_menu"] not in MENU_STYLES:
            raise ValidationError(_("Invalid apps menu style."))
        if values["navbar_mode"] not in ("color", "pattern", "photo"):
            raise ValidationError(_("Invalid top bar mode."))
        position = values["photo_position"]
        if type(position) is not int or not 0 <= position <= 100:
            raise ValidationError(_("Invalid photo position."))
        if values["text_size"] not in ("standard", "large"):
            raise ValidationError(_("Invalid text size."))
        for key in IMAGE_FIELDS:
            image = values[key]
            if not isinstance(image, str) or len(image) > PHOTO_PROFILE_LIMIT or (
                image and (not image.startswith("/9j/") or not re.fullmatch(r"[A-Za-z0-9+/]+={0,2}", image))
            ):
                raise ValidationError(_("Invalid appearance image."))
        if legacy_background:
            values["navbar_mode"] = (
                "photo" if values["navbar_photo"]
                else "pattern" if values["navbar_pattern"] != "solid"
                else "color"
            )
        return values

    @api.model
    def _read_profile(self, stored):
        if stored:
            try:
                return self._validate(json.loads(stored))
            except (ValueError, ValidationError):
                pass
        return False

    @api.model
    def _published(self, company=None):
        if company:
            profile = self._read_profile(company.sudo().euw_backend_appearance_profile)
            if profile:
                return profile
        stored = self.env["ir.config_parameter"].sudo().get_param(KEY)
        return self._read_profile(stored) or dict(DEFAULT_PROFILE)

    @api.model
    def _scope_company(self, scope):
        if scope == "global":
            return None
        if scope == "company":
            return self.env.company
        raise ValidationError(_("Invalid appearance scope."))

    @api.model
    def get_editor(self, scope):
        self._check_admin()
        company = self._scope_company(scope)
        return {
            "profile": self._published(company),
            "themes": sorted(self._themes()),
            "inherits_global": bool(company and not self._read_profile(company.sudo().euw_backend_appearance_profile)),
        }

    @api.model
    def _check_admin(self):
        if not self.env.user.has_group("base.group_system"):
            raise AccessError(_("Only Settings administrators can change backend appearance."))

    @api.model
    def normalize_photo(self, encoded, field="navbar_photo"):
        self._check_admin()
        return self._normalize_photo(encoded, field)

    @api.model
    def _normalize_photo(self, encoded, field="navbar_photo"):
        limits = {"navbar_photo": (1920, 420), "logo": (320, 96), "favicon": (64, 64)}
        if not isinstance(field, str) or field not in limits:
            raise ValidationError(_("Invalid appearance image."))
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
                source.thumbnail(limits[field])
                photo = ImageOps.exif_transpose(source)
                photo.thumbnail(limits[field])
                output = io.BytesIO()
                photo.convert("RGB").save(output, "JPEG", quality=78, optimize=True)
        except (ValueError, OSError, binascii.Error, Image.DecompressionBombError) as error:
            raise ValidationError(_("Choose a valid PNG, JPEG or WebP image.")) from error
        result = base64.b64encode(output.getvalue()).decode("ascii")
        if len(result) > PHOTO_PROFILE_LIMIT:
            raise ValidationError(_("Choose a smaller or less detailed image."))
        return result

    @api.model
    def _prepare_profile(self, values, previous=None):
        profile = self._validate(values)
        for key in IMAGE_FIELDS:
            if profile[key] and (not previous or profile[key] != previous[key]):
                profile[key] = self._normalize_photo(profile[key], key)
        return profile

    @api.model
    def publish(self, values, scope="global"):
        self._check_admin()
        company = self._scope_company(scope)
        profile = self._prepare_profile(values, self._published(company))
        if company:
            company.sudo().euw_backend_appearance_profile = json.dumps(profile)
        else:
            self.env["ir.config_parameter"].sudo().set_param(KEY, json.dumps(profile))
        return profile

    @api.model
    def restore(self, scope="global"):
        self._check_admin()
        company = self._scope_company(scope)
        if company:
            company.sudo().euw_backend_appearance_profile = False
        else:
            self.env["ir.config_parameter"].sudo().set_param(KEY, False)
        return self._published()

    @api.model
    def _theme_name(self, name):
        if not isinstance(name, str) or not 1 <= len(name.strip()) <= 60:
            raise ValidationError(_("Enter a theme name of up to 60 characters."))
        return name.strip()

    @api.model
    def _themes(self):
        value = self.env["ir.config_parameter"].sudo().get_param(THEMES_KEY)
        try:
            themes = json.loads(value or "{}")
        except ValueError:
            return {}
        return themes if isinstance(themes, dict) else {}

    @api.model
    def save_theme(self, name, values):
        self._check_admin()
        name = self._theme_name(name)
        params = self.env["ir.config_parameter"].sudo()
        themes = self._themes()
        if name not in themes and len(themes) >= 20:
            raise ValidationError(_("You can save up to 20 themes."))
        themes[name] = self._prepare_profile(values, themes.get(name))
        params.set_param(THEMES_KEY, json.dumps(themes))
        return sorted(themes)

    @api.model
    def load_theme(self, name):
        self._check_admin()
        themes = self._themes()
        if self._theme_name(name) not in themes:
            raise ValidationError(_("Theme not found."))
        return self._validate(themes[name.strip()])

    @api.model
    def delete_theme(self, name):
        self._check_admin()
        params = self.env["ir.config_parameter"].sudo()
        themes = self._themes()
        themes.pop(self._theme_name(name), None)
        params.set_param(THEMES_KEY, json.dumps(themes) if themes else False)
        return sorted(themes)

    @api.model
    def import_theme(self, data):
        self._check_admin()
        if (
            not isinstance(data, dict)
            or data.keys() != {"version", "profile"}
            or type(data["version"]) is not int
            or data["version"] != 1
        ):
            raise ValidationError(_("Invalid or unsupported appearance theme file."))
        return self._prepare_profile(data["profile"])
