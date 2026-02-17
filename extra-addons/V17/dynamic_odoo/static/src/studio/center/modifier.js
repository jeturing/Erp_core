/** @odoo-module **/

import {GROUPABLE_TYPES} from "@web/search/utils/misc";
import {Tab} from "@dynamic_odoo/core/widgets/tab/tab";
import {useService} from "@web/core/utils/hooks";
import {registry} from "@web/core/registry";
import {Domain} from "@web/core/domain";
import {Dialog} from "@web/core/dialog/dialog";
import {jsonNodeToString} from "@dynamic_odoo/core/utils/view";
import {studioListener} from "@dynamic_odoo/core/studio_core";
import {OhField} from "@dynamic_odoo/core/widgets/drag_component/drag_component";
import {Field} from "@dynamic_odoo/core/fields/field";
import {useSortService} from "@dynamic_odoo/core/services/sort_service";
import {ViewComponent} from "./view_components";
import {StructureNode} from "@dynamic_odoo/core/widgets/structure_node/structure_node";
import {evaluateBooleanExpr} from "@web/core/py_js/py";
import {domainFromExpression, expressionFromDomain} from "@web/core/tree_editor/condition_tree";
import {floorRandom} from "@dynamic_odoo/core/utils/format";
import {conditionToDomain} from "@dynamic_odoo/core/utils/domain";

const {Component, toRaw, useSubEnv, onPatched, useState, useEffect, onWillUpdateProps, xml} = owl;
const fieldRegistry = registry.category("fields");

const NodeID = () => "nodeId_" + Math.random().toString().replace(".", "");
const ColPrefix = ["col", "col-sm", "col-md", "con-lg", "col-xl"];
const GetCols = (node) => {
    const result = {classes: []};
    (node.attrs.class || "").split(" ").map((cl) => {
        cl = cl.trim();
        if (cl == "col") {
            result.type = "col";
            return;
        }
        if (cl.indexOf("col-") >= 0) {
            ColPrefix.map((ck) => {
                if (cl.indexOf(ck + "-") >= 0) {
                    result.type = ck;
                    result.cols = parseInt(cl.split(ck + "-")[1]);
                }
            });
            return;
        }
        result.classes.push(cl);
    });
    return result;
}
const setCols = (node, value, kind) => {
    const {type, cols, classes} = GetCols(node);
    if (kind == "type") {
        classes.push(cols ? (value + "-" + cols) : value);
    } else if (kind == "cols") {
        classes.push(value ? (type + "-" + value) : type);
    }
    node.attrs.class = classes.join(" ");
}

const getMCR = (node, mcrType) => {
    const mcr = [];
    node.children.map((child) => {
        const {type, name} = child.attrs;
        if (type == mcrType) {
            mcr.push(name)
        }
    });
    return mcr;
}

const mcrProps = (node, types, attrName) => {
    const model = node.attrs.model || (odoo.studio && odoo.studio.getState().model), value = getMCR(node, attrName);
    return {
        relation: "ir.model.fields",
        value_name: "name",
        value: value,
        domain: [["store", "=", true], ["ttype", "in", types], ["name", "!=", "id"], ["model", "=", model]],
    }
}

const mcrOnchange = (node, prop, value) => {
    const propName = prop.name,
        options = Array.isArray(value) ? value.map((val) => ({name: val, value: val})) : [{name: value, value: value}];
    const children = node.children.filter((child) => {
        const {type} = child.attrs;
        return type != propName;
    });
    const fieldsGroup = options.map((option) => {
        return {tag: "field", attrs: {name: option.value, type: propName}};
    });
    node.children = children.concat(fieldsGroup);
}

export const PropBoolean = (params = {}) => {
    return {
        type: Boolean, optional: true, modifierProps: {
            widget: "radio", ...params
        }
    }
}

