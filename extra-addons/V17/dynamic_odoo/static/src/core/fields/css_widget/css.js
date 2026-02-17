/** @odoo-module **/

import {MediaDialog} from '@web_editor/components/media_dialog/media_dialog';

const {
    Component,
    onMounted,
    onWillUpdateProps,
    useEffect,
    onWillUnmount,
    onPatched,
    onWillStart,
    useState,
    useRef,
} = owl;

const COLORS = {
    ALICEBLUE: 0xf0f8ffff,
    ANTIQUEWHITE: 0xfaebd7ff,
    AQUA: 0x00ffffff,
    AQUAMARINE: 0x7fffd4ff,
    AZURE: 0xf0ffffff,
    BEIGE: 0xf5f5dcff,
    BISQUE: 0xffe4c4ff,
    BLACK: 0x000000ff,
    BLANCHEDALMOND: 0xffebcdff,
    BLUE: 0x0000ffff,
    BLUEVIOLET: 0x8a2be2ff,
    BROWN: 0xa52a2aff,
    BURLYWOOD: 0xdeb887ff,
    CADETBLUE: 0x5f9ea0ff,
    CHARTREUSE: 0x7fff00ff,
    CHOCOLATE: 0xd2691eff,
    CORAL: 0xff7f50ff,
    CORNFLOWERBLUE: 0x6495edff,
    CORNSILK: 0xfff8dcff,
    CRIMSON: 0xdc143cff,
    CYAN: 0x00ffffff,
    DARKBLUE: 0x00008bff,
    DARKCYAN: 0x008b8bff,
    DARKGOLDENROD: 0xb886bbff,
    DARKGRAY: 0xa9a9a9ff,
    DARKGREEN: 0x006400ff,
    DARKGREY: 0xa9a9a9ff,
    DARKKHAKI: 0xbdb76bff,
    DARKMAGENTA: 0x8b008bff,
    DARKOLIVEGREEN: 0x556b2fff,
    DARKORANGE: 0xff8c00ff,
    DARKORCHID: 0x9932ccff,
    DARKRED: 0x8b0000ff,
    DARKSALMON: 0xe9967aff,
    DARKSEAGREEN: 0x8fbc8fff,
    DARKSLATEBLUE: 0x483d8bff,
    DARKSLATEGRAY: 0x2f4f4fff,
    DARKSLATEGREY: 0x2f4f4fff,
    DARKTURQUOISE: 0x00ced1ff,
    DARKVIOLET: 0x9400d3ff,
    DEEPPINK: 0xff1493ff,
    DEEPSKYBLUE: 0x00bfffff,
    DIMGRAY: 0x696969ff,
    DIMGREY: 0x696969ff,
    DODGERBLUE: 0x1e90ffff,
    FIREBRICK: 0xb22222ff,
    FLORALWHITE: 0xfffaf0ff,
    FORESTGREEN: 0x228b22ff,
    FUCHSIA: 0xff00ffff,
    GAINSBORO: 0xdcdcdcff,
    GHOSTWHITE: 0xf8f8ffff,
    GOLD: 0xffd700ff,
    GOLDENROD: 0xdaa520ff,
    GRAY: 0x808080ff,
    GREEN: 0x008000ff,
    GREENYELLOW: 0xadff2fff,
    GREY: 0x808080ff,
    HONEYDEW: 0xf0fff0ff,
    HOTPINK: 0xff69b4ff,
    INDIANRED: 0xcd5c5cff,
    INDIGO: 0x4b0082ff,
    IVORY: 0xfffff0ff,
    KHAKI: 0xf0e68cff,
    LAVENDER: 0xe6e6faff,
    LAVENDERBLUSH: 0xfff0f5ff,
    LAWNGREEN: 0x7cfc00ff,
    LEMONCHIFFON: 0xfffacdff,
    LIGHTBLUE: 0xadd8e6ff,
    LIGHTCORAL: 0xf08080ff,
    LIGHTCYAN: 0xe0ffffff,
    LIGHTGOLDENRODYELLOW: 0xfafad2ff,
    LIGHTGRAY: 0xd3d3d3ff,
    LIGHTGREEN: 0x90ee90ff,
    LIGHTGREY: 0xd3d3d3ff,
    LIGHTPINK: 0xffb6c1ff,
    LIGHTSALMON: 0xffa07aff,
    LIGHTSEAGREEN: 0x20b2aaff,
    LIGHTSKYBLUE: 0x87cefaff,
    LIGHTSLATEGRAY: 0x778899ff,
    LIGHTSLATEGREY: 0x778899ff,
    LIGHTSTEELBLUE: 0xb0c4deff,
    LIGHTYELLOW: 0xffffe0ff,
    LIME: 0x00ff00ff,
    LIMEGREEN: 0x32cd32ff,
    LINEN: 0xfaf0e6ff,
    MAGENTA: 0xff00ffff,
    MAROON: 0x800000ff,
    MEDIUMAQUAMARINE: 0x66cdaaff,
    MEDIUMBLUE: 0x0000cdff,
    MEDIUMORCHID: 0xba55d3ff,
    MEDIUMPURPLE: 0x9370dbff,
    MEDIUMSEAGREEN: 0x3cb371ff,
    MEDIUMSLATEBLUE: 0x7b68eeff,
    MEDIUMSPRINGGREEN: 0x00fa9aff,
    MEDIUMTURQUOISE: 0x48d1ccff,
    MEDIUMVIOLETRED: 0xc71585ff,
    MIDNIGHTBLUE: 0x191970ff,
    MINTCREAM: 0xf5fffaff,
    MISTYROSE: 0xffe4e1ff,
    MOCCASIN: 0xffe4b5ff,
    NAVAJOWHITE: 0xffdeadff,
    NAVY: 0x000080ff,
    OLDLACE: 0xfdf5e6ff,
    OLIVE: 0x808000ff,
    OLIVEDRAB: 0x6b8e23ff,
    ORANGE: 0xffa500ff,
    ORANGERED: 0xff4500ff,
    ORCHID: 0xda70d6ff,
    PALEGOLDENROD: 0xeee8aaff,
    PALEGREEN: 0x98fb98ff,
    PALETURQUOISE: 0xafeeeeff,
    PALEVIOLETRED: 0xdb7093ff,
    PAPAYAWHIP: 0xffefd5ff,
    PEACHPUFF: 0xffdab9ff,
    PERU: 0xcd853fff,
    PINK: 0xffc0cbff,
    PLUM: 0xdda0ddff,
    POWDERBLUE: 0xb0e0e6ff,
    PURPLE: 0x800080ff,
    REBECCAPURPLE: 0x663399ff,
    RED: 0xff0000ff,
    ROSYBROWN: 0xbc8f8fff,
    ROYALBLUE: 0x4169e1ff,
    SADDLEBROWN: 0x8b4513ff,
    SALMON: 0xfa8072ff,
    SANDYBROWN: 0xf4a460ff,
    SEAGREEN: 0x2e8b57ff,
    SEASHELL: 0xfff5eeff,
    SIENNA: 0xa0522dff,
    SILVER: 0xc0c0c0ff,
    SKYBLUE: 0x87ceebff,
    SLATEBLUE: 0x6a5acdff,
    SLATEGRAY: 0x708090ff,
    SLATEGREY: 0x708090ff,
    SNOW: 0xfffafaff,
    SPRINGGREEN: 0x00ff7fff,
    STEELBLUE: 0x4682b4ff,
    TAN: 0xd2b48cff,
    TEAL: 0x008080ff,
    THISTLE: 0xd8bfd8ff,
    TOMATO: 0xff6347ff,
    TRANSPARENT: 0x00000000,
    TURQUOISE: 0x40e0d0ff,
    VIOLET: 0xee82eeff,
    WHEAT: 0xf5deb3ff,
    WHITE: 0xffffffff,
    WHITESMOKE: 0xf5f5f5ff,
    YELLOW: 0xffff00ff,
    YELLOWGREEN: 0x9acd32ff
};
const UNITS = ['pt', 'px', 'pc', 'in', 'mm', 'cm', 'em', 'ex', 'ch', 'rem', 'vw', 'vh', 'vmin', 'vmax', '%'];

