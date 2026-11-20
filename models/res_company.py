from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    backend_appearance_profile = fields.Text(groups="base.group_system", copy=False)