export const preModifierProps = (params = {}, propName) => {
    return {
        type: Boolean, optional: true, modifierProps: {
            widget: "radio", widgetProps: (self, node) => {
                let value = node.attrs[propName];
                if (propName == "invisible" && node.attrs.hasOwnProperty("column_invisible")) {
                    value = node.attrs["column_invisible"];
                }
                const widgetProps = {
                    ...params, model: odoo.studio.getState().model, useCondition: true
                }
                const setValue = (value) => {

                    try {
                        widgetProps.value = evaluateBooleanExpr(value);
                        if (["true", "True", "False", "false"] == value) {
                            widgetProps.value = evaluateBooleanExpr(value);
                        } else {
                            widgetProps.condition = (new Domain(conditionToDomain(value))).toString();
                        }
                    } catch (error) {
                        widgetProps.condition = domainFromExpression(value, {
                            getFieldDef: self.getFieldDef.bind(self),
                        });
                    }
                }
                if (value) setValue(value);
                return widgetProps;
            }, onChange: (node, prop, data, params = {}) => {
                let propName = prop.name, value = data.value;
                if (data.isCondition) {
                    value = expressionFromDomain(value, {
                        getFieldDef: params.self.getFieldDef.bind(params.self),
                    });
                } else {
                    value = value ? "True" : "False";
                }
                if ((node.parentNode || {}).tag == "tree" && propName == "invisible") {
                    propName = "column_invisible";
                }
                node.attrs[propName] = value;
            }
        }
    }
}

export class NodeModifier {
    constructor(node, params = {}) {
        this.node = node;
        this.params = params;
        this.setup();
    }

    setup() {
        this.views = this.prepareViewByNode(this.node);
        if ((this.oldViews || []).toString() != this.views.toString()) {
            this.callBackStore = {views: {}, tabs: {}, fields: []};
            this.props = this.preparePropsByNode(this.views);
            this.fields = this.prepareFields(this.views, this.props);
            this.oldViews = this.views;
            return true;
        }
        return false;
    }

    get el() {
        if (this.node.nodeId) {
            return $(document).find("[node-id='" + this.node.nodeId + "']");
        }
        return null;
    }

    prepareViewByNode(node) {
        if (!node?.tag) {
            return [];
        }
        const {viewInfo} = this.params, {nodeViewStore} = this.constructor;
        const findView = nodeViewStore.filter((view) => view[0].includes("[" + node.tag + "]") || view[0].includes("[*]"));
        if (findView.length) {
            let viewCheck = []
            findView.map((view) => {
                viewCheck = view[1];
                if (viewCheck.length == 2 && (typeof viewCheck[0] === "function")) {
                    viewCheck = viewCheck[0](this.node, this.preparePropsByNode(viewCheck[1]));
                } else if (typeof viewCheck === "function") {
                    viewCheck = viewCheck(this.node, viewInfo);
                }
            });
            return viewCheck;
        }
        return [];
    }

    preparePropsByNode(views) {
        const props = {}, {nodeProps, nodePropsDefault} = this.constructor;
        views.map((propName) => {
            const {prepareProp} = ((nodeProps[propName] || {}).modifierProps || {});
            if (prepareProp) {
                prepareProp.bind(this)(this.node, props);
            } else if (propName in this.node.attrs) {
                props[propName] = this.node.attrs[propName];
            } else if (propName in nodePropsDefault) {
                props[propName] = nodePropsDefault[propName];
            }
        });
        return props;
    }

    prepareFields(views, nodeParams) {
        const fields = {},
            widgets = {String: "char", Boolean: "checkbox", Number: "integer"}, {nodeProps} = this.constructor;

        views.map((propName) => {
            const prop = {...nodeProps[propName], name: propName}, {modifierProps, noLabel, type} = prop;
            const isArray = Array.isArray(modifierProps || {});
            const prepareFieldProps = (_modifierProps) => {
                const {label, widget, component, widgetProps} = _modifierProps;
                const fieldProps = {
                    ...(widgetProps ? widgetProps(this, this.node) : {}),
                    update: (value) => this.onChangeProp.bind(this)(prop, value)
                }
                if (!fieldProps.hasOwnProperty("value") && propName in nodeParams) {
                    fieldProps.value = nodeParams[propName];
                }
                return {
                    label: noLabel ? false : (label || propName.split("_").map((ch) => ch.charAt(0).toUpperCase() + ch.slice(1)).join(" ")),
                    type: widget || widgets[type.name],
                    component: component || false,
                    props: fieldProps,
                };
            }
            const getModifierProps = () => {
                const paramsDepend = modifierProps[1].map((_prop) => ({[_prop]: nodeParams[_prop]})).reduce((obj, [k, v]) => {
                    obj[k] = v
                });
                modifierProps[1].map((propDepend) => {
                    if (!this.callBackStore.fields[propDepend]) {
                        this.callBackStore.fields[propDepend] = [];
                    }
                    this.callBackStore.fields[propDepend].push((propDependVal) => {
                        fields[propName] = prepareFieldProps(modifierProps[0]({
                            ...paramsDepend, [propDepend]: propDependVal
                        }));
                    });
                });
                return modifierProps[0](paramsDepend);
            };
            fields[propName] = prepareFieldProps(isArray ? getModifierProps() : (modifierProps || {}));
        });
        return fields;
    }

