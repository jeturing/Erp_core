/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { WebClient } from "@web/webclient/webclient";
import { ErrorDialog, ClientErrorDialog, NetworkErrorDialog, RPCErrorDialog, WarningDialog } from "@web/core/errors/error_dialogs";

// =====================================================
// 1. WebClient title: "Sajet" instead of "Odoo"
// =====================================================
patch(WebClient.prototype, {
    setup() {
        super.setup(...arguments);
        // Override the title fallback from "Odoo" to "Sajet"
        this.title.setParts({ zopenerp: "Sajet" });
    },
});

// =====================================================
// 2. ErrorDialog: "Sajet Error" instead of "Odoo Error"
// =====================================================
patch(ErrorDialog, {
    title: "Sajet Error",
});

// =====================================================
// 3. ClientErrorDialog: "Sajet Client Error"
// =====================================================
patch(ClientErrorDialog, {
    title: "Sajet Client Error",
});

// =====================================================
// 4. NetworkErrorDialog: "Sajet Network Error"
// =====================================================
patch(NetworkErrorDialog, {
    title: "Sajet Network Error",
});

// =====================================================
// 5. RPCErrorDialog: Replace "Odoo" in inferred titles
// =====================================================
patch(RPCErrorDialog.prototype, {
    setup() {
        super.setup(...arguments);
        // Replace "Odoo" in the title if it was set by inferTitle()
        if (this.props.title && typeof this.props.title === "string") {
            this.props.title = this.props.title.replace(/Odoo/g, "Sajet");
        }
    },
});

// =====================================================
// 6. WarningDialog: "Sajet Warning" instead of "Odoo Warning"
// =====================================================
patch(WarningDialog.prototype, {
    get title() {
        const original = super.title;
        if (typeof original === "string") {
            return original.replace(/Odoo/g, "Sajet");
        }
        return "Sajet Warning";
    },
});
