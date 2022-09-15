# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import io

from odoo import models

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class ReportProductPricelistMaxcam(models.AbstractModel):
    _inherit = 'report.product.report_pricelist'

    def _get_product_data(self, is_product_tmpl, product, pricelist, quantities):
        res = super(ReportProductPricelistMaxcam, self)._get_product_data(is_product_tmpl, product, pricelist,
                                                                            quantities)
        res.update({'default_code': product.default_code, 'alternate_code': product.alternate_code})
        return res

    def get_xlsx_report(self, data, response):
        header_fil = 4
        header_col = 1
        pricelist = data.get("pricelist")
        products = data.get("products")
        quantities = data.get("quantities")
        # Header
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()

        head = workbook.add_format({'align': 'right', 'font_color': '#212529', 'font_size': '16px'})
        sheet.merge_range('A2:B3', "Lista de precios:", head)
        head2 = workbook.add_format({'align': 'left', 'font_color': '#008784', 'font_size': '16px'})
        sheet.merge_range('C2:D3', pricelist.name + " (" + pricelist.currency_id.name + ")", head2)

        header_format = workbook.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter',
                                             'font_color': '#666666', 'top': 1, 'bottom': 1, 'font_size': 12})

        # Title Table
        sheet.write(header_fil, header_col, 'Productos', header_format)
        # productos
        products_name = map(lambda x: x.get('name'), products)
        len_max = len('Productos') + 1
        style = workbook.add_format({'bold': True, 'align': 'left', 'valign': 'vcenter', 'font_color': '#008784',
                                     'font_size': 12})
        self.write_in_xlsx(sheet, products_name, header_fil, header_col, style, len_max)
        header_col += 1
        sheet.write(header_fil, header_col, 'Referencia interna', header_format)

        # Referencia interna
        default_code = map(lambda x: x.get('default_code'), products)
        len_max = len('Referencia interna') + 1
        style = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'font_size': 12})
        self.write_in_xlsx(sheet, default_code, header_fil, header_col, style, len_max)

        header_col += 1
        sheet.write(header_fil, header_col, 'Código alterno', header_format)

        # Referencia interna
        default_code = map(lambda x: x.get('alternate_code'), products)
        len_max = len('Código alterno') + 1
        style = workbook.add_format({'align': 'left', 'valign': 'vcenter', 'font_size': 12})
        self.write_in_xlsx(sheet, default_code, header_fil, header_col, style, len_max)
        price = list(map(lambda x: x.get('price'), products))

        # Unidades
        style = workbook.add_format({'align': 'right', 'valign': 'vcenter', 'font_size': 12})
        qty_format = workbook.add_format({'bold': True, 'align': 'right', 'valign': 'vcenter',
                                          'font_color': '#666666', 'top': 1, 'bottom': 1, 'font_size': 12})
        for qty in quantities:
            header_col += 1
            title_qty = str(qty) + " Unidades"
            sheet.write(header_fil, header_col, title_qty, qty_format)
            data_qty = list(map(lambda x: x.get(qty), price))
            self.write_in_xlsx(sheet, data_qty, header_fil, header_col, style, len(title_qty) + 1)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()

    def write_in_xlsx(self, sheet, data, fil, col, style, max):
        inter_col = col
        inter_fil = fil
        max_name = max
        for record in data:
            if record:
                text = record
            else:
                text = ''
            inter_fil += 1
            sheet.write(inter_fil, inter_col, text, style)
            if record:
                data_len = len(str(record))
                if max_name < data_len:
                    max_name = data_len
        max_name += 1
        sheet.set_column(col, col, max_name)
