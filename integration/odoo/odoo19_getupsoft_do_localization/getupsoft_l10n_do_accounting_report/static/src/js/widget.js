odoo.define('getupsoft_l10n_do_accounting_report.dgii_report_widget', function (require) {
    "use strict";

    var field_registry = require('web.field_registry');
    var basic_fields = require('web.basic_fields');

    var UrlDgiiReportsWidget = basic_fields.UrlWidget.extend({
        init: function () {
            this._super.apply(this, arguments);

            this.isRnc = this.nodeOptions.is_rnc || false;

            var recordField = this.nodeOptions.invoice_field || 'invoice_id';
            var record = recordField && this.record.data[recordField];
            if (record && (record.type && record.type === "record")) {
                this.invoiceId = record.res_id;
            } else {
                this.invoiceId = null;
            }

            this.isModify = this.nodeOptions.is_modify | false;

        },
        _renderReadonly: function () {
            this._super.call(this, arguments);

            if (this.el && this.el.firstChild) {
                var url = `dgii_reports/`;

                if (this.isRnc) {
                    url += `?rnc=${this.value}`;
                } else if (this.invoiceId) {
                    url += `?invoice_id=${this.invoiceId}`;
                } else if (this.invoiceId && this.isModify) {
                    url += `?invoice_id=${this.invoiceId}&modify=${this.value}`;
                }

                this.el.firstChild.href = url;
            }
        },
    });

    field_registry.add('dgii_reports_url', UrlDgiiReportsWidget);

    return {
        UrlDgiiReportsWidget: UrlDgiiReportsWidget,
    };

});
