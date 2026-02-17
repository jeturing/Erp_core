/** @odoo-module **/

import {FormCompiler} from "@web/views/form/form_compiler";
import {FormRenderer} from "@web/views/form/form_renderer";
import {FormController} from "@web/views/form/form_controller";
import {ViewButton} from "@web/views/view_button/view_button";
import {evaluateExpr} from "@web/core/py_js/py";
import {patch} from "@web/core/utils/patch";
import {deserializeDateTime, formatDateTime} from "@web/core/l10n/dates";
import {usePopover} from "@web/core/popover/popover_hook";
import {ButtonBox} from "@web/views/form/button_box/button_box";

const {onWillStart, onWillUpdateProps, useState, onWillPatch, markup, onPatched, useSubEnv, Component} = owl;

ButtonBox.props.style = {type: String, optional: true};

export class ApprovalDetails extends Component {
    static props = ["*"]

    formatDateTime(value) {
        return formatDateTime(deserializeDateTime(value), {format: "DD"});
    }

    async onAction(state, approval) {
        const {model, id} = this.env.services.router.current.hash;
        await this.env.services.orm.call("studio.approval.details", "do_action", [approval.id, {state: state}], {});
        this.env.bus.trigger("MAIL:RELOAD-THREAD", {model: model, id: id});
    }
}

ApprovalDetails.template = "studio.ApprovalDetails";

export class Approval extends Component {
    static props = ["*"]

    setup() {
        this.popover = usePopover(ApprovalDetails, {popoverClass: "approval-popover"});
        this.state = useState({isOpened: false});
        onPatched(() => {
            if (this.state.isOpened) {
                this.popover.close();
                this.showDetails();
            }
        });
    }

    get approvals() {
        return this.props.approvals || [];
    }

    showDetails() {
        this.state.isOpened = true;
        this.popover.open(this.__owl__.bdom.firstNode(), {approvals: this.approvals});
    }
}

Approval.template = "studio.form_view.approval";

patch(ViewButton.prototype, {
    setup() {
        super.setup();
        const onClickViewButton = this.env.onClickViewButton;
        useSubEnv({
            onClickViewButton: (params) => {
                if (params.clickParams.confirm) {
                    params.clickParams.confirm = markup(params.clickParams.confirm)
                }
                onClickViewButton(params);
            },
        });
    },
    approvalRequest(approval) {
        const {model, id} = this.env.services.router.current.hash;
        this.env.services.orm.call("studio.approval.details", "request_approval", [approval.id], {}).then(() => {
            this.env.bus.trigger("MAIL:RELOAD-THREAD", {model: model, id: id});
        });
    },
    checkBeforeExecute() {
        const {approvals} = this.props;
        if (!(approvals || []).length) return true;
        const needRequest = approvals.filter((approval) => {
            if (approval.state == "wait") {
                this.approvalRequest(approval);
            }
            return ["wait", "decline"].includes(approval.state);
        });
        return !needRequest.length;
    },
    onClick(ev) {
        if (this.checkBeforeExecute()) {
            super.onClick(ev);
        }
    }
});

ViewButton.props = [...ViewButton.props, "btn_key?", "approvals?"];
ViewButton.components = {...ViewButton.components, Approval};


patch(FormCompiler.prototype, {
    compileButton(el, params) {
        const compiled = super.compileButton(el, params), context = el.getAttribute("context") || '{}';
        if (context.includes("btn_key")) {
            let btn_key = false;
            try {
                btn_key = evaluateExpr(context).btn_key;
            } catch {
                btn_key = eval(context.substring(1, context.length - 1).split(",").filter(
                    (x) => x.includes("btn_key")).map((x) => x.trim().split(":")[1])[0])
            }
            if (btn_key) {
                compiled.setAttribute("approvals", `__comp__.state.approvals['${btn_key}']`)
                compiled.setAttribute("btn_key", `'${btn_key}'`)
            }
        }
        const style = el.getAttribute("style");
        if (style) compiled.setAttribute("style", `'${style}'`);
        return compiled;
    }
});


patch(FormRenderer.prototype, {
    setup() {
        super.setup();
        this.env.services['bus_service'].subscribe("approval_data", (payload) => {
            this.state.approvals = payload.approvals;
        });
        onWillStart(async () => {
            await this.loadApproval();
        });
        onWillUpdateProps(async () => {
            await this.loadApproval();
        });
    },
    async loadApproval() {
        const {model, id} = this.env.services.router.current.hash, resId = this.props.record.data.id;
        this.state.approvals = await this.env.services.orm.call("studio.approval.details", "get_approval", [model, resId || id], {});
    }
});