    newNode(tag, params = {}) {
        const node = {tag: tag, ...params}
        return node;
    }

    getFieldDef(name) {
        if (typeof name === "string") {
            return this.params.viewInfo.fields[name] || null;
        }
        return null;
    }

    async onChangeProp(prop, value) {
        const {name, modifierProps} = prop, {onChange} = modifierProps || {};
        if (onChange) {
            await onChange(this.node, prop, value, {self: this});
        } else {
            this.node.attrs[name] = value;
        }
        if (!this.setup()) {
            if (name in this.callBackStore.fields) {
                this.callBackStore.fields[name].map((cb) => {
                    cb(value);
                });
            }
            this.fields[name].props.value = value;
        }
        const {onNodeChangeProp} = this.params;
        if (onNodeChangeProp) {
            onNodeChangeProp(prop, value);
        }
    }
}

NodeModifier.nodePropsDefault = {}
NodeModifier.nodeProps = {
    required: preModifierProps({label: "Required"}, "required"),
    invisible: preModifierProps({label: "Invisible"}, "invisible"),
    readonly: preModifierProps({label: "Readonly"}, "readonly"),
    show_all_invisible: PropBoolean({widget: "toggle_switch", label: "Show All Invisible"}),
    editable: PropBoolean({label: "Editable"}),
    edit: PropBoolean({
        label: "Can Edit", widgetProps: (self, node) => {
            return {value: node.attrs.hasOwnProperty("edit") ? node.attrs.edit : true}
        }
    }),
    create: PropBoolean({
        label: "Can Create", widgetProps: (self, node) => {
            return {value: node.attrs.hasOwnProperty("create") ? node.attrs.create : true}
        }
    }),
    delete: PropBoolean({
        label: "Can Delete", widgetProps: (self, node) => {
            return {value: node.attrs.hasOwnProperty("delete") ? node.attrs.delete : true}
        }
    }),
    widget: {
        type: String, optional: true, modifierProps: {
            widget: "selection", widgetProps: (self, node) => {
                const getSupportedTypes = (fieldType) => {
                    const widgetSupported = [];
                    Object.entries(fieldRegistry.content).map((field, idx) => {
                        const fieldCom = field[1][1];
                        if ((fieldCom.supportedTypes || []).includes(fieldType)) {
                            widgetSupported.push([field[0], `${fieldCom.component?.name || "Widget"} (${field[0]})`])
                        }
                    });
                    return widgetSupported;
                }
                const {fields} = self.params.viewInfo, {name, widget} = node.attrs,
                    fieldType = (fields[name] || {}).type;
                return {options: getSupportedTypes(fieldType), value: widget || fieldType}
            },
        }
    },
    groups: {
        type: String, optional: true, modifierProps: {
            widget: "many2many_groups", widgetProps: (self, node) => {
                const {groups} = node.attrs, value = groups ? groups.replaceAll(" ", "").split(",") : [];
                return {relation: "res.groups", value_name: "id", value: value}
            }, onChange: (node, prop, value, params) => {
                value.length ? (node.attrs.groups = value.join(",")) : (delete node.attrs.groups);
            }
        }
    },
    string: {
        type: String, optional: true, modifierProps: {
            onChange: (node, prop, value) => {
                node.attrs.string = value;
                const idxString = (node.children || []).findIndex((child) => typeof child == "string");
                if (idxString >= 0) {
                    node.children.splice(idxString, 1, value);
                }
            }, widgetProps: (self, node) => {
                const {fields} = self.params.viewInfo, result = {}, fieldName = node.attrs.name;
                const idxString = (node.children || []).findIndex((child) => typeof child == "string");
                result.value = (idxString >= 0 ? node.children[idxString] : node.attrs.string) || ""
                if (!result.value && fields && (fieldName in fields)) {
                    result.value = fields[fieldName].string;
                }
                return result;
            }
        }
    },
    relation: {
        type: String, optional: true, modifierProps: {
            widget: "many2one", widgetProps: (self, node) => {
                const field = self.params.viewInfo.fields[node.attrs.name];
                return {relation: "ir.model", readonly: !field.isNew, value_name: "model", value: field.relation};
            }, onChange: (node, prop, value) => {
                node.attrs.relation = value;
            }
        }
    },
    root_domain: {
        type: String, optional: true, modifierProps: {
            label: "Filter",
            widget: "domain_selector",
            widgetProps: (self, node) => {
                const {model} = self.params.viewInfo, domain = node.attrs.domain, props = {model: model};
                if (domain) {
                    props.value = domain;
                }
                return props;
            },
            onChange: (node, prop, value, params) => {
                node.attrs.domain = value;
                params.self.params.viewInfo.domain = (new Domain(value)).toList({});
            }
        }
    },
    root_model: {
        type: String, optional: true, modifierProps: {
            widget: "many2one",
            label: "Model",
            widgetProps: (self, node) => {
                const props = {relation: "ir.model", value_name: "model"},
                    model = node.attrs.model || self.params.viewInfo.model;
                if (model) {
                    props.value = model;
                }
                return props;
            },
            onChange: (node, prop, value, params) => {
                node.attrs.model = value;
                params.self.params.viewInfo.model = value;
            }
        },
    },
    default_group_by: {
        type: String, optional: true, modifierProps: {
            widget: "many2one", widgetProps: (self, node) => {
                const {model} = self.params.viewInfo;
                const props = {
                    relation: "ir.model.fields",
                    domain: [['model', '=', model], ['ttype', 'in', ["many2one", "selection"]]],
                    value_name: "name",

                };
                if (node.attrs.default_group_by) {
                    props.value = node.attrs.default_group_by
                }
                return props;
            },
        }
    },
    default_order: {
        type: String, optional: true, modifierProps: {
            widget: "many2one", widgetProps: (self, node) => {
                const {model} = self.params.viewInfo;
                const props = {
                    relation: "ir.model.fields",
                    domain: [['model', '=', model], ['ttype', 'in', ["date", "datetime", "many2one", "selection"]]],
                    value_name: "name",
                };
                if (node.attrs.default_order) {
                    props.value = node.attrs.default_order
                }
                return props;
            },
        }
    },
    href: {type: String, optional: true},
    css: {
        type: String, optional: true, noLabel: true, modifierProps: {
            widget: "css", widgetProps: (self, node) => {
                return {
                    node: node,
                    el: self.el,
                    onNodeChangeProp: (value) => self.params.onNodeChangeProp({name: "css"}, value)
                }
            },
        }
    },
    icon: {
        type: String, optional: true, modifierProps: {
            widget: "choose_icon", onChange: (node, prop, value) => {
                const classes = (node.attrs.class || "").split(" ");
                ["fa", "oi"].map((ic) => {
                    const oldIcon = classes.findIndex((cl) => cl == ic);
                    if (oldIcon >= 0) {
                        classes.splice(oldIcon, 1);
                        const removeOldIcon = (_classes) => {
                            const _idx = _classes.findIndex((cl) => cl.indexOf(`${ic}-`) >= 0);
                            if (_idx >= 0) {
                                _classes.splice(_idx, 1);
                                removeOldIcon(_classes)
                            }
                        }
                        removeOldIcon(classes);
                    }
                });
                classes.push("fa fa-" + value);
                node.attrs.class = classes.join(" ");
            }
        }
    },
    color: {
        type: String, optional: true, modifierProps: {
            widget: "choose_color", onChange: (node, prop, value) => {
                const style = node.attrs.style || "", objCss = {}, strCss = [];
                style.split(";").map((st) => {
                    const _st = st.trim().split(":").map((c) => c.trim());
                    objCss[_st[0]] = _st[1];
                });
                objCss[prop.name] = value;
                Object.keys(objCss).map((cssName) => {
                    strCss.push(cssName + ":" + objCss[cssName])
                });
                node.attrs.style = strCss.join(";");
            }
        }
    },
    columns: {
        type: String, optional: true, modifierProps: {
            onChange: (node, prop, value) => {
                const childLength = node.children.length;
                if (childLength > value) {
                    node.children.splice(value, 1);
                } else if (childLength < value) {
                    const columns = [];
                    for (let i = 0; i < (value - childLength); i++) {
                        columns.push({
                            tag: node.tag, children: [], parentId: node.nodeId, attrs: {class: 'can_drag col'}
                        });
                    }
                    node.params.xpathNode(node, columns, "append", false, false)
                }
            }, widgetProps: (self, node) => {
                return {value: (node.children || []).filter((child) => child.tag).length}
            }
        }
    },
    colType: {
        type: String, optional: true, modifierProps: {
            widget: "selection",
            widgetProps: () => ({options: [["col", "Col"], ["col-sm", "Col SM"], ["col-md", "Col MD"], ["col-lg", "Col LG"], ["col-xl", "Col XL"]]}),
            prepareProp: (node, props) => {
                const colData = GetCols(node);
                props.colType = colData.type || "col";
            },
            onChange: (node, prop, value) => {
                setCols(node, value, "type");
            },
        }
    },
    cols: {
        type: String, optional: true, modifierProps: {
            prepareProp: (node, props) => {
                const colData = GetCols(node);
                props.cols = colData.cols || 0;
            }, onChange: (node, prop, value) => {
                setCols(node, value, "cols");
            },
        }
    },
    measure: {
        type: String, optional: true, modifierProps: {
            widget: "many2many", onChange: (node, prop, value) => {
                mcrOnchange(node, prop, value)
            }, widgetProps: (self, node) => {
                return mcrProps(node, ["integer", "float", "monetary"], "measure");
            }
        },
    },
    col: {
        type: String, optional: true, modifierProps: {
            widget: "many2many", onChange: (node, prop, value) => {
                mcrOnchange(node, prop, value);
            }, widgetProps: (self, node) => {
                return mcrProps(node, GROUPABLE_TYPES, "col");
            }
        },
    },
    row: {
        type: String, optional: true, modifierProps: {
            widget: "many2many", onChange: (node, prop, value) => {
                mcrOnchange(node, prop, value);
            }, widgetProps: (self, node) => {
                return mcrProps(node, GROUPABLE_TYPES, "row");
            }
        },
    },
    related: {
        type: String, optional: true, modifierProps: {
            widget: "field_selector", widgetProps: (self, node) => {
                const {fields, model} = self.params.viewInfo, field = fields[node.attrs.name];
                return {model: model, value: field.related, readonly: !field.isNew};
            }, onChange: (node, prop, value, params) => {
                const {fields} = params.self.params.viewInfo, field = fields[node.attrs.name];
                field.related = value.path;
                field.type = value.fieldInfo.type;
                node.attrs.related = value.path;
                node.attrs.type = value.fieldInfo.type;
            }
        }
    },
    more: {
        type: String, optional: true, modifierProps: {
            widget: "more", onChange: (node, prop, value) => {
            }, widgetProps: (self, node) => {
                const removeNode = () => {
                    node.params.removeNode(node.nodeId);
                    self.params.onNodeChangeProp();
                }
                return {
                    value: node.attrs.name,
                    more: node.tag == "field" && !self.params.viewInfo.fields[node.attrs.name].isNew,
                    onRemove: removeNode
                };
            }
        },
    }
}
NodeModifier.nodeViewStore = [// ["[*]", ["css", "more"]],
    ["[th], [td], [p], [span], [h1], [h2], [h3], [h4], [h5], [h6], [h7], [strong]", ["string", "css", "more"]], ["[div]", (node) => {
        if ((node.attrs.class || "").includes("row")) {
            return ["columns", "css", "more"];
        } else if (GetCols(node).type) {
            return ["colType", "cols", "css", "more"];
        } else {
            return ["css", "more"];
        }
    }], ["[a]", ["string", "href", "css"]], ["[i]", (node) => {
        return ["icon", "css"];
    }], ["[label]", (node) => node.attrs.for ? ["string", "more"] : ["string", "more", "css"]], ["[field]", ["required", "invisible", "readonly", "string", "widget", "groups", "more"]],]
