# -*- coding: utf-8 -*-
import csv
import datetime
import json
import logging
import os

from odoo import models, fields, api, _
from odoo.tools import float_is_zero

_logger = logging.getLogger(__name__)


class MaxcamSellerAccountMove(models.Model):
    _inherit = "account.move"

    seller_id = fields.Many2one(
        "hr.employee", related="partner_id.seller_id", string="Seller", store=True
    )
    paid_seller = fields.Selection(
        [("not_paid", "not paid"), ("process", "in process"), ("paid", "paid")],
        default="not_paid",
    )
    reception_date_client = fields.Date(
        string="Fecha de recepción del cliente",
        help="indicates when the invoice signed by the client is received after dispatch",
    )
    last_payment_date = fields.Date(
        string="Fecha ultimo pago", compute="_last_payment_date", store=True
    )
    cash_reconcile_date = fields.Date(string="Fecha conciliacion efectivo")

    hr_expense_id = fields.Many2one("hr.expense", string="Gasto asociado a vendedor", index=True)
    commission = fields.Float()  # deprecated
    total_commission = fields.Float(compute="_compute_total_commission_of_invoice", store=True)
    commission_discount = fields.Float(
        compute="_compute_discount_invoice",
        store=True,
        help="Descuento de pagos de rectificativas",
    )

    discount_invoice = fields.Many2many(
        "account.move", "reversal_id", "move_id", compute="_compute_discount_invoice"
    )
    collection_days = fields.Integer(compute="_compute_collection_days", store=True)

    @api.depends("amount_residual")
    def _compute_discount_invoice(self):
        for record in self:
            commission_discount = 0
            discount_invoice = False
            if (
                record.currency_id.is_zero(record.amount_residual)
                and record.move_type == "out_invoice"
            ):
                if record.invoice_payments_widget:
                    discount_invoice, commission_discount = self.get_discount_invoice(
                        record.invoice_payments_widget
                    )
                    discount_invoice = self.env["account.move"].search(
                        [("id", "in", discount_invoice)]
                    )
            record.commission_discount = commission_discount * -1
            record.discount_invoice = discount_invoice

    def get_discount_invoice(self, payments):
        rec_ids = []
        total_commission = 0
        res = json.loads(payments)
        if res and len(res.get("content")) > 0:
            for payment in res.get("content"):
                account_payment_id = payment.get("account_payment_id", False)
                if not account_payment_id:
                    rec_id = payment.get("move_id", False)
                    if rec_id:
                        rec_invoice = self.env["account.move"].browse(int(rec_id))
                        if rec_invoice.exists():
                            if rec_invoice.reversed_entry_id.exists():
                                rec_total = 0
                                reversed_invoice = rec_invoice.reversed_entry_id
                                for rec_line in rec_invoice.invoice_line_ids:

                                    reversed_line = reversed_invoice.invoice_line_ids.filtered(
                                        lambda rl: rl.product_id.id == rec_line.product_id.id
                                    )
                                    rec_total += self.calculate_commission_product(
                                        rec_line.price_subtotal,
                                        reversed_line.commission,
                                        rec_invoice.currency_id.decimal_places,
                                    )
                                total_commission += rec_total

                                # total_commission += self.calculate_total_commission(
                                #     float(payment.get("amount")),
                                #     rec_invoice.reversed_entry_id.total_commission,
                                #     rec_invoice.reversed_entry_id.amount_untaxed_signed,
                                # )
                            rec_ids.append(rec_invoice.id)
        return rec_ids, total_commission

    def calculate_total_commission(self, product_amount_untaxed, product_rec_commission):
        return product_amount_untaxed * (product_rec_commission / 100)

    @api.depends("reception_date_client", "last_payment_date")
    def _compute_collection_days(self):
        for record in self:
            collection_days = 0
            if record.reception_date_client and record.last_payment_date:
                expired = fields.Date.from_string(
                    record.last_payment_date
                ) - fields.Date.from_string(record.reception_date_client)
                collection_days = expired.days
            record.collection_days = collection_days

    @api.depends("amount_residual", "cash_reconcile_date")
    def _last_payment_date(self):
        for record in self:
            if (
                record.currency_id.is_zero(record.amount_residual)
                and record.move_type == "out_invoice"
            ):
                if record.invoice_payments_widget:
                    settlement_date = self.get_max_payment_date(record.invoice_payments_widget)
                    settlement_date = fields.Date.from_string(settlement_date)
                else:
                    settlement_date = False
            else:
                settlement_date = False
            record.last_payment_date = (
                settlement_date if not record.cash_reconcile_date else record.cash_reconcile_date
            )

    @staticmethod
    def get_max_payment_date(payments):
        dates = []
        res = json.loads(payments)
        if res and len(res.get("content")) > 0:
            for payment in res.get("content"):
                account_payment_id = payment.get("account_payment_id", False)
                if account_payment_id:
                    dates.append(payment.get("date", False))
        if len(dates) > 0:
            settlement_date = max(dates)
        else:
            settlement_date = False
        return settlement_date

    @api.depends("total_commission", "commission_discount", "last_payment_date")
    def _compute_total_commission_of_invoice(self):
        for move in self:
            total_commission = 0
            if move.last_payment_date and move.amount_untaxed:
                for line in move.invoice_line_ids:
                    total_commission += move.calculate_commission_product(
                        line.price_subtotal,
                        line.commission,
                        move.currency_id.decimal_places,
                    )

                if total_commission != 0:
                    total_commission -= abs(move.commission_discount)

            move.total_commission = total_commission

    @api.model
    def calculate_commission_product(self, amount_untaxed, commission, decimal_places):
        total_commission = 0
        if not float_is_zero(commission, precision_digits=2) and amount_untaxed:
            total = (commission / 100) * amount_untaxed
            total_commission = round(total, decimal_places)

        return total_commission

    def set_dates_maxcam_1(self):
        _logger.info("========ejecuto cron=========")
        url = os.path.dirname(os.path.abspath(__file__))
        with open(url + "/hoja_1.csv") as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=",")
            line_count = 0
            line_count_i = 0
            for row in csv_reader:
                if line_count == 0:
                    _logger.info("Column names are %s", row)
                    line_count += 1
                else:
                    _logger.info("fecha %s", row[1])
                    _logger.info("numero %s", row[0])
                    # print("tasa",row[2])
                    inv = self.env["account.move"].sudo().search([("name", "=", row[0])], limit=1)
                    if inv:
                        line_count_i += 1
                        inv.write(
                            {
                                "reception_date_client": datetime.datetime.strptime(
                                    row[1], "%Y-%m-%d"
                                ).date()
                            }
                        )
                    line_count += 1
            _logger.info("Processed lines %s.", line_count)
            _logger.info("facturas encontradas %s.", line_count_i)

    def set_dates_maxcam_2(self):
        _logger.info("========ejecuto cron=========")
        url = os.path.dirname(os.path.abspath(__file__))
        with open(url + "/hoja_2.csv") as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=",")
            line_count = 0
            line_count_i = 0
            for row in csv_reader:
                if line_count == 0:
                    _logger.info("Column names are %s", row)
                    line_count += 1
                else:
                    _logger.info("fecha %s", row[1])
                    _logger.info("numero %s", row[0])
                    # print("tasa",row[2])
                    inv = self.env["account.move"].sudo().search([("name", "=", row[0])], limit=1)
                    if inv:
                        line_count_i += 1
                        inv.write(
                            {
                                "reception_date_client": datetime.datetime.strptime(
                                    row[1], "%Y-%m-%d"
                                ).date()
                            }
                        )
                    line_count += 1
            _logger.info("Processed lines %s.", line_count)
            _logger.info("facturas encontradas %s.", line_count_i)

    def set_dates_maxcam_3(self):
        _logger.info("========ejecuto cron=========")
        url = os.path.dirname(os.path.abspath(__file__))
        with open(url + "/hoja_3.csv") as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=",")
            line_count = 0
            line_count_i = 0
            for row in csv_reader:
                if line_count == 0:
                    _logger.info("Column names are %s", row)
                    line_count += 1
                else:
                    _logger.info("fecha %s", row[1])
                    _logger.info("numero %s", row[0])
                    # print("tasa",row[2])
                    inv = self.env["account.move"].sudo().search([("name", "=", row[0])], limit=1)
                    if inv:
                        line_count_i += 1
                        inv.write(
                            {
                                "reception_date_client": datetime.datetime.strptime(
                                    row[1], "%Y-%m-%d"
                                ).date()
                            }
                        )
                    line_count += 1
            _logger.info("Processed lines %s.", line_count)
            _logger.info("facturas encontradas %s.", line_count_i)

    def set_dates_maxcam_4(self):
        _logger.info("========ejecuto cron=========")
        url = os.path.dirname(os.path.abspath(__file__))
        with open(url + "/hoja_4.csv") as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=",")
            line_count = 0
            line_count_i = 0
            for row in csv_reader:
                if line_count == 0:
                    _logger.info("Column names are %s", row)
                    line_count += 1
                else:
                    _logger.info("fecha %s", row[1])
                    _logger.info("numero %s", row[0])
                    # print("tasa",row[2])
                    inv = self.env["account.move"].sudo().search([("name", "=", row[0])], limit=1)
                    if inv:
                        line_count_i += 1
                        inv.write(
                            {
                                "reception_date_client": datetime.datetime.strptime(
                                    row[1], "%Y-%m-%d"
                                ).date()
                            }
                        )
                    line_count += 1
            _logger.info("Processed lines %s.", line_count)
            _logger.info("facturas encontradas %s.", line_count_i)

    def action_show_invoice_resume(self):
        view = self.env.ref(
            "maxcam_commission_policies.invoice_commission_summary_wizard_form_view"
        )
        invoice_lines = self.invoice_line_ids.filtered(lambda x: x.product_id.type == "product")

        return {
            "name": _("Resumen de Factura"),
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "invoice.commission.summary.wizard",
            "views": [(view.id, "form")],
            "view_id": view.id,
            "target": "new",
            "flags": {"mode": "readonly"},
            "context": dict(
                self.env.context,
                default_name=self.name,
                default_invoice_line_ids=invoice_lines.ids,
            ),
        }

    def recalculate_total_commission(self):
        invoices = self.env["account.move"].search(
            [
                ("create_date", ">=", datetime.datetime(2022, 8, 4)),
                ("move_type", "=", "out_invoice"),
                ("picking_ids", "!=", False),
            ]
        )
        filtered_invoices = invoices.filtered(
            lambda x: "product" in x.picking_ids.commission_images_id.mapped("policy_type")
        )
        _logger.warning("Len of negative_commissions: %s" % len(filtered_invoices))

        for invoice in filtered_invoices:
            _logger.warning("Factura %s", invoice)
            _logger.warning("Factura con pre-comision negativa %s", invoice.total_commission)
            invoice._compute_discount_invoice()
            invoice._compute_total_commission_of_invoice()
            _logger.warning("Factura con post-comision negativa %s", invoice.total_commission)
