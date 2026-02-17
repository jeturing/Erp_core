/** @odoo-module **/

const {Component, onWillStart} = owl;

export class BatteryColorWidget extends Component {
    setup() {
        super.setup();
        this.colors = this.prepareColors(this.props.node.attrs.colors || "");
        onWillStart(async () => {
            await this._lazyloadWysiwyg();
        });
    }

    prepareColors(colors) {
        const dataColors = {};
        if (colors) {
            colors.split(",").map((color) => {
                color = color.split(":");
                dataColors[color[0]] = color[1];
            });
        }
        return dataColors;
    }

    colorPaletteProps(key) {
        const self = this, {update} = this.props;
        return {
            onColorPicked: (colorInfo) => {
                self.colors[key] = colorInfo.color;
                if (update) {
                    update(Object.entries(self.colors).map((color) => color[0] + ":" + color[1]).join(","))
                }
            },
            withGradients: true,
        }
    }

    async _lazyloadWysiwyg() {
        const colorPalette = await odoo.loader.modules.get('@web_editor/js/wysiwyg/widgets/color_palette');
        this.ColorPalette = colorPalette.ColorPalette;
    }
}

BatteryColorWidget.template = "dynamic_odoo.BatteryColorWidget";