NodeModifier.ShowNodeRoot = true;
NodeModifier.nodeTabs = [];

export const FIELD_ICONS = {
    datetime: "fa fa-clock-o",
    date: "fa fa-calendar",
    char: "fa fa-font",
    text: "fa fa-arrows-alt",
    many2one: "fa fa-envira",
    json: "fa fa-braille",
    one2many: "fa fa-bars",
    many2many: "fa fa-pagelines",
    many2many_tags: "fa fa-pagelines",
    integer: "fa fa-yelp",
    monetary: "fa fa-modx",
    float: "fa fa-fire",
    binary: "fa fa-file",
    signature: "fa fa-pencil",
    image: "fa fa-picture-o",
    related: "fa fa-random",
    selection: "fa fa-bars",
    statusbar: "fa fa-map-o",
    boolean: "fa fa-check-square",
    html: "fa fa-code",
}

export class TabField extends Component {
    setup() {
        super.setup();
        this.state = useState({search: false});
        onPatched(() => {
            this.props.onSearch();
        });
    }

    get fieldIcons() {
        return {...FIELD_ICONS};
    }

    onSearch(val) {
        this.state.search = val.toLowerCase();
    }
}

TabField.template = "dynamic_odoo.Modifier.TabField";
TabField.components = {DragField: OhField, Field: Field}

