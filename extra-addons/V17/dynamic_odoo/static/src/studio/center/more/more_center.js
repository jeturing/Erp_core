/** @odoo-module **/
import {useService} from "@web/core/utils/hooks";
import {ViewController} from "../view_controller";
import {LoginCenter} from "./login_desginer/login_center";


const {Component, useEffect, useState} = owl;

class ViewControllerExtend extends ViewController {
    get domain() {
        return `[['model_id.model', '=', '${this.props.resModel}']]`
    }

    get componentProps() {
        const props = super.componentProps;
        props.domain = [];
        props.irFilters = [
            {
                context: "{}",
                domain: this.domain,
                is_default: true,
                name: this.props.resModel,
            },
        ]
        return props;
    }
}

class Automation extends ViewControllerExtend {
}

Automation.actionXmlID = "base_automation.base_automation_act";

class AccessControl extends ViewControllerExtend {
}

AccessControl.actionXmlID = "base.ir_access_act";

class FilterRules extends ViewControllerExtend {
    get domain() {
        return `[['model_id', '=', '${this.props.resModel}']]`;
    }
}

FilterRules.actionXmlID = "base.actions_ir_filters_view";

class RecordRules extends ViewControllerExtend {
}

RecordRules.actionXmlID = "base.action_rule";


export default class MoreCenter extends Component {
    setup() {
        super.setup();
        this.onSetup();
        this.actionService = useService("action");
        this.state = useState({center: false});
        useEffect(() => {
            if (this.state.center) {
                $(document).find(".odoo_studio_mode").attr("sub_center", this.state.center);
            }
        });
    }

    get breadcrumbs() {
        const {center} = this.state
        if (center) {
            return [
                {title: "More", onClick: () => this.state.center = false},
                {
                    title: this.centerSupport[center].title, onClick: () => {
                    }
                }
            ];
        }
        return [];
    }

    onSetup() {
        this.centerSupport = {
            automation: {
                title: "Automation",
                icon: "fa fa-braille",
                color: "#E91E63",
                description: "You can create an automation to send email, update, write record ...",
                component: Automation
            },
            access_control: {
                title: "Access Control",
                icon: "fa fa-universal-access",
                color: "#FF9800",
                description: "You can create/update an access to model for anyone",
                component: AccessControl
            },
            filter_rules: {
                title: "Filter Rules",
                icon: "fa fa-filter",
                color: "#03A9F4",
                description: "You can create/update filter rules to any model",
                component: FilterRules
            },
            record_rules: {
                title: "Record Rules",
                icon: "fa fa-align-justify",
                color: "#FF5722",
                description: "You can create/update record rules for anyone",
                component: RecordRules
            },
            login_designer: {
                title: "Login View Designer",
                icon: "fa fa-user-circle",
                color: "#4CAF50",
                description: "You can change login view without knowledge",
                component: LoginCenter,
                assetsTemplate: "dynamic_odoo.LoginViewer.Assets",
            },
        }
    }
}

MoreCenter.template = "dynamic_odoo.MoreCenter";
