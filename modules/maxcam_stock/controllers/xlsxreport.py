import json

from odoo import http
from odoo.addons.web.controllers.main import _serialize_exception
from odoo.http import content_disposition, request
from odoo.tools import html_escape

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class XLSXReportController(http.Controller):

    @http.route('/report/xlsx/report_pricelist_xlsx', type='http', auth='user', methods=['POST'], csrf=False)
    def get_report_xlsx(self, active_model, data, pricelist_id, quantities, active_ids, **kw):
        report_obj = request.env['report.product.report_pricelist']
        try:
            # if output_format == 'xlsx':
            response = request.make_response(
                None,
                headers=[('Content-Type', 'application/vnd.ms-excel'),
                         ('Content-Disposition', content_disposition('Lista de Precios' + '.xlsx'))
                         ]
            )
            product_ids = list(map(int, list(active_ids.split(','))))
            quantities = list(map(int, list(quantities.split(','))))
            pricelist_id = int(pricelist_id) if pricelist_id else None
            data = report_obj._get_report_data(active_model, product_ids, pricelist_id, quantities, 'pdf')
            report_obj.get_xlsx_report(data, response)
            return response
        except Exception as e:
            se = _serialize_exception(e)
            error = {
                'code': 200,
                'message': 'Odoo Server Error',
                'data': se
            }
            return request.make_response(html_escape(json.dumps(error)))
