/** @odoo-module */

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
import { _t } from '@web/core/l10n/translation';
import { useService } from "@web/core/utils/hooks";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { jsonrpc } from "@web/core/network/rpc_service";
import { StripePopup } from "@bi_pos_stripe_payment/js/StripePopup";

patch(PaymentScreen.prototype, {

    async setup() {
        super.setup();
        this.popup = useService("popup");
        this.orm = useService("orm");

        // Cargar configuración activa de Stripe
        await this.loadStripeConfig();

        // Limpiar líneas de pago previas de Stripe si existen
        var paymentlines = this.pos.get_order().get_paymentlines();
        if (paymentlines.length > 0) {
            for (var i = 0; i < paymentlines.length; i++) {
                if (paymentlines[i].is_stripe) {
                    this.deletePaymentLine(paymentlines[i].cid);
                }
            }
        }
    },

    /**
     * Carga la configuración activa de Stripe desde el modelo `stripe.config` en Odoo.
     */
    async loadStripeConfig() {
        try {
            const stripeConfig = await this.orm.call(
                'stripe.config', 
                'search_read', 
                [[['activet', '=', true]], ['stripe_publishable_key', 'stripe_secret_key']]
            );
            if (stripeConfig && stripeConfig.length > 0) {
                this.stripe_publishable_key = stripeConfig[0].stripe_publishable_key;
            } else {
                throw new Error("No active Stripe configuration found.");
            }
        } catch (error) {
            console.error("Error loading Stripe configuration:", error);
            this.popup.add(ErrorPopup, {
                'title': _t('Configuration Error'),
                'body': _t('Unable to load active Stripe configuration. Please configure Stripe in Odoo.'),
            });
        }
    },

    /**
     * Solicita la selección de propina y ajusta el total de la transacción.
     */
    async requestTipAmount(amount) {
        // Opciones de porcentaje de propina
        const tipPercentages = [0, 5, 10, 15, 20, 30];
        
        // Crear opciones de propina para el popup
        const tipOptions = tipPercentages.map(percent => {
            return {
                label: `${percent}%`,
                callback: () => (amount * (1 + percent / 100)),  // Calcula el total con propina
            };
        });

        // Mostrar popup para selección de propina
        const { confirmed, payload } = await this.popup.showPopup('SelectionPopup', {
            title: _t('Select Tip Percentage'),
            list: tipOptions,
        });

        // Retorna el total ajustado con propina si se confirma
        if (confirmed) {
            return payload || amount;  // Usa el valor de la propina o el monto original
        }
        return amount; // Retorna el monto original si se cancela
    },

    /**
     * Añade una nueva línea de pago de Stripe si es válida y se selecciona un cliente.
     */
    async addNewPaymentLine(paymentMethod) {
        const order = this.pos.get_order();
        var payment_method = null;
        
        // Verifica si el método de pago seleccionado permite Stripe
        for (var i = 0; i < this.pos.payment_methods.length; i++) {
            if (this.pos.payment_methods[i].id === paymentMethod.id) {
                payment_method = this.pos.payment_methods[i];
                break;
            }
        }

        if (payment_method.allow_payment_to_stripe) {
            var currentOrder = this.pos.get_order();

            // Verifica si hay un cliente seleccionado
            if (!currentOrder.get_partner()) {
                this.popup.add(ErrorPopup, {
                    'title': _t('Unknown customer'),
                    'body': _t('You cannot use Stripe payment. Select customer first.'),
                });
                return false;
            }

            // Monto pendiente de la orden
            var due = order.get_due();
            if (this.stripe_publishable_key) {
                var selected_paymentline = null;

                // Solicita la propina y ajusta el total
                due = await this.requestTipAmount(due);

                // Solo permite pagos con montos válidos
                if (due > 0) {
                    const res = super.addNewPaymentLine(...arguments);
                    if (order.selected_paymentline) {
                        selected_paymentline = order.selected_paymentline;
                    }

                    if (selected_paymentline) {
                        selected_paymentline.is_stripe = true;
                        var stripe = Stripe(this.stripe_publishable_key);

                        // Crea una intención de pago en el servidor
                        var paymentIntent = jsonrpc("/create-payment-intent", {
                            stripe_data: { stripe_publishable_key: this.stripe_publishable_key },
                            amount: due,
                            currency: this.pos.company.currency_id[1],
                        }).then(function (data) {
                            if (data) {
                                $('.next').removeClass('highlight');
                                this.pos.get_order().stripe_payment_data = data;
                                this.pos.get_order().stripe_payment_cancel = selected_paymentline;

                                this.stripe_payment_transaction(data, order.name, selected_paymentline, due, 'draft');
                                this.popup.add(StripePopup, {
                                    'title': 'Stripe Payment',
                                    'data': data,
                                    'PaymentScreenData': this,
                                });
                            }
                        }.bind(this));
                        this.render();
                    }
                }
            } else {
                this.popup.add(ErrorPopup, {
                    'title': _t('Configuration Error'),
                    'body': _t('Configure Stripe Data for the Stripe Payment in Odoo.'),
                });
            }
        } else {
            const res = super.addNewPaymentLine(...arguments);
        }
    },
});