function strStyleToObj(strStyle = "", important = false) {
    const objStyle = {};
    strStyle.split(";").map((style) => {
        if (style.length && style.indexOf(":")) {
            const _style = (important ? style.replace("!important", "") : style).trim().split(":").map((c) => c.trim());
            objStyle[_style[0]] = _style[1];
        }
    });
    return objStyle;
}

function objStyleToStr(objStyle, important) {
    const strCss = [];
    Object.keys(objStyle).map((cssName) => {
        strCss.push(cssName + ":" + `${objStyle[cssName]}${important ? " !important" : ""}`);
    });
    return strCss.join(";");
}

function setStyle(style, name, value, important = false) {
    const objStyle = strStyleToObj(style, important);
    objStyle[name] = value;
    return objStyleToStr(objStyle, important);
}

function getUnitVal(value, important = false) {
    const result = {};
    UNITS.map((unit) => {
        if (value.indexOf(unit) > 0) {
            result.value = value.replace(unit, "").replace(important ? "!important" : "", "");
            result.unit = unit;
        }
    });
    return result;
}

const BORDER_SIDES = ["border", "border-left", "border-top", "border-right", "border-bottom"]


class BorderStyle extends Component {
    setup() {
        super.setup();
        this.style = [
            {label: "Dashed", value: "dashed"},
            {label: "Dotted", value: "dotted"},
            {label: "Solid", value: "solid"},
            {label: "Double", value: "double"},
            {label: "Inset", value: "inset"},
            {label: "Outset", value: "outset"},
            {label: "Ride", value: "ride"},
            {label: "Unset", value: "unset"},
            {label: "None", value: "none"},
        ];
        this.units = UNITS;
        this.sides = BORDER_SIDES;
        this.state = useState({side: this.props.side});
        this.getSideInfo();
        onWillUpdateProps(async (nextProps) => {
            if (nextProps.node && (this.props.node.nodeId != nextProps.node.nodeId)) {
                this.getSideInfo(nextProps.node);
            }
        });
        onWillStart(async () => {
            await this._lazyloadWysiwyg();
        });
    }

