/** @odoo-module */

import { AbstractAwaitablePopup } from "@point_of_sale/app/popup/abstract_awaitable_popup";
import { _t } from "@web/core/l10n/translation";
import { onMounted, useRef, useState } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useService } from "@web/core/utils/hooks";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { Orderline } from "@point_of_sale/app/generic_components/orderline/orderline";


export class StripePopup extends AbstractAwaitablePopup {
    static template = "bi_pos_stripe_payment.StripePopup";
    static defaultProps = {
        confirmText: 'Ok',
        cancelText: 'Cancel',
        title: 'Confirm ?',
    };
    
    setup() {
        super.setup();
        this.pos=usePos();
        this.popup = useService("popup");
        this.orm = useService("orm");
        onMounted(this.onMounted);
    }

    payWithCard(stripe, card, client_secret){
        $('.hide_footer').addClass('d-none');
        var self = this
        var country_code
        var partner = self.pos.get_order().get_partner()

        for (var i=0;i<self.pos.countries.length;i++){
            if(partner.country_id[1]==self.pos.countries[i].name){
                country_code = self.pos.countries[i].code
            }
        }
        
        var customer_name=$('#customer-name').val();
        var customer_mo_num = $('#customer-number').val()
        stripe.confirmCardPayment(client_secret, {
            payment_method: {
                card: card,
                billing_details: {
                    name: customer_name,
                    address: {
                        'line1': partner.street,
                        'postal_code': partner.zip,
                        'city': partner.city,
                        'state': partner.state_id[0],
                        'country': country_code,
                    },
              },

            }
        }).then(function(result) {
            if (result.error) {
                self.popup.add(ErrorPopup,{
                    title:'Payment Error!!',
                    body:result.error.message
                });
                
            } else {
                if(result.paymentIntent.status==='succeeded'){
                    let deleteLine = false
                    var paymentlines=self.pos.get_order().get_paymentlines();
                    paymentlines.forEach(function(line){
                        if(line.is_stripe){
                           deleteLine = line 
                        }
                    });
                    self.orm.call(
                        'pos.payment.transaction',
                        'update_satus',
                        [deleteLine.transaction_entry,customer_name,customer_mo_num]
                    )

                    $('.stripe-pending').text("PAYMENT DONE")
                    $('.refresh-button').addClass('d-none');
                    $('.delete-button').hide();
                    $('.next').addClass('highlight');

                    self.props.close({ confirmed: true, payload: null });

                }
                
            }
        });
    }

    onMounted() {
        var options = this.props
        var order = this.pos.get_order()
        var self = this
        $('.refresh-button').hide()
        var stripe = Stripe(self.pos.db.stripe_data[0].stripe_publishable_key)
        var element = stripe.elements();
        var card = element.create('card', {hidePostalCode: true});
            card.mount(".CardInputs");
            card.on('ready', function(event) {
                card.focus();
            });
        card.addEventListener('change', function (event) {
            var displayError = document.getElementById('card-error');
            if(event.error){
                displayError.textContent=event.error.message;
            }
            else{
                displayError.textContent=''
            }
        });
        this.stripe = stripe;
        this.stripe_card_element = card;

        var form=$('.stripeForm');
        form.on("submit", function(event) {
            event.preventDefault();
            $('.refresh-button').show()
            // Complete payment when the submit button is clicked
            self.payWithCard(stripe, card, options.data.client_secret);
        });
    }

    cancel(){
        super.cancel();
        var self = this
        
        var cancel_data = self.pos.get_order().stripe_payment_cancel
        self.props.PaymentScreenData.deletePaymentLine(cancel_data.cid)
    }
}