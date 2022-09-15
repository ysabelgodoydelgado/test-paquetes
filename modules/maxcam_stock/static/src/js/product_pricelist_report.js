odoo.define('maxcam_stock.generate_pricelist_inherit', function (require) {
'use strict';

var GeneratePriceList = require('product.generate_pricelist').GeneratePriceList;
var QtyTagWidget = require('product.generate_pricelist').QtyTagWidget;
var ActionManager = require('web.ActionManager');
var framework = require('web.framework');
var session = require('web.session');

GeneratePriceList.include({
    events: {
        'click .o_action': '_onClickAction',
        'click .o_xlsx': '_onClickXlsx',
        'submit form': '_onSubmitForm',
    },
    init: function (parent, params) {
        this._super.apply(this, arguments);
        this.context.quantities = [1];
    },
    /**
     * Open form view of particular record when link clicked.
     *
     * @private
     * @param {jQueryEvent}
     */
    _onClickXlsx: function () {
        const reportName = _.str.sprintf('report_pricelist_xlsx?active_model=%s&active_ids=%s&pricelist_id=%s&quantities=%s',
            this.context.active_model,
            this.context.active_ids,
            this.context.pricelist_id || '',
            this.context.quantities.toString() || '1',
        );
        return this.do_action({
            type: 'ir.actions.report',
            report_type: 'xlsx',
            report_name: reportName,
            report_file: 'pricelist',
        });
    },
});

// QtyTagWidget.include({
//         template: 'product.report_pricelist_qty'
//     });

});