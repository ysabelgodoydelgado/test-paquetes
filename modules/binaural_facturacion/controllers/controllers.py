# -*- coding: utf-8 -*-
from odoo import http

# class BinExemptAndTaxedPurchase(http.Controller):
#     @http.route('/bin_exempt_and_taxed_purchase/bin_exempt_and_taxed_purchase/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/bin_exempt_and_taxed_purchase/bin_exempt_and_taxed_purchase/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('bin_exempt_and_taxed_purchase.listing', {
#             'root': '/bin_exempt_and_taxed_purchase/bin_exempt_and_taxed_purchase',
#             'objects': http.request.env['bin_exempt_and_taxed_purchase.bin_exempt_and_taxed_purchase'].search([]),
#         })

#     @http.route('/bin_exempt_and_taxed_purchase/bin_exempt_and_taxed_purchase/objects/<model("bin_exempt_and_taxed_purchase.bin_exempt_and_taxed_purchase"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('bin_exempt_and_taxed_purchase.object', {
#             'object': obj
#         })