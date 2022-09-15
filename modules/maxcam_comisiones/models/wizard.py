import logging
from datetime import date
from datetime import datetime
from io import BytesIO

import xlsxwriter
from dateutil.relativedelta import relativedelta
from odoo import models, fields, http
from odoo.addons.web.controllers.main import serialize_exception, content_disposition
from odoo.http import request, Response

_logger = logging.getLogger(__name__)


class WizardMaxcamComision(models.TransientModel):
    _name = "wizard.reportes.comision"

    informe = fields.Selection(
        [
            ("Efectividad de vendedores", "Efectividad de vendedores"),
            ("Gestion de cobranza", "Gestion de cobranza"),
            ("Supervisores", "Supervisores"),
        ],
        "Tipo de informe",
        required=True,
    )
    fecha_inicio = fields.Date("Fecha de inicio", default=date.today().replace(day=1))
    fecha_term = fields.Date(
        "Fecha de termino", default=date.today().replace(day=1) + relativedelta(months=1, days=-1)
    )
    file = fields.Binary(readonly=True)
    filename = fields.Char()
    company_id = fields.Many2one("res.company", default=lambda self: self.env.user.company_id.id)
    supervisor_id = fields.Many2one(
        "hr.employee", string="Supervisor", domain=[("is_supervisor", "=", True)]
    )
    user_id = fields.Many2one("hr.employee")

    def _get_domain(self):
        search_domain = []
        search_domain += [("company_id", "=", self.company_id.id)]
        search_domain += [("invoice_date", ">=", self.fecha_inicio)]
        search_domain += [("invoice_date", "<=", self.fecha_term)]
        search_domain += [("move_type", "=", "out_invoice")]
        return search_domain

    def imprimir_excel(self):
        return {
            "type": "ir.actions.act_url",
            "url": "/web/get_excel_commision?informe=%s&wizard=%s&start=%s&end=%s"
            % (str(self.informe), self.id, str(self.fecha_inicio), str(self.fecha_term)),
            "target": "self",
        }

    def _excel_file(self, tabla, nombre, start, end):
        company = self.env["res.company"].search([], limit=1)
        data2 = BytesIO()
        workbook = xlsxwriter.Workbook(data2, {"in_memory": True})
        merge_format = workbook.add_format(
            {"bold": 1, "border": 1, "align": "center", "valign": "vcenter", "fg_color": "gray"}
        )
        datos = tabla
        range_start = "Desde: " + datetime.strptime(start, "%Y-%m-%d").strftime("%d/%m/%Y")
        range_end = "Hasta: " + datetime.strptime(end, "%Y-%m-%d").strftime("%d/%m/%Y")
        worksheet2 = workbook.add_worksheet(nombre)
        worksheet2.set_column("A:Z", 20)
        worksheet2.write("A1", company.name)
        worksheet2.write("A2", nombre)
        worksheet2.write("A4", range_start)
        worksheet2.write("A5", range_end)
        worksheet2.set_row(5, 20, merge_format)
        worksheet2.set_row(5, 20, merge_format)
        columnas = list(datos.columns.values)
        columns2 = [{"header": r} for r in columnas]
        porcent_format = workbook.add_format({"num_format": '#,###0.00" "%'})
        if nombre == "Efectividad de vendedores":
            for record in columns2[3:4]:
                record.update({"format": porcent_format})
        if nombre == "Gestion de cobranza":
            for record in columns2[8:14]:
                record.update({"format": porcent_format})
        data = datos.values.tolist()
        col3 = len(columns2) - 1
        col2 = len(data) + 6
        cells = xlsxwriter.utility.xl_range(5, 0, col2, col3)
        worksheet2.add_table(cells, {"data": data, "total_row": 1, "columns": columns2})
        workbook.close()
        data2 = data2.getvalue()
        return data2

    def _commission_excel_file(self, report_table, start, end):
        file = BytesIO()
        company = self.env["res.company"].search([], limit=1)

        with xlsxwriter.Workbook(file, {"in_memory": True}) as workbook:
            cell_format = workbook.add_format(
                {"bold": 1, "border": 1, "align": "center", "valign": "vcenter", "fg_color": "gray"}
            )

            for workbook_page, table in report_table.items():
                col_len = 0
                worksheet = workbook.add_worksheet(workbook_page)
                worksheet.set_column(f"{chr(65)}:{chr(len(table.keys()) + 64)}", 20)
                worksheet.write("A1", company.name)
                worksheet.write("A3", f"Desde: {start}")
                worksheet.write("A4", f"Hasta: {end}")

                for index, element in enumerate(table.items()):
                    header_column = f"{chr(index + 65)}6"
                    worksheet.write(header_column, element[0], cell_format)
                    col_len = len(element[1])

                    for index_cell, cell_data in enumerate(element[1]):
                        cell_position = f"{chr(index + 65)}{index_cell + 7}"
                        if isinstance(cell_data, float):
                            if element[0].startswith("%"):
                                element_format = workbook.add_format(
                                    {"num_format": '#,###0.00" "%'}
                                )
                                worksheet.write_number(cell_position, cell_data, element_format)

                            else:
                                element_format = workbook.add_format({"num_format": "#,###0.00"})
                                worksheet.write_number(cell_position, cell_data, element_format)
                        elif isinstance(cell_data, str):
                            worksheet.write_string(cell_position, cell_data)

                worksheet.autofilter(f"A6:{chr(len(table.keys()) + 64)}{col_len}")

        return file.getvalue()


class WizardMaxcanReportesExcel(models.TransientModel):
    _name = "wizard.reportes.comision.excel"
    file = fields.Binary()
    filename = fields.Char()


class MaxcanControlador(http.Controller):
    @http.route("/web/get_excel_commision", type="http", auth="user")
    @serialize_exception
    def download_document(self, informe, wizard, start, end):
        filecontent = ""
        report_obj = request.env["wizard.reportes.comision"]
        if informe == "Efectividad de vendedores":
            tabla = report_obj._efectividad(int(wizard))
            nombre = "Efectividad de vendedores"
        if informe == "Gestion de cobranza":
            tabla = report_obj._comisiones(int(wizard))
            nombre = "Gestion de cobranza"
            file_content = report_obj._commission_excel_file(tabla, start, end)

            return request.make_response(
                file_content,
                [
                    ("Content-Type", "application/pdf"),
                    ("Content-Length", len(file_content)),
                    ("Content-Disposition", content_disposition(nombre + ".xlsx")),
                ],
            )
        if informe == "Supervisores":
            tabla = report_obj._comisiones_supervisor(int(wizard))
            nombre = "Supervisores"
        if not tabla.empty and nombre:
            filecontent = report_obj._excel_file(tabla, nombre, start, end)
        if not filecontent:
            return Response(
                "No hay datos para mostrar", content_type="text/html;charset=utf-8", status=500
            )
        return request.make_response(
            filecontent,
            [
                ("Content-Type", "application/pdf"),
                ("Content-Length", len(filecontent)),
                ("Content-Disposition", content_disposition(nombre + ".xlsx")),
            ],
        )