    onChange(name, value) {
        const {node, onChange, important} = this.props, {side} = this.state;
        const currentSide = this.sideInfo[side];
        currentSide[name] = value;
        const {width, unit, style, color} = currentSide;
        node.attrs.style = setStyle(node.attrs.style || "", side, width + unit + " " + style + " " + color, important);
        if (onChange) {
            onChange();
        }
    }

    getSideInfo(node = this.props.node) {
        this.sideInfo = {};
        BORDER_SIDES.map((side) => {
            this.sideInfo[side] = this.prepareSideInfo(side, node);
        });
    }

    prepareSideInfo(name, node) {
        const info = {style: "none", width: 0, unit: "px", color: "none"};
        if (node.el) {
            const borderData = strStyleToObj(node.attrs.style, this.props.important)[name] || node.el.css(name) || "";
            if (borderData.length) {
                const dataSplit = borderData.split(" "), {value, unit} = getUnitVal(dataSplit[0]);
                info.width = value;
                info.unit = unit;
                info.style = dataSplit[1];
                info.color = dataSplit.splice(2, dataSplit.length).join(" ");
            }
        }
        return info;
    }

    async _lazyloadWysiwyg() {
        const colorPalette = await odoo.loader.modules.get('@web_editor/js/wysiwyg/widgets/color_palette');
        this.ColorPalette = colorPalette.ColorPalette;
    }

    get colorPaletteProps() {
        return {
            onColorPicked: (colorInfo) => {
                this.onChange("color", colorInfo.color);
            },
            onCustomColorPicked: (colorInfo) => {
                this.onChange("color", colorInfo.color);
            },
            withGradients: true,
        }
    }

}

BorderStyle.defaultProps = {
    side: "border",
}
BorderStyle.template = "dynamic_odoo.CssWidget.BorderStyle";
BorderStyle.props = {
    side: {
        optional: true,
        type: String,
        validate: (t) => BORDER_SIDES.includes(t)
    },
    node: {type: Object, optional: true},
    important: {type: Boolean, optional: true},
    onChange: {type: Function, optional: true}
}

class Units extends Component {
    setup() {
        super.setup();
        const {value} = this.props;
        this.units = UNITS;
        this.state = useState({value: value});
        onWillUpdateProps((nextProps) => {
            if (nextProps.value != this.state.value) {
                this.state.value = nextProps.value;
            }
        })
    }

    onChange(ev) {
        const {onChange} = this.props;
        this.state.value = ev.target.value;
        if (onChange) {
            onChange(this.state.value);
        }
    }
}

Units.defaultProps = {
    value: "px",
}
Units.template = "dynamic_odoo.CssWidget.units";
Units.props = {
    value: {type: String, optional: true, validate: (t) => UNITS.includes(t)},
    onChange: {type: Function, optional: true}
}

