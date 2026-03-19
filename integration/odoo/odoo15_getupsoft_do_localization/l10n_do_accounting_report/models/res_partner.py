"""file: res_partner.py ."""
from odoo import fields, models


class ResPartner(models.Model):
    """..."""

    _inherit = "res.partner"

    related = fields.Selection(
        [("0", "Not Related"), ("1", "Related")],
        default="0",
    )
