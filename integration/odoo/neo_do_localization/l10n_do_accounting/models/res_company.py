from odoo import models


class ResCompany(models.Model):
    _inherit = "res.company"

    def _localization_use_documents(self):
        """ Dominican localization uses documents """
        self.ensure_one()
        return (
            self.country_id == self.env.ref("base.do")
            and True
            or super()._localization_use_documents()
        )