class CssAttribute extends Component {
    setup() {
        super.setup();
        const self = this;
        this.state = useState({...this.prepareState(this.props)});
        this.input = useRef("input");
        this.units = UNITS;
        onMounted(this.onMounted);
        onWillUnmount(this.onWillUnmount);
        onWillUpdateProps((nextProps) => {
            Object.assign(self.state, this.prepareState(nextProps));
        });
    }

    isSvg() {
        return this.props.icon.indexOf("Studio.icon") >= 0;
    }

    prepareState(props) {
        const {value, important, _default, name, useUnit} = props,
            state = {
                value: value,
                active: name && (_default == value), ...((useUnit && value) ? getUnitVal(value, important) : {})
            };
        return state;
    }

    async keyupListenerCallback(ev) {
        ev.stopPropagation();
        ev.stopImmediatePropagation();
        const {node, name} = this.props;
        if (ev.keyCode == 13 && node && name) {
            this.state.value = ev.target.value
            this.onChange();
        }
    }

    onMounted() {
        if (this.input.el) {
            this.keyupListenerCallback = this.keyupListenerCallback.bind(this);
            this.input.el.addEventListener('keyup', this.keyupListenerCallback);
        }
    }

    onWillUnmount() {
        if (this.input.el) {
            this.input.el.removeEventListener('keyup', this.keyupListenerCallback);
        }
    }

    onClickIcon() {
        this.state.value = !this.state.value;
        this.onChange();
    }


    onSelect(ev) {
        this.state.value = ev.target.value;
        this.onChange();
    }

    onChangeUnit(unit) {
        this.state.unit = unit;
        this.onChange();
    }

    setStyle(value) {
        const {node, name, _default, useUnit, important, unit} = this.props;
        node.attrs.style = setStyle(node.attrs.style || "", name, _default ? _default : (useUnit ? ((value || 0) + this.state.unit || unit) : value), important);
    }

    onChange() {
        const {action, node, name, noUpdate, isStyle, onChange} = this.props, {value} = this.state;
        if (action) {
            action.bind(this)(name, value);
        } else if (node && name && isStyle) {
            this.setStyle(value);
        }
        if (!noUpdate && onChange) {
            onChange();
        }
    }
}

CssAttribute.template = "dynamic_odoo.CssWidget.CssAttribute";
CssAttribute.defaultProps = {
    type: "icon",
    isStyle: true,
    // useUnit: true,
}
CssAttribute.props = {
    type: {type: String, optional: true, validate: t => ["icon", "input", "select", "block"].includes(t)},
    node: {type: Object, optional: true},
    isStyle: {type: Boolean, optional: true},
    icon: {type: String, optional: true},
    name: {type: String, optional: true},
    _default: {type: String, optional: true},
    value: {type: [String, Object], optional: true},
    action: {type: Function, optional: true},
    noUpdate: {type: Boolean, optional: true},
    label: {type: String, optional: true},
    options: {type: Array, optional: true},
    onChange: {type: Function, optional: true},
    useUnit: {type: Boolean, optional: true},
    classes: {type: String, optional: true},
    important: {type: Boolean, optional: true}
}
CssAttribute.components = {Units}

class ChooseColor extends CssAttribute {
    setup() {
        super.setup();
        onWillStart(async () => {
            await this._lazyloadWysiwyg();
        });
    }

    async _lazyloadWysiwyg() {
        const colorPalette = await odoo.loader.modules.get('@web_editor/js/wysiwyg/widgets/color_palette');
        this.ColorPalette = colorPalette.ColorPalette;
    }

    onColorPicker(colorInfo) {
        this.setStyle(colorInfo.color);
        if (this.props.onChange) {
            this.props.onChange();
        }
    }

    get colorPaletteProps() {
        const self = this;
        return {
            onColorPicked: (colorInfo) => {
                self.onColorPicker(colorInfo);
            },
            onCustomColorPicked: (colorInfo) => {
                self.onColorPicker(colorInfo);
            },
            withGradients: true,
        }
    }
}

ChooseColor.template = "dynamic_odoo.CssWidget.ChooseColor";

