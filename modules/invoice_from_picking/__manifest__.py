# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.
{
    "name": "Invoice From Picking(Shipment/Delivery Order) Odoo",
    "version": "14.0.0.0",
    "depends": ['base', 'account', 'sale_management', 'stock', 'purchase', 'sale_stock','max_cam_dispatch'],
    "author": "BrowseInfo",
    "summary": "customer invoice from picking vendor invoices from Picking customer invoice from delivery order vendor bill from picking vendor bill from receipt invoice from Shipment invoice from Shipment Account invoice from picking single invoice from delivery order",
    'description': """
    
    Generate single invoice from multiple delivery order, Create single invoice from multiple shipment order, Single invoice for multiple orders, single invoice from Order, multiple delivery order generate single invoice, easy invoice from picking, invoice in picking
Generate single invoice from multiple delivery order, Create single invoice from multiple shipment order, Single invoice for multiple orders, single invoice from Orders, multiple delivery generate single invoice, easy invoice from picking.
invoice in picking, retrun invoice from picking, return invoice from shipment, return invoice from Delivery.
Picking from Customer Invoice
      Picking from Customer Invoice
      Invoice From Picking
      vendor invoices from Picking
      vendor invoices from Picking (Delivery Order/ Incoming Shipment
      vendor invoices from Incoming Shipment
      vendor invoices from Delivery Order
      invoices from Delivery Order
      invoices from Incoming Shipment
      invoice from Shipment
      Stock Move from Invoice
      Stock Picking from Invoice and Vendor Bill
      Stock Picking from Vendor Bill
      Picking from Vendor Bill
      Vendor Bill to Incoming Shipment
      invoice from Shipment
Account invoice from picking
invoice from stock fr    
Generate single invoice from multiple Delivery Order, Create single invoice from multiple Delivery Order, Single invoice for multiple Delivery Order, single invoice from Orders, multiple Picking generate single invoice, easy invoice from Delivery order
Generate single invoice from multiple Shipment, Create single invoice from multiple Shipment, Single invoice for multiple Shioment, single invoice from Picking, multiple shipment generate single invoice, easy invoice from incoming shipment
    Generate Single invoice from Multiple Picking ,generate invoice from delivery Order, generate invoice from picking, generate invoice from shipment.
    invoice by picking, invoice by delivery order, invoice by shipment
Gerar uma ??nica fatura de v??rios pedidos de entrega, criar uma ??nica fatura de v??rios pedidos de remessa, fatura ??nica para v??rios pedidos, fatura ??nica do pedido, v??rios pedidos de remessa geram fatura ??nica, fatura f??cil de picking, fatura na retirada
Gere uma fatura ??nica a partir de v??rios pedidos de entrega, crie uma ??nica fatura a partir de v??rios pedidos de remessa, fatura individual para v??rios pedidos, fatura ??nica de pedidos, v??rias entregas geram fatura ??nica, fatura f??cil de picking.

    fatura na retirada, fatura da retirada da fatura, retorno da fatura da expedi????o, retorno da fatura da entrega.
    
Gere uma ??nica fatura de v??rios pedidos, crie uma ??nica fatura a partir de v??rios pedidos, uma ??nica fatura para v??rios pedidos, uma ??nica fatura de pedidos, v??rios picking geram uma ??nica fatura, uma fatura f??cil a partir de uma ordem de entrega
Gere uma ??nica fatura de v??rias remessas, crie uma ??nica fatura a partir de v??rias remessas, uma ??nica fatura para v??rios itens, uma ??nica fatura de retirada, v??rias remessas geram uma ??nica fatura, fatura f??cil a partir da remessa de entrada
    Gere uma ??nica fatura a partir de uma sele????o m??ltipla, gere uma fatura a partir da ordem de entrega, gere a fatura a partir do picking, gere a fatura a partir da remessa.
    fatura por picking, fatura por ordem de entrega, fatura por remessa

?????????? ???????????? ?????????? ???? ?????? ?????????? ?????????? ?? ?????????? ???????????? ?????????? ???? ?????? ?????? ?????????? ?? ???????????? ?????????? ???????????? ???????????? ?? ???????????? ?????????? ???? ?????????? ?? ?????? ?????????? ?????????? ?????????? ???????????? ?????????? ?? ???????????? ???????? ???? ???????????????? ?? ???????????? ???? ??????
?????????? ???????????? ?????????? ???? ?????? ?????????? ?????????? ?? ?????????? ???????????? ?????????? ???? ?????? ?????? ?????????? ?? ???????????? ?????????? ???????????? ???????????? ?? ???????????? ?????????? ???? ?????????????? ?? ?????????? ?????????? ?????????? ???????????? ?????????? ?? ???????????? ???????? ???? ??????.

    ???????????? ???? ?????? ?? ?????????????? ???????????????? ???? ???????????? ?? ???????????????? ???????????? ???? ?????????? ?? ???????????? ???????????? ???? ??????????????.
    
?????????? ???????????? ?????????? ???? ?????? ?????????? ?????????? ?? ?????????? ???????????? ?????????? ???? ?????? ?????????? ?????????? ?? ???????????? ?????????? ???????? ?????????? ?????????? ?? ???????????? ?????????? ???? ?????????????? ?? ???????????? ???????????? ?????????? ???????????? ?????????? ?? ???????????? ???????? ???? ?????? ??????????????
?????????? ???????????? ?????????? ???? ?????? ?????????? ?? ?????????? ???????????? ?????????? ???? ?????? ?????????? ?? ???????????? ?????????? ???????? Shioment ?? ???????????? ?????????? ???? Picking ?? ?????? ?????????? ?????????? ???????????? ?????????? ?? ???????????? ???????? ???? ???????? ??????????
    ?????????? ???????????? ?????????? ???? ???????????? ???????????? ?? ???????????? ???????????? ???? ?????????????? ???????????? ?? ???????????? ???????????? ???? ?????? ?? ???????????? ???????????????? ???? ??????????.
    ???????????? ???? ???????? ???????????? ?? ???????????? ???????????? ?????? ?????????????? ?? ???????????????? ???? ???????? ??????????
G??n??rer une facture unique ?? partir d'un bon de livraison multiple, Cr??er une facture unique ?? partir de plusieurs commandes, Facture unique pour plusieurs commandes, Facture unique ?? partir de la commande, Bon de livraison multiple g??n??rer une facture unique, Facture facile ?? cueillir, Facture ?? la cueillette
G??n??rer une facture unique ?? partir d'un bon de livraison multiple, Cr??er une facture unique ?? partir d'une commande d'exp??dition multiple, Facture unique pour plusieurs commandes, Facture unique des commandes, Livraison multiple g??n??rer une facture unique, Facture facile de la cueillette.

    Facturer ?? la cueillette, r??tracter la facture de la cueillette, retourner la facture de l'exp??dition, retourner la facture de la livraison.
    
G??n??rer une facture unique ?? partir de plusieurs ordres de livraison, Cr??er une facture unique ?? partir de plusieurs ordres de livraison, Facture unique pour plusieurs ordres de livraison, Facture unique des commandes, Facturation multiple g??n??rer une facture unique, Facture facile ?? partir du bon de livraison
G??n??rer une facture unique ?? partir de plusieurs envois, Cr??er une facture unique ?? partir de plusieurs envois, Facture unique pour plusieurs shioments, facture unique ?? partir de pr??l??vement, plusieurs envois g??n??rer une facture unique, facture facile ?? partir de l'envoi entrant
    G??n??rer une facture unique ?? partir de la cueillette multiple, g??n??rer la facture ?? partir de la commande, g??n??rer la facture ?? partir de la cueillette, g??n??rer la facture ?? partir de l'exp??dition.
    facture par pr??l??vement, facture par bon de livraison, facture par envoi

Genere una sola factura a partir de varias ??rdenes de entrega, cree una sola factura a partir de varias ??rdenes de env??o, una sola factura para varias ??rdenes, una sola factura a partir de una orden, una orden de entrega m??ltiple genere una sola factura, una factura f??cil para recoger, una factura para recoger
Genere una sola factura a partir de varias ??rdenes de entrega, cree una ??nica factura a partir de varias ??rdenes de env??o, una factura ??nica para pedidos m??ltiples, una sola factura desde pedidos, una entrega m??ltiple genere una sola factura, una factura f??cil de elegir.

    factura en la selecci??n, devoluci??n de la factura de la recolecci??n, devoluci??n de la factura del env??o, devoluci??n de la factura de la Entrega.
    
Genere una sola factura desde una orden de entrega m??ltiple, cree una sola factura desde una orden de entrega m??ltiple, una sola factura por una orden de entrega m??ltiple, una sola factura desde pedidos, una selecci??n m??ltiple genere una sola factura, una factura f??cil desde una orden de entrega
Genere una sola factura desde un Env??o m??ltiple, Cree una sola factura desde un Env??o m??ltiple, Una sola factura por Shioment m??ltiple, Una sola factura desde Picking, Env??o m??ltiple genere una sola factura, Factura sencilla desde el env??o entrante
    Genere una sola factura desde varias selecciones, genere facturas desde el pedido de entrega, genere facturas desde picking, genere facturas desde el env??o.
    factura por picking, factura por orden de entrega, factura por env??o


""",
    'category': 'Accounting',
    "website": "https://www.browseinfo.in",
    "data": [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'wizard/stock_invoice_onshipping.xml',
        'views/inherited_stock_picking.xml',
        'views/inherited_invoice_view.xml',
        'views/inherited_purchase.xml',
        'views/inherited_sale_order_view.xml',
        'views/stock_picking.xml',
        
    ],
    "price": 29,
    "currency": 'EUR',
    'qweb': [
    ],
    "auto_install": False,
    "installable": True,
    'live_test_url':'https://youtu.be/mzAseYyeyw0',
    "images": ["static/description/Banner.png"],
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
