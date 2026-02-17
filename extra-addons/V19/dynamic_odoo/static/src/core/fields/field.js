/** @odoo-module **/

import {registry} from "@web/core/registry";
import {CharField, IntegerField} from "./char_field/char_field";
import {SelectionField} from "./selection_field/selection_field";
import {Many2oneField} from "./many2one_field/many2one_field";
import {Many2manyField, Many2manyGroups} from "./many2many_field/many2many_field";
import {ChooseColor} from "./color_widget/color_widget";
import {ChooseIcon} from "./choose_icon/choose_icon";
import {BatteryColorWidget} from "./battery_color_widget/color_widget";
import {CssWidget} from "./css_widget/css";
import {GraphType} from "./choose_graph_type/graph_type";
import {ToggleSwitch} from "./toggle_switch/toggle_switch";
import {Radio} from "./radio_field/radio_field";
import {MoreField} from "./more_field/more_field";
import {RecordColor} from "./record_color/record_color";
import {StudioDateTimeField} from "./datetime_field/datetime_field";
import {StudioHtmlField} from "./html_field/html_field";
import {FieldSelector} from "./field_selector/field_selector";
import {DomainSelector} from "./domain_selector/domain_selector";

const {Component, onWillUpdateProps} = owl;

const fieldRegistry = registry.category("dynamic_odoo.Field");

fieldRegistry.add("choose_color", ChooseColor);
fieldRegistry.add("battery_color", BatteryColorWidget);
fieldRegistry.add("css", CssWidget);
fieldRegistry.add("choose_icon", ChooseIcon);
fieldRegistry.add("char", CharField);
fieldRegistry.add("integer", IntegerField);
fieldRegistry.add("float", IntegerField);
fieldRegistry.add("monetary", IntegerField);
fieldRegistry.add("selection", SelectionField);
fieldRegistry.add("many2one", Many2oneField);
fieldRegistry.add("many2many", Many2manyField);
fieldRegistry.add("many2many_groups", Many2manyGroups);
fieldRegistry.add("graph_type", GraphType);
fieldRegistry.add("toggle_switch", ToggleSwitch);
fieldRegistry.add("more", MoreField);
fieldRegistry.add("radio", Radio);
fieldRegistry.add("record_color", RecordColor);
fieldRegistry.add("datetime", StudioDateTimeField);
fieldRegistry.add("field_selector", FieldSelector);
fieldRegistry.add("domain_selector", DomainSelector);
fieldRegistry.add("html", StudioHtmlField);


export class Field extends Component {
    setup() {
        super.setup();
        const {component, props, type} = this.props;
        this.FieldComponent = component ? component : fieldRegistry.get(type);
        this.fieldComponentProps = {...props};
        this.setFieldLabel();
        onWillUpdateProps(async (nextProps) => {
            if (nextProps.props) {
                this.fieldComponentProps = nextProps.props;
                this.setFieldLabel();
            }
        });
    }

    setFieldLabel() {
        if (this.FieldComponent && this.FieldComponent.noFieldLabel) {
            this.fieldComponentProps.label = this.props.label;
        }
    }
}

Field.template = "dynamic_odoo.Field";