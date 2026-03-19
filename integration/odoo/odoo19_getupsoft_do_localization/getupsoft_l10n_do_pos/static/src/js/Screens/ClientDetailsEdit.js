odoo.define('getupsoft_l10n_do_pos.ClientDetailsEdit', function(require) {
    'use strict';

    const { onMounted, onWillUnmount } = owl.hooks;
    const ClientDetailsEdit = require('point_of_sale.ClientDetailsEdit');
    const Registries = require('point_of_sale.Registries');

    const ClientDetailsEditDoPos = ClientDetailsEdit =>
        class extends ClientDetailsEdit {

            constructor() {
                super(...arguments);
                // Agregamos el campo posicion fiscal al form
                this.intFields.push('property_account_position_id');
                const partner = this.props.partner;
                this.changes.property_account_position_id = partner.property_account_position_id && partner.property_account_position_id[0];
            }

            setup() {
                super.setup();

                var self = this;

                onMounted(() => {
                    // inicializa el auto completado cd nombre
                    $('[name="name"]').autocomplete({
                        source: "/dgii_ws/",
                        minLength: 3,
                        autoFocus: true,
                        select: function (_event, ui) {
                            // Modifa los campos, visualmente
                            $('[name="name"]').val(ui.item.name);
                            $('[name="vat"]').val(ui.item.rnc).trigger("change");
                            // Guarda el nuevo valor
                            self.changes['name'] = ui.item.name;
                            self.changes['vat'] = ui.item.rnc;

                            return false;
                        },
                    });

                });
                onWillUnmount(() => {
                    // remueve el componente de auto completado
                    $('[name="name"]').autocomplete('destroy');
                });

            }

        }
    Registries.Component.extend(ClientDetailsEdit, ClientDetailsEditDoPos);
    return ClientDetailsEditDoPos;

});
