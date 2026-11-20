from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    euw_backend_appearance_profile = fields.Text(groups="base.group_system", copy=False)