export class TabComponents extends Component {
    componentProps(component) {
        const {viewInfo} = this.props;
        return {viewInfo: viewInfo, ...(component.prepareProps || (() => ({})))(viewInfo)};
    }
}

TabComponents.template = "dynamic_odoo.Modifier.TabComponents";

export class ComponentTabsModifier extends Component {
    setup() {
        super.setup();
        this.prepareNodeModifier();
        onWillUpdateProps((nextProps) => {
            this.prepareNodeModifier(nextProps);
        });
    }

    prepareNodeModifier(props = this.props) {
        const {reload, viewInfo, nodeModifier} = props;
        this.nodeModifier = new nodeModifier(viewInfo.archJson, {
            onNodeChangeProp: (prop, value) => reload(prop, value),
            app: this.__owl__.app,
            viewInfo: viewInfo
        });
    }

    get tabView() {
        let viewContent = [];
        const fieldsModifier = this.nodeModifier.fields;
        if (fieldsModifier) {
            viewContent = Object.keys(fieldsModifier).map((fieldName) => ({
                component: Field, props: {...fieldsModifier[fieldName], name: fieldName}
            }));
        }
        return {name: "views", data: {label: "Views", content: viewContent}}
    }

    get DragComponent() {
        return {}
    }

    get tabComponent() {
        return {
            name: "components", data: {
                label: "Components",
                content: [{component: TabComponents, props: {...this.props, components: {...this.DragComponent}}}]
            }
        }
    }

