from odoo.exceptions import AccessError, ValidationError
from odoo.tests import TransactionCase, new_test_user

from ..models.appearance import DEFAULT_PROFILE, KEY


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
