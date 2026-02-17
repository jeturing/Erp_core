/** @odoo-module */

import { PosStore } from "@point_of_sale/app/store/pos_store";
import { Payment } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";
import { loadJS } from "@web/core/assets";

patch(PosStore.prototype, {
    async setup() {
        await super.setup(...arguments);
        // var self = this;
        await loadJS(`https://js.stripe.com/v3/`);

    },

    async _processData(loadedData) {
        await super._processData(...arguments);
        this.db.stripe_data = loadedData['stripe.config'] || [];
    }
});

patch(Payment.prototype, {
    
    setup() {
        super.setup(...arguments);
        this.is_stripe = this.is_stripe;
        this.transaction_entry = this.transaction_entry || false;
    },

    set_transaction_entry(res){
        this.transaction_entry = res
    },

    init_from_JSON(json){
        super.init_from_JSON(...arguments);
        this.is_stripe=json.is_stripe;
        this.transaction_entry=json.transaction_entry;
    },

    export_as_JSON(){
        const json = super.export_as_JSON(...arguments);
        json.is_stripe = this.is_stripe
        json.transaction_entry = this.transaction_entry
        return json        
    },

});


