"""File: dgii.py ."""
from werkzeug.urls import url_encode
from werkzeug.utils import redirect

from odoo.http import Controller, request, route


class DgiiReportsControllers(Controller):
    """Controlador DGII."""

    @route(["/dgii_reports"], type="http", auth="user")
    def redirect_link(self, rnc=None, invoice_id=None, modify=None):
        """Este endpoint ayuda a redireccionar hacia la factura o el cliente."""
        url = "/web?#"
        record = False

        if rnc:
            record = request.env["res.partner"].search([("vat", "=", rnc)])
        elif invoice_id and not modify:
            record = request.env["account.move"].browse(int(invoice_id))
        elif invoice_id and modify:
            # TODO: agregar logica para buscar la factura modificadora
            pass

        if record:
            action = record[0].get_access_action(access_uid=request.session.uid)
            url_params = {
                "model": record._name,
                "action": action.get("id"),
            }

            if len(record) == 1:
                url_params["id"] = record.id
                url_params["active_id"] = record.id

            view_id = record.get_formview_id(access_uid=request.session.uid)
            if view_id:
                url_params["view_id"] = view_id

            url = "/web?#%s" % url_encode(url_params)

        return request.redirect(url)