class FontSize extends Component {
    setup() {
        super.setup();
        const DEFAULT = {value: 13, unit: "px"};
        const self = this, {value, important} = this.props;
        this.state = useState({...(value ? getUnitVal(value, important) : DEFAULT)});
        this.dot = useRef("dot");
        this.wrap = useRef("wrap");
        this.units = UNITS;
        onMounted(() => {
            this.bindDraggable();
            this.fillCss();
        });
        onWillUpdateProps((nextProps) => {
            const {value, unit} = self.state, {important} = this.props;
            if (nextProps.value != (value + unit)) {
                Object.assign(self.state, nextProps.value ? getUnitVal(nextProps.value, important) : DEFAULT);
            }
        });
        onPatched(() => {
            this.bindDraggable();
            this.fillCss();
        });
    }

    bindDraggable() {
        const self = this, {onChange} = this.props;
        $(this.dot.el).draggable({
            axis: "x",
            containment: ".slideOver",
            drag: function (event, ui) {
                self.state.value = self.fsByLeft(ui.position.left);
                self.fillCss(ui.position.left);
            },
            stop: function (event, ui) {
                self.state.value = self.fsByLeft(ui.position.left);
                self.fillCss(ui.position.left);
                self.setStyle();
                onChange();
            }
        });
    }

    setStyle() {
        const {unit, value} = this.state, {node, important} = this.props;
        node.attrs.style = setStyle(node.attrs.style || "", "font-size", value + unit, important);
    }

    fillCss(left) {
        left = left || this.leftByFS(this.state.value);
        const wrap = $(this.wrap.el);
        wrap.find(".dot").css({left: left + "px"});
        wrap.find(".lineOver").css({width: (left + 3) + "px"});
    }

    get per() {
        const wrap = $(this.wrap.el), width = wrap.find(".slideOver").outerWidth();
        return (width - 16) / 100;
    }

    fsByLeft(left) {
        return Math.round(parseFloat(left) / this.per);
    }

    leftByFS(fontSize) {
        return Math.round(parseFloat(fontSize) * this.per);
    }

    onChangeUnit(unit) {
        const {onChange} = this.props;
        this.state.unit = unit;
        this.setStyle();
        if (onChange) {
            onChange();
        }
    }
}

FontSize.template = "dynamic_odoo.CssWidget.FontSize";
FontSize.components = {Units}

export class CssWidget extends Component {
    setup() {
        if (!odoo.studio.css) {
            odoo.studio.css = {};
        }
        super.setup();
        this.drag_area = useRef("drag_area");
        this.state = useState({pinned: odoo.studio.css.pinned || true});
        useEffect(() => {
            this.bindDraggable();
        });
        onWillUpdateProps((nextProps) => {
            console.log(nextProps)
        })
    }

    bindDraggable() {
        const {top, left} = odoo.studio.css.position || {};
        if (top && left) {
            $(this.drag_area.el).css({top: top, left: left});
        }
        $(this.drag_area.el).draggable({
            handle: ".drag_area",
            stop: function (event, ui) {
                odoo.studio.css.position = ui.position;
            },
        });
    }