    get tabField() {
        const {viewInfo, bindSort} = this.props, {archJson, fields} = viewInfo;
        const without_fields = [];
        const getWithoutFields = (node) => {
            if (node.tag == "field" && node.attrs.name) {
                without_fields.push(node.attrs.name);
            } else if (node.children) {
                node.children.map((_node) => {
                    getWithoutFields(_node);
                });
            }
        }
        getWithoutFields(archJson);
        archJson.children.map((field) => field.tag == "field" ? field.attrs.name : undefined);
        return {
            name: "fields", data: {
                label: "Fields", content: [{
                    component: TabField, props: {
                        fields: fields, onSearch: bindSort, without_fields: without_fields
                    }
                }]
            }
        }
    }

    get tabs() {
        return {};
    }
}

ComponentTabsModifier.template = xml`<Tab t-if="Object.keys(tabs).length" onChangedTab="props.bindSort" options="tabs" />`;
ComponentTabsModifier.components = {Tab};


export class ComponentModifier extends Component {
    setup() {
        super.setup();
        const {viewInfo, setComponent} = this.props, {archJson} = viewInfo;
        this.nodes = {};
        this.state = useState({node: archJson});
        this.setNodeId(archJson);
        studioListener("MODIFIER:PATCHED", () => {
            this.setElToNode();
            this.bindAction();
            this.bindStyle();
        });
        onWillUpdateProps((nextProps) => {
            const {archJson} = nextProps.viewInfo;
            this.setNodeId(archJson);
            const currentNode = this.findNode(archJson, (node) => node.nodeId == this.state.node.nodeId);
            this.state.node = currentNode ? currentNode : archJson;
        });
        useEffect(() => {
            this.setElToNode();
            this.bindAction();
            this.bindStyle();
        });
        this.actionService = useService("action");
        if (setComponent) setComponent(this);
    }

