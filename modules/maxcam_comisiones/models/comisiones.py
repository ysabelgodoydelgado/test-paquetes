import logging
from collections import OrderedDict
from datetime import datetime
from re import A

import pandas as pd
from odoo import api, models, fields
from odoo.tools.float_utils import float_is_zero

_logger = logging.getLogger(__name__)


class ReporteComisiones(models.TransientModel):
    _inherit = "wizard.reportes.comision"

    def _comisiones(self, wizard=False):
        if wizard:
            wiz = self.search([("id", "=", wizard)])
        else:
            wiz = self

        search_domain = wiz._get_domain()
        report_commissions = (
            self.env["commission.policy"].sudo().search([("is_report_range", "=", True)])
        )
        invoices = self.env["account.move"].search(search_domain)
        users = wiz.env["hr.employee"].search([])
        report_table = self.create_commission_data_table(report_commissions, invoices, users)

        return report_table

    @api.model
    def create_commission_data_table(self, report_commissions, invoices, users) -> OrderedDict:
        date_today = fields.Date.context_today(self)
        report_table = self._report_table_template(report_commissions)
        report_invoice_to_exclude_list = []

        for commission in report_commissions:
            pk = commission.display_name
            policy_key = f"Rango {pk}"

            for user in users:
                commission_ranges = self.get_range_lines_dict(commission)
                percentage_total = []
                seller_total_amount_untaxed: float = 0.0
                seller_due_amount_untaxed: float = 0.00
                seller_invoices = invoices.filtered(
                    lambda i: i.seller_id.id == user.id
                    and i.picking_ids
                    and commission.policy_type
                    in i.picking_ids[0].commission_images_id.mapped("policy_type")
                    and i.state in ["posted"]
                    and i.payment_state not in ["paid", "in_payment"]
                )

                for invoice in seller_invoices:
                    if self._has_commission_greater_hierarchy(
                        commission, invoice, "product", "product"
                    ):
                        continue
                    if self._has_commission_greater_hierarchy(
                        commission, invoice, "product", "category"
                    ):
                        continue
                    if self._has_commission_greater_hierarchy(
                        commission, invoice, "product", "brand"
                    ):
                        continue
                    if self._has_commission_greater_hierarchy(commission, invoice, "client"):
                        continue
                    if invoice.id in report_invoice_to_exclude_list:
                        continue

                    report_invoice_to_exclude_list.append(invoice.id)
                    days_expired = abs((invoice.invoice_date_due - date_today).days)
                    seller_total_amount_untaxed += invoice.amount_untaxed

                    for cl in commission.commission_line_ids:
                        if cl.date_from <= days_expired <= cl.date_until or (
                            cl.date_from <= days_expired and cl.date_until == 0
                        ):
                            if not cl.sudo().not_applied:
                                seller_due_amount_untaxed += invoice.amount_untaxed

                            if cl.date_from <= 0:
                                key = f"0 - {cl.date_until}"
                                commission_ranges[key] += invoice.amount_untaxed
                            elif cl.date_until == 0:
                                key = str(cl.date_from)
                                commission_ranges[key] += invoice.amount_untaxed
                            else:
                                key = f"{cl.date_from} - {cl.date_until}"
                                commission_ranges[key] += invoice.amount_untaxed

                report_table[policy_key]["Vendedor"].append(user.name)
                report_table[policy_key]["Total Cartera"].append(seller_total_amount_untaxed)

                for key, cl in zip(commission_ranges.keys(), commission.commission_line_ids):
                    range_key = f"{key} días" if "-" in key else f"Mayor a {key}"
                    range_key_mod = f"% {key}" if "-" in key else f"% Mayor a {key}"

                    report_table[policy_key][range_key].append(commission_ranges[key])

                    if float_is_zero(seller_total_amount_untaxed, precision_digits=2):
                        total_amount_untaxed: float = 0.00
                    else:
                        total_amount_untaxed: float = (
                            commission_ranges[key] / seller_total_amount_untaxed
                        )

                    if cl.not_applied:
                        percentage_amount: float = 0.00
                    else:
                        percentage_amount: float = 1 + (cl.percentage_report / 100)
                    result = total_amount_untaxed * percentage_amount

                    percentage_total.append(result)
                    report_table[policy_key][range_key_mod].append(result)

                report_table[policy_key]["Cartera Vencida"].append(seller_due_amount_untaxed)
                report_table[policy_key]["% Total"].append(sum(percentage_total))
                report_table["Total"][f"% Total {policy_key}"].append(sum(percentage_total))

        report_table["Total"]["Vendedor"] = users.mapped("name")
        total_list = self.calculate_total_per_page(zip(*report_table["Total"].values()))
        report_table["Total"]["% de Totales"] = total_list

        return report_table

    @api.model
    def calculate_total_per_page(self, page_values_zipped) -> float:
        total_list = []
        for page_values in page_values_zipped:
            new_page_values = self.filter_str_and_zero_float(page_values)
            sum_pages = (sum(new_page_values) / len(new_page_values)) if new_page_values else 0.00
            total_list.append(sum_pages)

        return total_list

    @api.model
    def filter_str_and_zero_float(self, total_pages_tuple) -> list:
        new_total_pages_tuple = []
        for page_total in total_pages_tuple:
            if isinstance(page_total, float) and not float_is_zero(page_total, precision_digits=2):
                new_total_pages_tuple.append(page_total)

        return new_total_pages_tuple

    @api.model
    def _has_commission_greater_hierarchy(
        self, commission, invoice, commission_type, product_commission_type=None
    ) -> bool:
        if not product_commission_type:
            product_commission_type = ""

        veridic_type_commission = []
        picking = invoice.picking_ids[0]
        commission_i = picking.commission_images_id

        comm_i = commission_i.filtered(
            lambda c: c.policy_type == commission_type
            or c.product_commission_type == product_commission_type
        )
        for ci in comm_i:
            veridic_type_commission.append(
                ci.policy_type != commission.policy_type
                or ci.product_commission_type != commission.product_commission_type
            )

        if veridic_type_commission:
            return all(veridic_type_commission)

        return False

    @api.model
    def _report_table_template(self, report_commissions) -> OrderedDict:
        """
        A method that generate a grouped-by-commission dictionary to store
        the seller data report.

        :param report_commissions: An 'comission.policy' object to group
        the report.
        :return: The pre-formatted dictionary with the report-active
        commissions.
        """
        commission_table = OrderedDict()
        for commission in report_commissions:
            policy_key = commission.display_name
            key = f"Rango {policy_key}"
            commission_table[key] = OrderedDict(
                {
                    "Vendedor": [],
                    "Total Cartera": [],
                }
            )

            for cl in commission.commission_line_ids:
                if cl.date_from <= 0:
                    range_key = f"0 - {cl.date_until} días"
                elif not cl.date_until:
                    range_key = f"Mayor a {cl.date_from}"
                else:
                    range_key = f"{cl.date_from} - {cl.date_until} días"
                commission_table[key][range_key] = []

            commission_table[key]["Cartera Vencida"] = []

            for cl in commission.commission_line_ids:
                if cl.date_from <= 0:
                    range_key = f"% 0 - {cl.date_until}"
                elif not cl.date_until:
                    range_key = f"% Mayor a {cl.date_from}"
                else:
                    range_key = f"% {cl.date_from} - {cl.date_until}"
                commission_table[key][range_key] = []

            commission_table[key]["% Total"] = []

        total_dict_keys = OrderedDict(
            {**{"Vendedor": []}, **{f"% Total {key}": [] for key in commission_table.keys()}}
        )
        commission_table["Total"] = total_dict_keys

        return commission_table

    @api.model
    def get_range_lines_dict(self, commission) -> OrderedDict:
        dictionary_ranges = OrderedDict()
        for cl in commission.commission_line_ids:
            if cl.date_from <= 0:
                range_key = f"0 - {cl.date_until}"
            elif not cl.date_until:
                range_key = str(cl.date_from)
            else:
                range_key = f"{cl.date_from} - {cl.date_until}"

            dictionary_ranges[range_key]: float = 0.0

        return dictionary_ranges

    def get_date_last_payment(self, f):
        last_date = False
        for partial, amount, counterpart_line in f._get_reconciled_invoices_partials():
            _logger.info("Fecha de pago")
            _logger.info(counterpart_line.date)
            if not last_date:
                last_date = counterpart_line.date
            elif counterpart_line.date > last_date:
                last_date = counterpart_line.date
        return last_date

    def _comisiones_supervisor(self, wizard=False):
        if wizard:
            wiz = self.search([("id", "=", wizard)])
        else:
            wiz = self
        date_today = datetime.now().strftime("%Y-%m-%d")
        # search_domain = []
        # search_domain += [('company_id', '=', wiz.company_id.id)]
        # search_domain += [('invoice_date', '>=', wiz.fecha_inicio)]
        # search_domain += [('invoice_date', '<=', wiz.fecha_term)]
        # search_domain += [('move_type', 'in', ['out_invoice'])]
        # docs = self.env['account.move'].search(search_domain)

        search_domain = []
        search_domain += [("company_id", "=", wiz.company_id.id)]
        search_domain += [("date", ">=", wiz.fecha_inicio)]
        search_domain += [("date", "<=", wiz.fecha_term)]
        search_domain += [("state", "in", ["draft", "reported", "approved"])]

        # search_domain += [('move_type', 'in', ['out_invoice'])]
        # docs = self.env['account.move'].search(search_domain)
        docs = self.env["hr.expense"].search(search_domain)
        if wiz.supervisor_id:
            user_supervisor_id = wiz.env["hr.employee"].search(
                [("is_supervisor", "=", True), ("supervisor_id", "=", wiz.supervisor_id.id)]
            )
        else:
            user_supervisor_id = wiz.env["hr.employee"].search([("is_supervisor", "=", True)])
        user_ids = wiz.env["hr.employee"].search([])

        dic = OrderedDict(
            [
                ("Supervisor", ""),
                ("Vendedor", ""),
                ("Total Cartera", 0.00),
                ("0-15 DIAS", 0.00),
                ("16-20 DIAS", 0.00),
                ("21-30 DIAS", 0.00),
                ("30-40 DIAS", 0.00),
                ("MAYOR A 40 DIAS", 0.00),
                ("0-15", 0.00),
                ("16-20", 0.00),
                ("21-30", 0.00),
                ("30-40", 0.00),
                ("MAYOR A 40", 0.00),
                ("TOTAL", 0.00),
            ]
        )
        lista = []
        for us in user_supervisor_id:
            data_us = {
                "column_0": 0,
                "column_1": 0,
                "column_2": 0,
                "column_3": 0,
                "column_4": 0,
                "column_5": 0,
            }
            for u in user_ids.filtered(lambda i: i.supervisor_id.id == us.id):
                data = {
                    "column_0": 0,
                    "column_1": 0,
                    "column_2": 0,
                    "column_3": 0,
                    "column_4": 0,
                    "column_5": 0,
                }
                gasto = docs.filtered(lambda i: i.employee_id.id == u.id)
                dicti = OrderedDict()
                dicti.update(dic)
                for gt in gasto:
                    for gf in gt.invoice_ids.filtered(lambda a: a.move_type in ["out_invoice"]):
                        # last_payment = self.get_date_last_payment(gf)
                        # _logger.info('USO LA FECHA')
                        # _logger.info(str(last_payment))
                        # days_expired = -1 * (
                        #            datetime.strptime(str(gf.invoice_date_due), '%Y-%m-%d') - datetime.strptime(
                        #        str(last_payment),
                        #        '%Y-%m-%d')).days
                        days_expired = gf.collection_days
                        data["column_0"] += gf.amount_untaxed
                        data_us["column_0"] += gf.amount_untaxed
                        if days_expired <= 15:
                            data["column_1"] += gf.amount_untaxed
                            data_us["column_1"] += gf.amount_untaxed
                        elif 16 <= days_expired <= 20:
                            data["column_2"] += gf.amount_untaxed
                            data_us["column_2"] += gf.amount_untaxed
                        elif 21 <= days_expired <= 30:
                            data["column_3"] += gf.amount_untaxed
                            data_us["column_3"] += gf.amount_untaxed
                        elif 31 <= days_expired <= 40:
                            data["column_4"] += gf.amount_untaxed
                            data_us["column_4"] += gf.amount_untaxed
                        elif 40 < days_expired:
                            data["column_5"] += gf.amount_untaxed
                            data_us["column_5"] += gf.amount_untaxed
                dicti["Supervisor"] = us.name
                dicti["Vendedor"] = u.name
                dicti["Total Cartera"] = data["column_0"]
                dicti["0-15 DIAS"] = data["column_1"]
                dicti["16-20 DIAS"] = data["column_2"]
                dicti["21-30 DIAS"] = data["column_3"]
                dicti["30-40 DIAS"] = data["column_4"]
                dicti["MAYOR A 40 DIAS"] = data["column_5"]
                col_a = data["column_1"] * 0.006
                col_b = data["column_2"] * 0.005
                col_c = data["column_3"] * 0.004
                col_d = data["column_4"] * 0.003
                dicti["0-15"] = col_a
                dicti["16-20"] = col_b
                dicti["21-30"] = col_c
                dicti["30-40"] = col_d
                dicti["MAYOR A 40"] = 0.00
                dicti["TOTAL"] = col_a + col_b + col_c + col_d
                lista.append(dicti)
            dicti = OrderedDict()
            dicti.update(dic)
            dicti["Supervisor"] = us.name
            dicti["Vendedor"] = ""
            dicti["Total Cartera"] = data_us["column_0"]
            dicti["0-15 DIAS"] = data_us["column_1"]
            dicti["16-20 DIAS"] = data_us["column_2"]
            dicti["21-30 DIAS"] = data_us["column_3"]
            dicti["30-40 DIAS"] = data_us["column_4"]
            dicti["MAYOR A 40 DIAS"] = data_us["column_5"]
            col_as = data_us["column_1"] * 0.006
            col_bs = data_us["column_2"] * 0.005
            col_cs = data_us["column_3"] * 0.004
            col_ds = data_us["column_4"] * 0.003
            dicti["0-15"] = col_as
            dicti["16-20"] = col_bs
            dicti["21-30"] = col_cs
            dicti["30-40"] = col_ds
            dicti["MAYOR A 40"] = 0.00
            dicti["TOTAL"] = col_as + col_bs + col_cs + col_ds
            lista.append(dicti)
        tabla = pd.DataFrame(lista)
        return tabla.fillna(0)
