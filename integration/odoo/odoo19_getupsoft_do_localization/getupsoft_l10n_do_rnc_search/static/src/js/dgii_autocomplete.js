/** @odoo-module **/

import { CharField, charField } from "@web/views/fields/char/char_field";
import { registry } from "@web/core/registry";
import { useEffect, useRef } from "@odoo/owl";

export class DgiiAutoCompleteField extends CharField {
    setup() {
        super.setup();
        this.inputRef = useRef("input");
        
        useEffect((inputEl) => {
            if (!inputEl) return;
            if (window.$ && $.fn && $.fn.autocomplete) {
                $(inputEl).autocomplete({
                    source: "/dgii_ws/",
                    minLength: 3,
                    select: (event, ui) => {
                        const rncValue = ui.item.rnc || ui.item.vat;
                        const updates = {};
                        
                        // Determinar si actualizamos nombre o VAT o ambos
                        if (this.props.name === 'vat') {
                            updates.vat = rncValue;
                            updates.name = ui.item.name;
                        } else {
                            updates.name = ui.item.name;
                            updates.vat = rncValue;
                        }
                        
                        // Actualizar odoo state hook
                        if (this.props.record && this.props.record.update) {
                            this.props.record.update(updates);
                        } else {
                            // Fallback if not standard owl record
                            $(inputEl).val(ui.item.name).trigger('change');
                        }
                        
                        return false;
                    }
                });
            }
        }, () => [this.inputRef.el]);
    }
}
DgiiAutoCompleteField.template = "web.CharField";

registry.category("fields").add("dgii_autocomplete", {
    ...charField,
    component: DgiiAutoCompleteField,
});
