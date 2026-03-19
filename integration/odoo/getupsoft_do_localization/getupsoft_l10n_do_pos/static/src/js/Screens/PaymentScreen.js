odoo.define('getupsoft_l10n_do_pos.PaymentScreen', function (require) {
    'use strict';

    /**
     * TODO: Si la posicion fiscal del cliente tiene 2 o mas tipos
     * TODO: de NCF, debemos hacer que el usuario elija cual usara, para
     * TODO: la facturacion.
     */

    const NumberBuffer = require('point_of_sale.NumberBuffer');
    const PaymentScreen = require('point_of_sale.PaymentScreen');
    const Registries = require('point_of_sale.Registries');
    const session = require('web.session');

    const PaymentScreenDoPos = PaymentScreen =>
        class extends PaymentScreen {

            constructor() {
                super(...arguments);

                // INFO: hack, se queda comentado con fines de estudios futuros
                // this.payment_methods_from_config = this.env.pos.payment_methods.filter(method =>
                //   method.id === 10001 || this.env.pos.config.payment_method_ids.includes(method.id)
                // );
            }

            get ncList() {
                return this.env.pos.get_nc_list();
            }

            addNewPaymentLine(owlEvent) {
                const { detail: paymentMethod } = owlEvent;

                if (paymentMethod.type === 'nc_type') {
                    if (this.ncList.length && this.ncList.length > 0) {
                        let self = this;

                        this.showPopup(
                            'SelectionPopup',
                            {
                                title: "Elija la Nota de Credito",
                                list: this.ncList,
                            }
                        ).then(({ confirmed, payload }) => {
                            if (confirmed) {
                                const { id, name, residual } = payload;

                                self.currentOrder.add_paymentline(paymentMethod);
                                self.currentOrder.selected_paymentline.set_nc_data({'credit_note_id': id, 'note': name});
                                // Add paymentline for residual
                                self.currentOrder.selected_paymentline.set_amount(residual);

                                self.render();

                                NumberBuffer.reset();
                                return true;
                            }
                        });

                    } else {
                        this.showPopup('ErrorPopup', {
                            title: this.env._t('Error'),
                            body: "El cliente no tiene Nota de creditos para aplicar",
                        });
                    }
                } else {
                    super.addNewPaymentLine(owlEvent);
                }
            }

            // INFO: se queda comentado, con final de estudios futuros.
            // addNewPaymentLine(owlEvent) {
            //     let self = this;
            //     const { detail: paymentMethod } = owlEvent;
            //     if (paymentMethod.id === 10001) {
            //         const client = this.currentOrder.get_client();
            //         if (!client) {
            //             this.showPopup('ErrorPopup', {
            //                 title: this.env._t('Error'),
            //                 body: this.env._t('Primero debe asignar un cliente a la orden.'),
            //             });
            //             return false;
            //         }
            //
            //         this.showPopup(
            //             'TextInputPopup',
            //             {
            //                 title: this.env._t('Digite el No. de la Nota de Credito'),
            //             }
            //         ).then(({confirmed, payload: nc_number}) => {
            //             // Revisar el la DB si existe la Nota de credito.
            //
            //             if (confirmed) {
            //                 var msg_error = "";
            //
            //                 self.rpc({
            //                         model: 'pos.order',
            //                         method: 'credit_note_info_from_ui',
            //                         args: [[self.currentOrder], nc_number],
            //                         kwargs: {context: self.env.session.user_context},
            //                     },
            //                     {},
            //                 )
            //                 .then(function (result) {
            //                     var residual = parseFloat(result.residual) || 0;
            //                     var client = self.env.pos.get_client();
            //                     if (!client) {
            //                         // TODO: default partner
            //                         client = {
            //                             id: self.pos.config.l10n_do_default_partner_id[0]
            //                         }
            //                     }
            //
            //                     if (result.id === false) {
            //                         msg_error = _t("La nota de credito no existe.");
            //                     } else if (!client  || (client && client.id !== result.partner_id)){
            //                         msg_error = _t("La Nota de Crédito Pertenece a Otro Cliente");
            //                     } else if (residual < 1) {
            //                         msg_error = _t("El balance de la Nota de Credito es 0.");
            //                     } else {
            //                         var order = self.env.pos.get_order();
            //                         var payment_method = self.env.pos.payment_methods_by_id[10001];
            //                         var paymentline = order.paymentlines.find(function (pl) {
            //                             return pl.note === nc_number;
            //                         });
            //
            //                         if (paymentline) {
            //                             msg_error = "Esta Nota de Credito ya esta aplicada a la Orden";
            //                         } else {
            //                             order.add_paymentline(payment_method);
            //                             order.selected_paymentline.credit_note_id = result.id;
            //                             order.selected_paymentline.note = nc_number;
            //                             order.selected_paymentline.set_amount(residual); // Add paymentline for residual
            //
            //                             self.render();
            //                             return false;
            //                         }
            //                     }
            //
            //                     self.showPopup('ErrorPopup', {
            //                         title: self.env._t('Search') + " Nota de Credito",
            //                         body: msg_error,
            //                     });
            //
            //                 })
            //                 .catch(function (error) {
            //                     console.log('>>> Error: Check NC <<<');
            //                     throw error;
            //                 });
            //             }
            //         });
            //     }
            //
            //     super.addNewPaymentLine(owlEvent);
            // }

            async validateOrder(isForceValidate) {
                // Auto asignar 'to_invoice', segun lo requiera la posicion fiscal
                // asignada en la orden. Esta posicion puede ser la propia del cliente
                // o una asignada directamente.

                // TODO: Si el usuario elige un cliente fiscal pero asigna a la orden
                // TODO: la posicion fiscal 'special' entonces la orden final saldra sin valor
                // TODO: fiscal.

                const client = this.currentOrder.get_client();

                // Asegura de que si la orden lo require, este to_invoice activo
                if (this.currentOrder.fiscal_position
                    && this.currentOrder.fiscal_position.l10n_do_to_invoice === true
                    && this.currentOrder.is_to_invoice() === false) {
                    this.currentOrder.set_to_invoice(true);
                }

                // TODO: si la posicion por defecto require invoice, entonces debemos
                // TODO: color por el cliente por defecto, esto debe venir configurado en pos.
                if (this.currentOrder.to_invoice && !client) {
                    this.showPopup('ErrorPopup', {
                        title: this.env._t('Error'),
                        body: 'El cliente es necesario para procesar este orden'
                    });
                    return;
                }

                // Si la factura requiere factura y el cliente no tiene posicion fiscal
                // entonces sal e indica al usuario.
                if (this.currentOrder.to_invoice && !client.property_account_position_id) {
                    this.showPopup('ErrorPopup', {
                        title: this.env._t('Error'),
                        body: this.env._t(`El cliente debe tener una posicion fiscal asignada. \n
                            Debe agregar manualmente la posicion fiscal al cliente.`),
                    });
                    return;
                }

                // Evita que se valide una orden cuya posicion fiscal es diferente a la del cliente.
                if (this.currentOrder.fiscal_position
                    && this.currentOrder.fiscal_position.id !== client.property_account_position_id[0]) {
                    this.showPopup('ErrorPopup', {
                        title: this.env._t('Error'),
                        body: this.env._t(`La posicion fiscal del cliente no es igual a la posicion fiscal asignada a la orden.\n
                            Debe asignar manualmente la misma posicion fiscal del cliente a la orden.`),
                    });
                    return;
                }

                return super.validateOrder(isForceValidate);
            }

            async _postPushOrderResolve(order, order_server_ids) {
                // Este metodo carga los datos NCF de la factura recien creada.
                // try {
                    debugger;
                    const [orderWithInvoice] = await this.rpc({
                        method: 'read',
                        model: 'pos.order',
                        domain: [['id', 'in', order_server_ids]],
                        args: [order_server_ids, [
                            'l10n_latam_document_number',
                            'l10n_do_ncf_expiration_date',
                            'l10n_do_origin_ncf',
                            'l10n_latam_document_type_id',
                            'l10n_do_is_return_order',
                        ]],
                        kwargs: { load: false },
                        context: session.user_context,
                    },{
                        timeout: 10000,
                        // shadow: true,
                    });

                    debugger;

                    order.set_ncf_data(orderWithInvoice || null);
                // } finally {
                    return super._postPushOrderResolve(...arguments);
                // }
            }
        }

    Registries.Component.extend(PaymentScreen, PaymentScreenDoPos);
    return PaymentScreenDoPos;

});


