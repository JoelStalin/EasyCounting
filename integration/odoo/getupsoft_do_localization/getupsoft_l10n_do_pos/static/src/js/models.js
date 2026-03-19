odoo.define('getupsoft_l10n_do_pos.models', function (require) {
    "use strict";

    var models = require('point_of_sale.models');

    models.load_fields('res.company', ['street', 'street2']);
    models.load_fields('account.journal', [
        'l10n_latam_use_documents',
        'l10n_do_ncf_control_manager_ids',
        'l10n_do_payment_form',
    ]);

    models.load_models({
        model: 'l10n_latam.document.type',
        fields: [
            'name',
            'code',
            'l10n_do_use_in',
            'l10n_do_auto_sequence',
            'internal_type',
            'doc_code_prefix',
            'country_id',
        ],
        domain: function () {
            return [
                ['internal_type', 'in', ['invoice', 'credit_note']],
                ['active', '=', true],
                ['code', '=', 'B'],
                ['l10n_do_use_in', '!=', 'purchase'],
                ['l10n_do_auto_sequence', '=', false],
            ];
        },
        loaded: function (self, latam_document_types) {
            latam_document_types.forEach(function (latam_document_type) {
                if (latam_document_type.internal_type === 'credit_note') {
                    self.l10n_latam_document_type_credit_note = latam_document_type;
                }
            });
            self.l10n_latam_document_types = latam_document_types.filter(
                item => item.id !== self.l10n_latam_document_type_credit_note.id
            );
        },
    });

    const super_pos_model = models.PosModel.prototype;
    models.PosModel = models.PosModel.extend({
        initialize: function(attributes) {
            super_pos_model.initialize.call(this, attributes);

            this.l10n_latam_document_types = [];

            // Esto no carga al iniciar el POS sino que carga
            // segun el cliente actual. Esto se usa en PaymentScreen
            // por tanto es necesario para que el widget pueda
            // persivir el cambio.
            this.set({ 'l10n_do_nc_list': [] });

            function updateClient(pos, customer, _options) {
                if (!customer) {
                    pos.set_nc_list([], { silent: true });
                }

                if (pos && customer) {
                    pos.get_nc_lines().then((ncList) => {
                        pos.set_nc_list(ncList, { silent: true });
                    });

                    let order = pos.get_order();
                    const fiscal_position = _.find(pos.fiscal_positions, function(fp) {
                        return fp.id === customer.property_account_position_id[0];
                    });

                    // Si no es NC buscamos el 1er tipo de NCF que tenga la posion y la asignamos
                    // de lo contrario le colocalos el NCF tipo Nota Credito que viene por defecto.
                    if (fiscal_position && !order.l10n_do_is_return_order) {

                        // TODO: Si la position fiscal tiene 2 o mas tipo de NCF, debemos hacer que el cajero/a
                        // TODO: elija el NCF a usar al momento del pago.
                        order.l10n_latam_document_type_id = fiscal_position.l10n_do_ncf_ids[0];

                        if (order.l10n_latam_document_type_id) {
                            order.l10n_latam_document_type = _.find(pos.l10n_latam_document_types, function(ldt) {
                                return ldt.id === order.l10n_latam_document_type_id;
                            });
                        }

                        // La posicion fiscal determina si queremos factura por defecto.
                        order.to_invoice = fiscal_position.l10n_do_to_invoice;
                        order.trigger('change', order);
                    }
                }
            }

            this.on('change:selectedClient', updateClient, this);
        },

        set_nc_list: function(ncList, options){
            this.set({ l10n_do_nc_list: ncList }, options);
        },

        get_nc_list: function(){
            return this.get('l10n_do_nc_list');
        },

        // INFO: esto lo dejamos con fines de estudios futuros
        // push_and_invoice_order: function (order) {
        //     var self = this;
        //     var promise = super_pos_model.push_and_invoice_order.apply(self, [order]);
        //     return new Promise((resolve, reject) => {
        //         self.flush_mutex.exec(async () => {
        //             try {
        //                 const server_ids = await promise;
        //                 const [orderWithInvoice] = await self.rpc({
        //                     method: 'read',
        //                     model: 'pos.order',
        //                     args: [server_ids, [
        //                         'l10n_latam_document_number',
        //                         'l10n_do_ncf_expiration_date',
        //                         'l10n_do_origin_ncf',
        //                         'l10n_latam_document_type_id',
        //                         'l10n_do_is_return_order',
        //                     ]],
        //                     kwargs: { load: false },
        //                 });
        //
        //                 var order = self.get_order();
        //                 // order.l10n_do_is_return_order = orderWithInvoice.l10n_do_is_return_order;
        //                 // order.l10n_do_origin_ncf = orderWithInvoice.l10n_do_origin_ncf;
        //                 // order.l10n_latam_document_number = orderWithInvoice.l10n_latam_document_number;
        //                 // order.l10n_do_ncf_expiration_date = orderWithInvoice.l10n_do_ncf_expiration_date;
        //                 //
        //                 // order.l10n_latam_document_type = _.find(self.l10n_latam_document_types, function(ldt) {
        //                 //     return ldt.id === orderWithInvoice.l10n_latam_document_type_id;
        //                 // });
        //                 // order.l10n_latam_document_type_id = order.l10n_latam_document_type ? order.l10n_latam_document_type.id : false;
        //
        //                 // order.set_data_latam_document(
        //                 //     orderWithInvoice.l10n_do_ncf_expiration_date,
        //                 //     orderWithInvoice.l10n_do_origin_ncf,
        //                 // );
        //                 // order.set_latam_document_type(
        //                 //     orderWithInvoice.l10n_latam_document_type_id
        //                 // );
        //
        //                 order.trigger('change', order);
        //
        //                 resolve(server_ids);
        //             } catch (error) {
        //                 reject(error);
        //             }
        //         });
        //     });
        // },

        /**
        * Obtner las Notas de Credito del cliente actual en la orden.
        *
        * :return: List<Order>
        */
        get_nc_lines: async function () {
            const currentOrder = this.get_order();
            const client = this.get_client();

            if (client) {
                return await this.rpc({
                    method: 'get_nc_line_from_ui',
                    model: 'pos.order',
                    args: [[currentOrder], client.id],
                });
            }

            return [];
        },

        get_default_customer: function() {
            let client = null;

            if (this.config && this.config.l10n_do_default_partner_id) {
                client = this.db.get_partner_by_id(this.config.l10n_do_default_partner_id[0]);
            } else {
                console.error("El cliente por defecto, no fue configurado en la configuracion del PTV.");
            }

            return client;
        },


        push_and_invoice_order: function (order) {
            //Elimina que cuando se hace una factura, imprima el documento pdf de esa factura
            var self = this;
            return new Promise((resolve, reject) => {
                if (!order.get_client()) {
                    reject({ code: 400, message: 'Missing Customer', data: {} });
                } else {
                    var order_id = self.db.add_order(order.export_as_JSON());
                    self.flush_mutex.exec(async () => {
                        try {
                            const server_ids = await self._flush_orders([self.db.get_order(order_id)], {
                                timeout: 30000,
                                to_invoice: true,
                            });
                            if (server_ids.length) {
                                const [orderWithInvoice] = await self.rpc({
                                    method: 'read',
                                    model: 'pos.order',
                                    args: [server_ids, ['account_move']],
                                    kwargs: { load: false },
                                });
                                // await self
                                //     .do_action('account.account_invoices', {
                                //         additional_context: {
                                //             active_ids: [orderWithInvoice.account_move],
                                //         },
                                //     })
                                //     .catch(() => {
                                //         reject({ code: 401, message: 'Backend Invoice', data: { order: order } });
                                //     });
                            } else {
                                reject({ code: 401, message: 'Backend Invoice', data: { order: order } });
                            }
                            resolve(server_ids);
                        } catch (error) {
                            reject(error);
                        }
                    });
                }
            });
        },

    });

    const _super_orderline_model = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
        export_as_JSON: function() {
            var json = _super_orderline_model.export_as_JSON.apply(this, arguments);
            json.my_product_name = this.full_product_name || '';
            return json;
        },
        export_for_printing: function() {
            var json = _super_orderline_model.export_for_printing.apply(this, arguments);
            let product_name = this.generate_wrapped_product_name()[0];
            if (this.product.default_code) {
                product_name = `[${this.product.default_code}] ${product_name}`;
            }
            json.my_product_name = product_name;
            return json;
        },
    });



    const super_order_model = models.Order.prototype;
    models.Order = models.Order.extend({
        initialize: function () {
            super_order_model.initialize.apply(this, arguments);

            this.l10n_latam_document_number = this.l10n_latam_document_number || "";
            this.l10n_do_ncf_expiration_date = this.l10n_do_ncf_expiration_date || "";
            this.l10n_do_origin_ncf = this.l10n_do_origin_ncf || "";

            this.l10n_do_is_return_order = this.l10n_do_is_return_order || false;

            
            debugger;

            if (!this.get_client() || this.get_client() == null) {
                this.set_client(this.pos.get_default_customer());
            }


            const [l10n_latam_document_type_id,l10n_latam_document_type ] =  this.get_default_document_type();

            
            this.l10n_latam_document_type = l10n_latam_document_type || false;
            this.l10n_latam_document_type_id =  l10n_latam_document_type_id|| false;

            this.save_to_db();

            return this;
        },

        init_from_JSON: function(json) {
            super_order_model.init_from_JSON.call(this, json);

            this.to_invoice = json.to_invoice;
            this.l10n_latam_document_number = json.l10n_latam_document_number || false;
            this.l10n_do_ncf_expiration_date = json.l10n_do_ncf_expiration_date || false;
            this.l10n_do_origin_ncf = json.l10n_do_origin_ncf || false;
            this.l10n_latam_document_type = _.find(this.pos.l10n_latam_document_types, function(ldt) {
                return ldt.id === json.l10n_latam_document_type_id;
            });
            this.l10n_latam_document_type_id = this.l10n_latam_document_type ? this.l10n_latam_document_type.id : false;
            this.l10n_do_is_return_order = json.l10n_do_is_return_order || false;

            if (!json.partner_id || json.partner_id == null) {
                this.set_client(this.pos.get_default_customer());
            }
        },

        export_as_JSON: function () {
            var json = super_order_model.export_as_JSON.call(this);

            var to_return = _.extend(json, {
                l10n_latam_document_number: this.l10n_latam_document_number || false,
                l10n_do_ncf_expiration_date: this.l10n_do_ncf_expiration_date || false,
                l10n_do_origin_ncf: this.l10n_do_origin_ncf || false,
                l10n_latam_document_type_id: this.l10n_latam_document_type_id || false,
                l10n_do_is_return_order: this.l10n_do_is_return_order || false,
            });
            return to_return;
        },

        export_for_printing: function() {
            var json = super_order_model.export_for_printing.apply(this, arguments);

            var to_return = _.extend(json, {
                l10n_latam_document_number: this.l10n_latam_document_number,
                l10n_do_ncf_expiration_date: this.l10n_do_ncf_expiration_date,
                l10n_do_origin_ncf: this.l10n_do_origin_ncf,
                l10n_latam_document_type_id: this.l10n_latam_document_type_id,
                l10n_do_is_return_order: this.l10n_do_is_return_order,
            });
            return to_return;
        },


        get_default_document_type: function(){
            

            let customer = this.get_client() ;

            if (!customer) {
                //Si no hay cliente, retonar por defecto el tipo :Consumidor Final
                let dtype = _.find(this.pos.l10n_latam_document_types, function(ldt) {
                    return ldt.doc_code_prefix === "B02";
                });
            
                let dtype_id = dtype.id

                return [dtype_id,dtype]
            }

            const fiscal_position = _.find(this.pos.fiscal_positions, function(fp) {
                return fp.id === customer.property_account_position_id[0];
            });
            
            let l10n_latam_document_type_id = fiscal_position.l10n_do_ncf_ids[0];

            if (l10n_latam_document_type_id) {
                var l10n_latam_document_type = _.find(this.pos.l10n_latam_document_types, function(ldt) {
                    return ldt.id === l10n_latam_document_type_id;
                });
            }

            return [l10n_latam_document_type_id,l10n_latam_document_type]
        },

        set_data_latam_document: function(document_number, ncf_expiration_date, ncf_origin) {
            this.l10n_latam_document_number = document_number || false;
            this.l10n_do_ncf_expiration_date = ncf_expiration_date || false;
            this.l10n_do_origin_ncf = ncf_origin || false;

            this.trigger('change', this);
            this.save_to_db();
        },

        set_latam_document_type: function(document_type_id) {
            this.l10n_latam_document_type = _.find(this.pos.l10n_latam_document_types, function(ldt) {
                return ldt.id === document_type_id;
            });
            this.l10n_latam_document_type_id = this.l10n_latam_document_type ? this.l10n_latam_document_type.id : false;

            this.trigger('change', this);
            this.save_to_db();
        },

        set_ncf_data(data) {
            if (data) {
                this.l10n_do_is_return_order = data.l10n_do_is_return_order;
                this.l10n_do_origin_ncf = data.l10n_do_origin_ncf;
                this.l10n_latam_document_number = data.l10n_latam_document_number;
                this.l10n_do_ncf_expiration_date = data.l10n_do_ncf_expiration_date;

                this.l10n_latam_document_type = _.find(this.pos.l10n_latam_document_types, function(ldt) {
                    return ldt.id === data.l10n_latam_document_type_id;
                });
                this.l10n_latam_document_type_id = this.l10n_latam_document_type ? this.l10n_latam_document_type.id : false;

                if (data.l10n_do_is_return_order) {
                    this.l10n_latam_document_type = this.pos.l10n_latam_document_type_credit_note;
                    this.l10n_latam_document_type_id = this.pos.l10n_latam_document_type_credit_note.id;
                }

                // this.trigger('change', this);
                // this.save_to_db();
            }
        },

        set_nc_data(l10n_do_origin_ncf) {
            this.l10n_do_origin_ncf = l10n_do_origin_ncf;
            this.l10n_do_is_return_order = true;
            this.l10n_latam_document_type = this.pos.l10n_latam_document_type_credit_note;
            this.l10n_latam_document_type_id = this.pos.l10n_latam_document_type_credit_note.id;

            this.trigger('change', this);
            this.save_to_db();
        },

        wait_for_push_order: function () {
            return true;
        }
    });

    var super_paymentline = models.Paymentline.prototype;
    models.Paymentline = models.Paymentline.extend({
        initialize: function (attr, options) {
            this.credit_note_id = null;
            this.note = '';
            super_paymentline.initialize.call(this, attr, options);
        },
        init_from_JSON: function (json) {
            super_paymentline.init_from_JSON.call(this, json);
            this.credit_note_id = json.credit_note_id;
            this.note = json.note;
        },
        export_as_JSON: function () {
            var json = super_paymentline.export_as_JSON.call(this);

            var to_return = _.extend(json, {
                credit_note_id: this.credit_note_id,
                note: this.note,
                payment_reference: this.payment_method.payment_reference,
            });
            return to_return;
        },
        set_nc_data: function(data){
            this.order.assert_editable();
            this.note = data.note;
            this.credit_note_id = data.credit_note_id;
            this.trigger('change',this);
        },
    });

    return models;

});
