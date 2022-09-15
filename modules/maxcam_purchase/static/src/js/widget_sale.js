odoo.define("maxcam_purchase.HistorySalesWidget", function (require) {
  "use strict";

  var core = require("web.core");

  var Widget = require("web.Widget");
  var widget_registry = require("web.widget_registry");

  var rpc = require("web.rpc");

  var HistorySalesWidget = Widget.extend({
    template: "maxcam_purchase.historySales",
    events: _.extend({}, Widget.prototype.events, {
      "click .fa-area-chart": "_onClickButton",
    }),

    /**
     * @override
     * @param {Widget|null} parent
     * @param {Object} params
     */
    init: function (parent, params) {
      this.data = params.data;
      this.fields = params.fields;
      console.log(this.data);
      console.log(this.fields);
      this._super(parent);
    },

    start: function () {
      var self = this;
      return this._super.apply(this, arguments).then(function () {});
    },

    updateState: function (state) {
      this.$el.popover("dispose");
      var candidate = state.data[this.getParent().currentRow];
      if (candidate) {
        this.data = candidate.data;
        this.renderElement();
      }
    },

    _onClickButton: function () {
      // SE llama a la funcion get_id_wizard_solds para saber el id de la vista del wizard
      rpc
        .query({
          model: "purchase.order.line",
          method: "get_id_wizard_solds",
          args: [],
        })
        .then((response) => {
          //SE LLAMA LA VISTA DE TIPO PIVOTE al hacer click
          this.do_action({
            name: "Análisis de ventas",
            view_type: "form",
            view_mode: "pivot",
            target: "new",
            views: [[response.view_id, "pivot"]],
            res_model: "sale.report",
            type: "ir.actions.act_window",
            context: {
              default_product_id: this.data.product_id.data.id,
              search_default_product_id: this.data.product_id.data.id,
              pivot_measures: ["product_uom_qty", "qty_invoiced"],
              search_default_Sales: 1,
            },
          });
        })
        .catch((err) => console.error(err));
      this.$el.find(".fa-area-chart").prop("special_click", true);
    },
  });

  widget_registry.add("history_sales_widget", HistorySalesWidget);

  return HistorySalesWidget;
});
