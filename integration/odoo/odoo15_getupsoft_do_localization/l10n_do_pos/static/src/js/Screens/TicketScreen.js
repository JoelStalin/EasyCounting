odoo.define('l10n_do_pos.TicketScreen', function(require) {
    'use strict';

    // const { useState } = owl.hooks;
    const TicketScreen = require('point_of_sale.TicketScreen');
    const Registries = require('point_of_sale.Registries');
    const PaymentScreen = require('point_of_sale.PaymentScreen');

    const TicketScreenDoPos = TicketScreen =>
        class extends TicketScreen {
            constructor() {
                super(...arguments);
                // Limpia la busqueda si el cliente es el por defecto
                const customer = this.env.pos.get_order().get_client();
                if (customer.id === this.env.pos.get_default_customer().id) {
                    this._state.ui.searchDetails.searchTerm = "";
                }
            }

            async _onDoRefund() {
                const order = this.getSelectedSyncedOrder();
                const customer = order.get_client();

                await super._onDoRefund(arguments);

                if (!order && !order.l10n_latam_document_number) {
                    return this.render();
                }

                const refunds = Object.values(this.env.pos.toRefundLines)
                    .filter(function ({ orderline }) {
                        return customer ?
                            orderline.orderPartnerId === customer.id
                            && orderline.orderUid === order.uid
                            : true;
                    });

                if (refunds.length === 0) {
                    return this.render();
                }
                const refundOrder = this.env.pos.get('orders').models .find(
                    (_order) => _order.uid === refunds[0].destinationOrderUid);

                if (refundOrder !== this.env.pos.get_order()) {
                    this.env.pos.set_order(refundOrder);
                }

                refundOrder.set_client(order.get_client());
                refundOrder.updatePricelist(order.get_client());
                refundOrder.set_nc_data(order.l10n_latam_document_number);

                const pay = new PaymentScreen();
                await pay.validateOrder(false);
                await this.showScreen("ReceiptScreen");
                this.env.pos.delete_current_order();
            }

        }

    Registries.Component.extend(TicketScreen, TicketScreenDoPos);
    return TicketScreenDoPos;

});
