from odoo import models


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    def session_info(self):
        result = super().session_info()
        if self.env.user._is_internal():
            result["backend_appearance"] = self.env["backend.appearance"]._published()
        return result
