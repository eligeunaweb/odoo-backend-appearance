from odoo.exceptions import AccessError, ValidationError
from odoo.tests import TransactionCase, new_test_user

from ..models.appearance import KEY


class TestAppearance(TransactionCase):
    def test_publish_restore(self):
        service = self.env["backend.appearance"]
        profile = {"accent": "#3366AA", "navbar": "", "density": "compact"}
        self.assertEqual(service.publish(profile)["accent"], "#3366aa")
        self.assertEqual(service._published()["density"], "compact")
        self.assertEqual(service.restore(), {"accent": "", "navbar": "", "density": "normal"})

    def test_invalid_and_corrupt_profiles(self):
        service = self.env["backend.appearance"]
        profile = {"accent": "#123456", "navbar": "", "density": "spacious"}
        service.publish(profile)
        for invalid in ({}, {**profile, "accent": "red"}, {**profile, "density": []}):
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
