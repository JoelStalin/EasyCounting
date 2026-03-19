odoo.define('l10n_do_pos.ClientListScreen', function(require) {
    'strict';

    const { onMounted } = owl.hooks;
    const ClientListScreen = require("point_of_sale.ClientListScreen");
    const Registries = require("point_of_sale.Registries");

    const ClientListScreenDoPos = ClientListScreen =>
        class extends ClientListScreen {
            setup() {
                super.setup();
                var self = this;

                // Autoscoll para mostrar la linea del cliente seleccionado.
                onMounted(() => {
                    if (self.state.selectedClient) {
                        let el = document.querySelector(`[data-id='${self.state.selectedClient.id}']`);
                        if (el) {
                            el.scrollIntoView(true);
                        }
                    }
                });
            }

            clickNext() {
                // Evita cerrar la pantalla cuando el cliente sea el por defecto.
                if (this.nextButton.command === "deselect"
                    && this.state.selectedClient === this.env.pos.get_default_customer()) {
                    this.state.selectedClient = null;
                    this.render();
                } else {
                    super.clickNext();
                }
            }
        }

    Registries.Component.extend(ClientListScreen, ClientListScreenDoPos);
    return ClientListScreenDoPos;
});