    get nodeModifier() {
        return new this.constructor.NodeModifier(this.state.node, {
            viewInfo: this.props.viewInfo, app: this.__owl__.app, onNodeChangeProp: this.onChangeProp.bind(this)
        });
    }

    get componentProps() {
        const props = {};
        return props;
    }

    get structureNode() {
        return this.props.viewInfo.archJson;
    }

    get structureNodeProps() {
        return {
            onChangeNode: (node) => this.state.node = node,
            structureNode: this.structureNode,
            nodeModifier: this.constructor.NodeModifier,
            viewInfo: this.props.viewInfo,
            reload: this.onChangeProp.bind(this),
            node: this.state.node,
        }
    }

    get viewComponentProps() {
        const props = {viewInfo: this.props.viewInfo};

        if (!this.constructor.ViewComponent) {
            props.classes = this.constructor.classes;
            props.parent = this.props.parent;
            props.componentProps = this.componentProps;
            props.editMode = true;
        }
        return props;
    }

    getEl(node) {
        return $(document).find("[node-id='" + node.nodeId + "']");
    }


    getNode(nodeId) {
        if ((typeof nodeId == "string") && (nodeId.indexOf("nodeId_") >= 0)) {
            return this.nodes[nodeId];
        }
        return nodeId;
    }

    createNewNode() {
    }

    setElToNode() {
        Object.values(this.nodes).map((node) => {
            node.el = this.getEl(node);
        });
    }

    get nodeParams() {
        return {
            findNode: this.findNode.bind(this),
            copyNode: this.onCopyNode.bind(this),
            xpathNode: this.onXpathNode.bind(this),
            removeNode: this.onRemoveNode.bind(this),
            setNodeId: this.setNodeId.bind(this)
        }
    }

    get attrsRemove() {
        return ["modifiers"]
    }

    setNodeId(node) {
        if (!node?.tag) {
            return;
        }
        let nodeId = node.nodeId || (node.attrs || {})['node-id'] || NodeID();
        if (typeof node == 'object') {
            node.nodeId = nodeId;
            node.attrs['node-id'] = nodeId;
            node.params = this.nodeParams;
            if (!node.parentNode && node.parentId) {
                node.parentNode = this.nodes[node.parentId];
            }
            (node.children || []).map((child) => {
                if (typeof child == 'object') {
                    child.parentId = nodeId;
                    child.parentNode = node;
                    this.setNodeId(child);
                }
            });
            this.nodes[nodeId] = node;
        }
    }

    cleanArchJson() {
        const {viewInfo} = this.props, {archJson} = viewInfo;
        const loop = (nodes) => {
            nodes.map((node) => {
                if (node.attrs) this.attrsRemove.map((attr) => {
                    delete toRaw(node).attrs[attr];
                });
                loop(node.children || []);
            });
        }
        loop([archJson]);
    }

    prepareDataToSave() {
        this.cleanArchJson();
        const {archJson} = this.props.viewInfo;
        return {arch: jsonNodeToString(archJson)};
    }

    onChangeProp(prop, value) {
        this.render(true);
    }

    onDuplicateNode(node) {
        this.onXpathNode(node, [this.onCopyNode(node)], "after");
    }

    onCopyNode(node) {
        node = this.getNode(node);
        const newNodes = [];
        const copyNode = (nodes, wrap = []) => {
            nodes.map((child) => {
                let _newNode = child;
                if (child.tag) {
                    _newNode = {...child, children: []};
                    delete _newNode.el;
                    delete _newNode.nodeId;
                    delete _newNode.parentNode;
                    _newNode = $.extend(true, {}, _newNode);
                    delete _newNode.attrs['node-id'];
                }
                wrap.push(_newNode);
                copyNode(child.children || [], _newNode.children || []);
            });
        }
        copyNode([node], newNodes);
        if (newNodes.length) {
            this.setNodeId(newNodes[0]);
            return newNodes[0];
        }
        return false;
    }

    findNode(wrap_node, condition = (node) => {
    }) {
        wrap_node = wrap_node || this.props.viewInfo.archJson;
        let found = false;
        const loop = (nodes) => {
            for (let i = 0; i < nodes.length; i++) {
                const node = nodes[i];
                if (condition(node)) {
                    found = node;
                    break;
                }
                loop(node.children || []);
                if (found) break;
            }
        }
        loop([wrap_node]);
        return found;
    }

