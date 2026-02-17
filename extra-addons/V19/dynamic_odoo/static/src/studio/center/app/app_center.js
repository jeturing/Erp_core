/** @odoo-module **/
import {MediaDialog} from '@web_editor/components/media_dialog/media_dialog';
import {Field} from "@dynamic_odoo/core/fields/field";

const {Component, onWillStart, useState} = owl;

class ColorPicker extends Component {
    setup() {
        this.state = useState({value: this.props.value || "#ffffff"});
        onWillStart(async () => {
            await this._lazyloadWysiwyg();
        });
    }

    async _lazyloadWysiwyg() {
        const colorPalette = await odoo.loader.modules.get('@web_editor/js/wysiwyg/widgets/color_palette');
        this.ColorPalette = colorPalette.ColorPalette;
    }

    get colorPaletteProps() {
        return {
            onColorPicked: (colorInfo) => {
                this.state.value = colorInfo.color;
                this.props.update(colorInfo.color);
            },
            withGradients: true,
        }
    }
}

ColorPicker.template = "dynamic_odoo.widget.ColorPicker";

class IconCreator extends Component {
    setup() {
        this.state = useState({icon: "fa fa-home", image: false, bgColor: "#424869", color: "#ffffff"});
    }

    onShowIconDialog() {
        const media = document.createElement('i');
        this.env.services.dialog.add(MediaDialog, {
            noImages: true,
            noDocuments: true,
            noVideos: true,
            media,
            save: icon => {
                this.state.image = false;
                this.state.icon = icon.className;
            }
        });
    }

    onUploadIcon() {
        this.env.services.dialog.add(MediaDialog, {
            onlyImages: true,
            save: image => {
                this.state.icon = false;
                this.state.image = $(image).attr("src")
            }
        });
    }
}

IconCreator.template = "dynamic_odoo.AppCenter.Icons";
IconCreator.components = {ColorPicker};

export default class AppCenter extends Component {
    setup() {
        super.setup();
        this.onSetup();
        this.state = useState(this.prepareState());
    }

    get currentStep() {
        return this.steps[this.state?.step];
    }

    prepareState(step = "step0") {
        const views = this.steps[step].views;
        return {step: step, views: views ? views() : [], canNext: this.canNext(step)}
    }

    onSetup() {
        this.fields = {
            app_name: {label: "Choose an app name", type: "char"},
            menu_name: {label: "Choose menu name", type: "char"},
            is_new: {
                label: "New model", type: "toggle_switch", value: false, props: {
                    update: (value) => {
                        this.fields.is_new.value = value;
                        this.state.views = this.prepareState(this.state.step).views;
                    }
                }
            },
            model_name: {label: "Choose model", type: "many2one", props: {relation: "ir.model", value_name: "model"}},
            new_model: {
                label: "New model name", type: "char", props: {placeholder: "eg: x_..."}
            },
        }

        this.steps = {
            step0: {title: "Welcome to", next: "step1"},
            step1: {title: "Create your App", next: "step2", prev: "step0", editable: true, views: () => ["app_name"]},
            step2: {
                title: "Create your first Menu",
                next: this.onCreate.bind(this),
                prev: "step1",
                views: () => {
                    const view = ["is_new", "model_name", "menu_name"];
                    if (this.fields.is_new.value) {
                        view.splice(1, 1, "new_model");
                    }
                    return view;
                }
            },
        }
    }

    canNext(step = this.state.step) {
        const views = (this.steps[step].views || (() => ([])))();
        return !views.filter((fieldName) => !this.fields[fieldName].hasOwnProperty('value')).length;
    }

    flowStep(type = "next") {
        const step = this.currentStep[type];
        if (typeof step == "function") {
            return step();
        }
        Object.assign(this.state, this.prepareState(step));
    }

    getProps(field) {
        const fieldProps = {
            label: field.label,
            type: field.type,
            props: {
                update: (value) => {
                    this.fields[field.name].value = value;
                    this.state.canNext = this.canNext();
                }, ...field.props || {}
            }
        }
        if (field.hasOwnProperty("value")) {
            fieldProps.props.value = field.value;
        }
        return fieldProps;
    }

    get data() {
        const data = {};
        Object.keys(this.fields).map((fieldName) => {
            const field = this.fields[fieldName];
            if (field.value) {
                data[fieldName] = field.value;
            }
        });
        delete data[data.is_new ? 'model_name' : 'new_model'];
        return data;
    }

    async onCreate() {
        let iconData = await (domtoimage || {
            toPng: async () => {
            }
        }).toPng(document.getElementsByClassName("ic_preview")[0]);
        if (iconData) {
            iconData = iconData.split(",")[1];
        }
        const menu = await this.env.services.orm.call("ir.ui.menu", "create_new_app", [{
            ...this.data,
            app_icon: iconData
        }], {});
        await this.env.bus.trigger("START:RELOAD_MODELS");
        await this.env.services.menu.reload();
        await this.env.services.menu.selectMenu(menu.menu_id);
        this.props.onCreate();
    }
}


AppCenter.template = "dynamic_odoo.AppCenter";
AppCenter.components = {Field, IconCreator};