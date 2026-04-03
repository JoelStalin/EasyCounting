odoo.define('l10n_do_accounting.l10n_do_accounting', function (require) {
    "use strict";

    var basicFields = require('web.basic_fields');
    var field_registry = require('web.field_registry');
   
    var FieldDgiiAutoComplete = basicFields.FieldChar.extend({
        _prepareInput: function ($input) {
            this._super.apply(this, arguments);

            $input.autocomplete({
                source: "/dgii_ws/",
                minLength: 3,
                select: function (event, ui) {
                    var $rncInput = $("input[name='vat']").length ? $("input[name='vat']") : $("div[name$='vat']").children();
                    var $nameInput = $("input[name='name']").length ? $("input[name='name']") : $("h1 input.o_field_widget");

                    var rncValue = ui.item.rnc || ui.item.vat;

                    if ($input.attr('name') === 'vat' || $input.closest("div[name='vat']").length) {
                        $input.val(rncValue).trigger("change");
                        if ($nameInput.length) { $nameInput.val(ui.item.name).trigger("change"); }
                    } else {
                        $input.val(ui.item.name).trigger("change");
                        if ($rncInput.length) { $rncInput.val(rncValue).trigger("change"); }
                    }

                    return false;
                },
            });
        },
    });

    field_registry.add('dgii_autocomplete', FieldDgiiAutoComplete);

    return {
        FieldDgiiAutoComplete: FieldDgiiAutoComplete,
    };

});