    onRemoveNode(node, showParent = true) {
        node = this.getNode(node);
        if (typeof node == "object") {
            const parentNode = this.getNode(node.parentId),
                idxRemove = parentNode.children.findIndex((ch) => ch.nodeId == node.nodeId);
            if (idxRemove >= 0) {
                parentNode.children.splice(idxRemove, 1);
            }
        }
        if (showParent) this.state.node = this.nodes[node.parentId];
    }

    onXpathNode(node, nodeMoves, position = "after", deleteMove = false, resetNode = true) {
        node = this.getNode(node);
        nodeMoves = nodeMoves.map((nodeMove) => {
            nodeMove = this.getNode(nodeMove);
            if (!nodeMove.nodeId) {
                this.setNodeId(nodeMove);
            }
            if (deleteMove) {
                this.onRemoveNode(nodeMove, false);
            }
            return nodeMove;
        });
        const {parentId, nodeId} = node, parentNode = this.getNode(parentId);
        const nodeIdx = parentNode?.children.findIndex((ch) => ch.nodeId == nodeId);
        const setParentId = (nodes, parentId) => {
            nodes.map((nMove) => {
                nMove.parentId = parentId;
            });
        }
        const xpathWithPos = {
            after: () => {
                parentNode.children.splice((nodeIdx + 1), 0, ...nodeMoves);
                setParentId(nodeMoves, parentNode.nodeId);
            }, before: () => {
                parentNode.children.splice((nodeIdx), 0, ...nodeMoves);
                setParentId(nodeMoves, parentNode.nodeId);
            }, append: () => {
                node.children.push(...nodeMoves);
                setParentId(nodeMoves, node.nodeId);
            }
        };
        if (resetNode) this.state.node = nodeMoves[0];
        xpathWithPos[position]();
    }

    onClickNode(e) {
        // e.preventDefault();
        e.stopPropagation();
        e.stopImmediatePropagation();
        const el = $(e.currentTarget), nodeId = el.closest("[node-id]").attr("node-id");
        el.addClass("node-active");
        if (nodeId in this.nodes) {
            this.state.node = this.nodes[nodeId];
        }
    }

    stopSort(nodeMove, params = {}, isNew = false) {
        const {nodeXpath, position} = params;
        if (isNew) {
            this.setNodeId(nodeMove);
        }
        this.onXpathNode(nodeXpath, Array.isArray(nodeMove) ? nodeMove : [nodeMove], position, !isNew);
        this.render(true);
    }

    bindSort() {
        useSortService($(this.__owl__.bdom.el), {
            stopSort: this.stopSort.bind(this), env: this.env, modifier: this, viewInfo: this.props.viewInfo
        });
    }

    bindStyle() {
        const {node} = this.state, clActive = "node-active";
        this.$parentEl.find("." + clActive).removeClass(clActive)
        this.$parentEl.find("[node-id='" + node.nodeId + "']").addClass(clActive);
    }

    bindAction() {
        this.$el = $(this.__owl__.bdom?.el);
        this.$parentEl = $(this.__owl__.bdom.parentEl);
        this.$el.find(".component_viewer.SORT_COMPONENT").data("component", this);
        this.$parentEl.find("[node-id]").click(this.onClickNode.bind(this));
        this.bindSort();
    }
}

ComponentModifier.showNodeRoot = true;
ComponentModifier.NodeModifier = NodeModifier;
ComponentModifier.template = "dynamic_odoo.Modifier.ComponentModifier";
ComponentModifier.components = {StructureNode: StructureNode, Field: Field, ViewComponent: ViewComponent}

export class ComponentModifierDialog extends Component {
    setup() {
        this.Modifier = ComponentModifier;
        this.state = useState({key: this.key});
        useSubEnv({
            debug: false,
        });
    }

    get key() {
        return `modifier_${floorRandom()}`;
    }

    reset() {
        const {reset} = this.props;
        if (reset) reset();
        this.state.key = this.key;
    }

    confirm() {
        const {confirm} = this.props;
        if (confirm) confirm();
        this.state.key = this.key;
        // this.props.close();
    }
}

ComponentModifierDialog.template = "dynamic_odoo.ModifierDialog";
ComponentModifierDialog.components = {Dialog};
