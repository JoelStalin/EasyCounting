from odoo import api, fields, models


class DgiiReportRegenerateWizard(models.TransientModel):
    """
    Dgii Wizard.

    This wizard only objective is to show a warning when a dgii report
    is about to be regenerated.
    """

    _name = "dgii.report.regenerate.wizard"
    _description = "DGII Report Regenerate Wizard"

    report_id = fields.Many2one("dgii.reports", "Report")

    def regenerate(self):
        """Regnera el reporte."""
        self.report_id._generate_report()
