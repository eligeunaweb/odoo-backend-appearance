from odoo import models
from odoo.http import request


class IrHttp(models.AbstractModel):
    _inherit = "ir.http"

    def session_info(self):
        result = super().session_info()
        if self.env.user._is_internal():
            companies = result["user_companies"]
            selected = request.httprequest.cookies.get("cids", "").split("-")
            allowed = {str(cid) for cid in companies["allowed_companies"]}
            cid = int(selected[0]) if set(selected) <= allowed else companies["current_company"]
            company = self.env["res.company"].browse(cid)
            result["backend_appearance"] = self.env["backend.appearance"]._published(company)
        return result