    onSetup() {
        const {node, important} = this.props;
        this.objStyle = strStyleToObj(node.attrs.style || "", important);
        const isFlex = ["flex"].includes(this.getCss("display")),
            hasBgImage = !["none", ""].includes(this.getCss("background-image"));
        this.style = {
            width: {
                widget: CssAttribute,
                props: {name: "width", node: node, important: important, useUnit: true, label: "W", type: "input"}
            },
            height: {
                widget: CssAttribute,
                props: {name: "height", node: node, important: important, useUnit: true, label: "H", type: "input"}
            },
            copy: {
                widget: CssAttribute, props: {
                    icon: "Studio.icon.copy",
                    action: (name, value) => {
                        node.copy = value;
                    },
                    noUpdate: true,
                    important: important,
                    isStyle: false,
                }
            },
            paste: {
                widget: CssAttribute, props: {
                    icon: "Studio.icon.paste",
                    action: (name, value) => {
                        if (node.copy) {
                            delete node.copy;
                            const {xpathNode, copyNode} = node.params;
                            xpathNode(node, [copyNode(node)]);
                        }
                    },
                    important: important,
                    isStyle: false,
                }
            },
            remove: {
                widget: CssAttribute, props: {
                    icon: "Studio.icon.remove",
                    action: (name, value) => {
                        const {removeNode} = node.params;
                        removeNode(node);
                    },
                    important: important,
                    isStyle: false,
                }
            },
            align_left: {
                widget: CssAttribute,
                props: {
                    name: "text-align",
                    _default: "left",
                    important: important,
                    node: node,
                    icon: "Studio.icon.align-left"
                }
            },
            align_center: {
                widget: CssAttribute,
                props: {
                    name: "text-align",
                    _default: "center",
                    important: important,
                    node: node,
                    icon: "Studio.icon.align-center"
                }
            },
            align_right: {
                widget: CssAttribute,
                props: {
                    name: "text-align",
                    _default: "right",
                    important: important,
                    node: node,
                    icon: "Studio.icon.align-right"
                }
            },
            color: {
                widget: ChooseColor, props: {
                    node: node,
                    name: "color",
                    important: important,
                    icon: "Studio.icon.color",
                }
            },
            bg_color: {
                widget: ChooseColor, props: {
                    node: node,
                    important: important,
                    name: "background-color",
                    icon: "Studio.icon.bgColor",
                }
            },
            bg_image: {
                widget: CssAttribute,
                props: {
                    node: node,
                    isStyle: false,
                    important: important,
                    name: "background-image",
                    classes: hasBgImage ? "hasSub" : "",
                    icon: "picture-o",
                    action: this.onShowChooseImage,
                }
            },
            font_weight: {
                widget: CssAttribute,
                props: {
                    name: "font-weight",
                    _default: "700",
                    important: important,
                    node: node,
                    icon: "Studio.icon.text-bold"
                }
            },
            font_style: {
                widget: CssAttribute,
                props: {
                    name: "font-style",
                    _default: "italic",
                    important: important,
                    node: node,
                    icon: "Studio.icon.text-italic"
                }
            },
            underline: {
                widget: CssAttribute,
                props: {
                    name: "text-decoration",
                    _default: "underline",
                    important: important,
                    node: node,
                    icon: "Studio.icon.text-underline"
                }
            },
            font_size: {
                widget: FontSize, props: {node: node, important: important, value: this.getCss("font-size")}
            },
            border: {widget: BorderStyle, props: {node: node, important: important}},
            margin_left: {
                widget: CssAttribute,
                props: {name: "margin-left", node: node, important: important, useUnit: true, label: "L", type: "input"}
            },
            margin_right: {
                widget: CssAttribute,
                props: {
                    name: "margin-right",
                    node: node,
                    important: important,
                    useUnit: true,
                    label: "R",
                    type: "input"
                }
            },
            margin_top: {
                widget: CssAttribute,
                props: {name: "margin-top", node: node, important: important, useUnit: true, label: "T", type: "input"}
            },
            margin_bottom: {
                widget: CssAttribute,
                props: {
                    name: "margin-bottom",
                    node: node,
                    important: important,
                    useUnit: true,
                    label: "B",
                    type: "input"
                }
            },
            padding_left: {
                widget: CssAttribute,
                props: {
                    name: "padding-left",
                    node: node,
                    important: important,
                    useUnit: true,
                    label: "L",
                    type: "input"
                }
            },
            padding_right: {
                widget: CssAttribute,
                props: {
                    name: "padding-right",
                    node: node,
                    important: important,
                    useUnit: true,
                    label: "R",
                    type: "input"
                }
            },
            padding_top: {
                widget: CssAttribute,
                props: {name: "padding-top", node: node, important: important, useUnit: true, label: "T", type: "input"}
            },
            padding_bottom: {
                widget: CssAttribute,
                props: {
                    name: "padding-bottom",
                    node: node,
                    important: important,
                    useUnit: true,
                    label: "B",
                    type: "input"
                }
            },
            display_inline: {
                widget: CssAttribute,
                props: {name: "display", node: node, important: important, label: "Inline", _default: "inline"}
            },
            display_block: {
                widget: CssAttribute,
                props: {name: "display", node: node, important: important, label: "Block", _default: "block"}
            },
            display_flex: {
                widget: CssAttribute,
                props: {
                    name: "display",
                    classes: isFlex ? "hasSub" : "",
                    important: important,
                    node: node,
                    label: "Flex",
                    _default: "flex"
                }
            },
            font_family: {
                widget: CssAttribute,
                props: {
                    name: "font-family",
                    node: node,
                    type: "select",
                    important: important,
                    options: this.prepareFontOptions()
                }
            },
            background_size: {
                widget: CssAttribute,
                props: {
                    name: "background-size",
                    label: "Background Size",
                    node: node,
                    important: important,
                    type: "select",
                    options: this.prepareOptions(["auto", "contain", "cover", "inherit", "initial", "revert", "unset"]),
                }
            },
            background_repeat: {
                widget: CssAttribute,
                props: {
                    name: "background-repeat",
                    label: "Background Repeat",
                    node: node,
                    important: important,
                    type: "select",
                    options: this.prepareOptions(["inherit", "initial", "no-repeat", "repeat", "repeat-x", "repeat-y", "revert", "round", "space", "unset"]),
                }
            },
            background_position: {
                widget: CssAttribute,
                props: {
                    name: "background-position",
                    label: "Background position",
                    node: node,
                    important: important,
                    type: "select",
                    options: this.prepareOptions(["bottom", "center", "inherit", "initial", "top", "left", "right", "revert", "unset"]),
                }
            },
            background_attachment: {
                widget: CssAttribute,
                props: {
                    name: "background-attachment",
                    label: "Background Attachment",
                    node: node,
                    important: important,
                    type: "select",
                    options: this.prepareOptions(["fixed", "inherit", "initial", "local", "revert", "scroll", "unset"]),
                }
            },
            background_blend_mode: {
                widget: CssAttribute,
                props: {
                    name: "background-blend-mode",
                    label: "Background Blend Mode",
                    node: node,
                    important: important,
                    type: "select",
                    options: this.prepareOptions(["color", "color-burn", "color-dodge", "darken", "difference", "exclusion", "hard-light", "hue", "inherit",
                        "initial", "lighten", "luminosity", "multiply", "normal", "overlay", "revert", "saturation"]),
                }
            },
            flex_direction: {
                widget: CssAttribute,
                props: {
                    name: "flex-direction",
                    label: "Flex Direction",
                    node: node,
                    important: important,
                    type: "select",
                    options: this.prepareOptions(["column", "column-revert", "row", "row-revert"]),
                }
            },
            align_content: {
                widget: CssAttribute,
                props: {
                    name: "align-content",
                    label: "Align Content",
                    node: node,
                    important: important,
                    type: "select",
                    options: this.prepareOptions(["flex-end", "flex-start"]),
                }
            },
            align_items: {
                widget: CssAttribute,
                props: {
                    name: "align-items",
                    label: "Align Items",
                    node: node,
                    important: important,
                    type: "select",
                    options: this.prepareOptions(["flex-end", "flex-start"]),
                }
            },
            align_self: {
                widget: CssAttribute,
                props: {
                    name: "align-self",
                    label: "Align Self",
                    node: node,
                    important: important,
                    type: "select",
                    options: this.prepareOptions(["flex-end", "flex-start"]),
                }
            },
            justify_content: {
                widget: CssAttribute,
                props: {
                    name: "justify-content",
                    label: "Justify Content",
                    node: node,
                    important: important,
                    type: "select",
                    options: this.prepareOptions(["flex-end", "flex-start"]),
                }
            },
            justify_items: {
                widget: CssAttribute,
                props: {
                    name: "justify-items",
                    label: "Justify Items",
                    node: node,
                    important: important,
                    type: "select",
                    options: this.prepareOptions(["flex-end", "flex-start"]),
                }
            },
            place_self: {
                widget: CssAttribute,
                props: {
                    name: "place-self",
                    label: "Place Self",
                    node: node,
                    important: important,
                    type: "select",
                    options: this.prepareOptions(["auto", "baseline", "center", "end", "flex-end", "flex-start", "normal", "self-end", "self-start", "start", "stretch"]),
                }
            },
            place_content: {
                widget: CssAttribute,
                props: {
                    name: "place-content",
                    label: "Place Content",
                    node: node,
                    important: important,
                    type: "select",
                    options: this.prepareOptions(["baseline", "center", "end", "flex-end", "flex-start", "normal", "space-around", "space-between", "space-evenly", "start", "stretch"]),
                }
            },
            place_items: {
                widget: CssAttribute,
                props: {
                    name: "place-items",
                    label: "Place Items",
                    node: node,
                    important: important,
                    type: "select",
                    options: this.prepareOptions(["baseline", "center", "end", "flex-end", "flex-start", "normal", "self-end", "self-start", "start", "stretch"]),
                }
            },

        }

        this.views = [
            {
                rows: [{name: "group1", views: ["copy", "paste", "remove"]},
                    {name: "group2", views: ["align_left", "align_center", "align_right"]}]
            },
            {
                classes: "reverse_group",
                rows: [
                    {name: "group3", views: ["color", "bg_color", "bg_image"]},
                    {name: "group4", views: ["font_weight", "font_style", "underline"]}
                ]
            },
            hasBgImage ?
                {
                    classes: "wrap_group",
                    rows: [
                        {name: "group_112", classes: "bg_sub_style", views: ["background_size"]},
                        {name: "group_114", classes: "bg_sub_style", views: ["background_repeat"]},
                        {name: "group_113", classes: "bg_sub_style", views: ["background_attachment"]},
                        {name: "group_115", classes: "bg_sub_style", views: ["background_position"]},
                        {name: "group_117", classes: "bg_sub_style", views: ["background_blend_mode"]},
                    ]
                } : {},
            {
                classes: "reverse_group",
                rows: [
                    {name: "group123", views: ["display_inline", "display_block", "display_flex"]},
                    {name: "group091", views: ["font_family"]}
                ]
            },
            isFlex ?
                {
                    classes: "wrap_group",
                    rows: [
                        {classes: "bg_sub_style", views: ["flex_direction"]},
                        {classes: "bg_sub_style", views: ["align_content"]},
                        {classes: "bg_sub_style", views: ["align_self"]},
                        {classes: "bg_sub_style", views: ["align_items"]},
                        {classes: "bg_sub_style", views: ["justify_content"]},
                    ]
                } : {},
            isFlex ?
                {
                    classes: "wrap_group",
                    rows: [
                        {classes: "bg_sub_style", views: ["justify_items"]},
                        {classes: "bg_sub_style", views: ["place_self"]},
                        {classes: "bg_sub_style", views: ["place_content"]},
                        {classes: "bg_sub_style", views: ["place_items"]},
                    ]
                } : {},
            {
                rows: [
                    {name: "group5", views: ["border"]}
                ]
            },
            {
                rows: [
                    {name: "group6", views: ["font_size"]}, {
                        name: "group7",
                        classes: "g_wh",
                        views: ["width", "height"]
                    }
                ]
            },
            {
                rows: [
                    {
                        name: "group6",
                        classes: "g_margin hasTitle",
                        title: "Margin",
                        views: ["margin_top", "margin_bottom", "margin_right", "margin_left"]
                    },
                    {
                        name: "group7",
                        classes: "g_padding hasTitle",
                        title: "Padding",
                        views: ["padding_top", "padding_bottom", "padding_right", "padding_left"]
                    }
                ]
            }
        ]
    }

