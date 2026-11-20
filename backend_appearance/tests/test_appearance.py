import base64
import io

from PIL import Image

from odoo.exceptions import AccessError, ValidationError
from odoo.tests import TransactionCase, new_test_user, tagged

from ..models.appearance import DEFAULT_PROFILE, KEY


@tagged("post_install", "-at_install")
class TestAppearance(TransactionCase):
    def test_publish_restore(self):
        service = self.env["backend.appearance"]
        profile = {
            **DEFAULT_PROFILE,
            "accent": "#3366AA",
            "density": "compact",
            "navbar_pattern": "waves",
            "pattern_intensity": 70,
        }
        self.assertEqual(service.publish(profile)["accent"], "#3366aa")
        self.assertEqual(service._published(), {**profile, "accent": "#3366aa"})
        self.assertEqual(service.restore(), DEFAULT_PROFILE)

    def test_legacy_profile_keeps_appearance(self):
        self.env["ir.config_parameter"].sudo().set_param(
            KEY, '{"accent":"#123456","navbar":"","density":"compact"}'
        )
        service = self.env["backend.appearance"]
        self.assertEqual(service._published(), {**DEFAULT_PROFILE, "accent": "#123456", "density": "compact"})

    def test_invalid_and_corrupt_profiles(self):
        service = self.env["backend.appearance"]
        profile = {**DEFAULT_PROFILE, "accent": "#123456", "density": "spacious"}
        service.publish(profile)
        for invalid in (
            {},
            {**profile, "accent": "red"},
            {**profile, "density": []},
            {**profile, "navbar_pattern": "url(example.png)"},
            {**profile, "pattern_intensity": 101},
            {**profile, "pattern_intensity": True},
        ):
            with self.assertRaises(ValidationError):
                service.publish(invalid)
        self.assertEqual(service._published(), profile)
        self.env["ir.config_parameter"].sudo().set_param(KEY, "{invalid")
        self.assertEqual(service._published()["density"], "normal")

    def test_internal_user_cannot_publish_or_restore(self):
        user = new_test_user(self.env, login="appearance_employee", groups="base.group_user")
        service = self.env["backend.appearance"].with_user(user)
        with self.assertRaises(AccessError):
            service.publish({"accent": "", "navbar": "", "density": "normal"})
        with self.assertRaises(AccessError):
            service.restore()
        with self.assertRaises(AccessError):
            service.normalize_photo("")

    def test_top_bar_photo_and_menu(self):
        service = self.env["backend.appearance"]
        original = io.BytesIO()
        Image.new("RGB", (2200, 600), "#3a7bb5").save(original, "PNG")
        encoded = base64.b64encode(original.getvalue()).decode()
        normalized = service.normalize_photo(encoded)
        with Image.open(io.BytesIO(base64.b64decode(normalized))) as image:
            self.assertEqual(image.format, "JPEG")
            self.assertLessEqual(image.width, 1920)
            self.assertLessEqual(image.height, 420)
        published = service.publish({
            **DEFAULT_PROFILE,
            "navbar": "#121212",
            "navbar_pattern": "dots",
            "navbar_photo": normalized,
            "apps_menu": "dark",
        })
        self.assertEqual(service._published(), published)
        self.assertEqual(published["navbar_pattern"], "dots")
        self.assertEqual(published["apps_menu"], "dark")
        for invalid in ("not a photo", base64.b64encode(b"<svg/>").decode()):
            with self.assertRaises(ValidationError):
                service.normalize_photo(invalid)
        self.assertEqual(service.restore(), DEFAULT_PROFILE)

    def test_custom_apps_menu_colors(self):
        service = self.env["backend.appearance"]
        profile = {
            **DEFAULT_PROFILE,
            "apps_menu": "custom",
            "apps_menu_background": "#FFCC00",
            "apps_menu_highlight": "#000011",
        }
        self.assertEqual(service.publish(profile), {**profile, "apps_menu_background": "#ffcc00"})
        for invalid in ("", "transparent", "url(example.png)", "#fff"):
            with self.assertRaises(ValidationError):
                service.publish({**profile, "apps_menu_highlight": invalid})
        self.assertEqual(service._published()["apps_menu_highlight"], "#000011")
