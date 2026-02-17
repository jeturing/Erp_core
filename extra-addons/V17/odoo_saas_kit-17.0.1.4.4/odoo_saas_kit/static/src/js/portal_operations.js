/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
// import rpc from "@web/legacy/js/core/rpc";
// import ajax from "@web/legacy/js/core/ajax";

publicWidget.registry.ContractPortalOperation = publicWidget.Widget.extend({
    selector: '.contract_portal_page, .container',
    events: {
        'click .get_subdomain_email': '_onClickGetSubdomainEmail',
        'click .instance_login': '_onClickInstanceLogin',
        'click .renew_contract': '_onClickRenewBtn',
    },

    init() {
        this._super(...arguments);
        // this.rpc = this.bindService("rpc");
        this.orm = this.bindService("orm");
    },

    _onClickGetSubdomainEmail:function() {
        var contract_id = $("#contract_id").attr('value');
        // rpc.query({ model: 'saas.contract', method: 'get_subdomain_email', args: [contract_id]})
        this.orm.call("saas.contract", "get_subdomain_email", [contract_id])
        .then(function(){
            console.log("--Email sent--")
        });
    },


    _onClickInstanceLogin: function(ev){
        ev.stopPropagation();
        var client_id = parseInt($('.instance_login').attr('client_id'));
        // rpc.query({model: 'saas.client',method: 'read',args: [[client_id], ['client_url']],})
        this.orm.read("saas.client",[client_id], ['client_url'])
        .then(function(url){
            // location.href = url[0]['client_url'];
            window.open(url[0]['client_url'], "_blank");
        });
    },

    _onClickRenewBtn: function(ev){
        var contract_id = parseInt($(ev.currentTarget).attr('contract_id'));
        // console.log(contract_id);
        // rpc.query({model: 'saas.client',method: 'read',args: [[client_id], ['client_url']],})
        this.orm.call("saas.contract", "generate_renew_invoice", [contract_id])
        .then(function(res){
            // console.log(res);
            if(res.status == true){
                window.location.reload();
            }
            else{
                $('.err_alert').show();
                $('.err_alert').html(res.message);
            }
        });
    },
    
});
