/** @odoo-module **/

const {Component, onWillStart, useState} = owl;

export class ChooseColor extends Component {
    setup() {
        super.setup();
        this.state = useState({value: this.props.value || "#5f5e5e"});
        onWillStart(async () => {
            await this._lazyloadWysiwyg();
        });
    }

    colorPaletteProps(key) {
        const self = this;
        return {
            onColorPicked: (colorInfo) => {
                self.onChooseColor(colorInfo.color);
            },
            withGradients: true,
        }
    }

    async _lazyloadWysiwyg() {
        const colorPalette = await odoo.loader.modules.get('@web_editor/js/wysiwyg/widgets/color_palette');
        this.ColorPalette = colorPalette.ColorPalette;
    }

    onChooseColor(color) {
        const {update} = this.props;
        this.state.value = color;
        if (update) {
            update(color);
        }
    }
}

ChooseColor.template = "dynamic_odoo.ChooseColorWidget";
ChooseColor.props = {
    update: {type: Function, optional: true},
    value: {type: String, optional: true},
    label: {type: String, optional: true}
}
ChooseColor.noFieldLabel = true;