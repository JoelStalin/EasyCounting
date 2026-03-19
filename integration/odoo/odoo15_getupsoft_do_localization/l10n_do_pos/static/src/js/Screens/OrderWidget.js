odoo.define("l10n_do_pos.OrderWidget", function (require) {
    "use strict";

    const OrderWidget = require("point_of_sale.OrderWidget");
    const Registries = require("point_of_sale.Registries");

    const OrderWidgetDoPos = OrderWidget =>
        class extends OrderWidget {
            _onNewOrder(order) {
                // OVERWRITE
                if (order) {
                    this._applyDefaultPartner(order);
                    order.on("change", this._applyDefaultPartner, this);
                }
                super._onNewOrder(order);
            }

            _onPrevOrder(order) {
                // OVERWRITE
                if (order) {
                    order.off("change", null, this);
                }
                super._onPrevOrder(order);
            }

            /**
             * Agrega el cliente por defecto, definido en la configuracion
             * del pos y la posicion fiscal por defecto tiene activo el
             * 'to_invoice'
             *
             * @param: order
             */
            _applyDefaultPartner(order) {
                if (!order) {
                    order = this.env.pos.get_order();
                }

                let client = order.get_client();
                if (!client && order.fiscal_position && order.fiscal_position.l10n_do_to_invoice) {
                    const defaultCustomer = this.env.pos.get_default_customer();
                    if (defaultCustomer) {
                        order.set_client(defaultCustomer);
                    } else {
                        let message = "El cliente por defecto, no fue configurado en la configuracion del PTV.";
                        console.error(message);
                        this.showPopup('ErrorPopup', {
                            title: this.env._t('Error'),
                            body: message,
                        });
                    }
                }
            }
        }

    Registries.Component.extend(OrderWidget, OrderWidgetDoPos);
    return OrderWidgetDoPos;
});
