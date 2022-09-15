from odoo import api, models


class ZebraReport(models.AbstractModel):
    _name = 'report.maxcam_stock.zebra_report_tags'

    @api.model
    def _get_report_values(self, docids, data=None):
        return {
            'doc_ids': docids,
            'doc_model': 'stock.picking',
            'docs': self.env['stock.picking'].browse(docids),
            'data': data,
        }