    getCss(name) {
        return this.objStyle[name] || (this.props.node.el || $("<div>")).css(name);
    }

    prepareStyleProps(view) {
        const props = {...this.style[view].props, onChange: this.onNodeChangeProp.bind(this)};
        if (props.name) {
            props.value = this.getCss(props.name);
        }
        return props;
    }

    prepareOptions(vals = []) {
        return vals.map((val) => ({label: val[0].toUpperCase() + val.slice(1, val.length), value: val}));
    }

    prepareFontOptions() {
        const fonts = ["Arial", "Verdana", "Helvetica", "Tahoma", "Trebuchet MS", "Times New Roman", "Georgia", "Garamond", "Courier New", "Brush Script MT"];
        const currentFont = this.getCss("font-family");
        if (currentFont && typeof currentFont != 'undefined' && !fonts.includes(currentFont)) {
            fonts.push(currentFont);
        }
        return this.prepareOptions(fonts);
    }

    onNodeChangeProp() {
        const {onNodeChangeProp, node} = this.props;
        if (onNodeChangeProp) {
            onNodeChangeProp(node.attrs.style);
        }
    }

    onPinned() {
        this.state.pinned = !this.state.pinned;
        odoo.studio.css.pinned = this.state.pinned;
    }

    async onShowChooseImage(name, value) {
        const self = this;
        this.env.services.dialog.add(MediaDialog, {
            onlyImages: true,
            save: image => {
                const {node, onChange, important} = self.props, objStyle = strStyleToObj(node.attrs.style, important),
                    url = $(image).attr("src");
                objStyle[name] = "url(" + url + ")";
                node.attrs.style = objStyleToStr(objStyle, important);
                self.state.value = url;
                onChange();
            }
        });
    }
}

CssWidget.template = "dynamic_odoo.CssWidget";
CssWidget.defaultProps = {
    important: true,
}
CssWidget.props = {
    el: {type: Object, optional: true},
    value: {type: [Array, Object, String], optional: true},
    node: {type: Object, optional: true},
    onNodeChangeProp: {type: Function, optional: true},
    update: {type: Function, optional: true},
    important: {type: Boolean, optional: true}
}