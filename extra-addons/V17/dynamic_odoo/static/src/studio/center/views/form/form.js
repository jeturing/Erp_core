/** @odoo-module **/

import {registry} from "@web/core/registry";
import {NodeModifier, ComponentTabsModifier, FIELD_ICONS} from "../../modifier"
import {ViewComponentModifier} from "../view_modifier";
import {DRAG_COMPONENTS} from "./drag_component";
import {Approval} from "./button_approval/button_approval";
import {dispatchEvent} from "@dynamic_odoo/core/studio_core";
import {xmlToJson} from "@dynamic_odoo/core/utils/view";
import {evaluateExpr, evaluateBooleanExpr} from "@web/core/py_js/py";
import {ButtonCodeEditor} from "./button_code_editor/button_code_editor";
import {SelectionOptions} from "@dynamic_odoo/core/fields/options_center/options_center";
import {DefaultFieldValue} from "./components/default_field_value/default_field_value";
import {floorRandom} from "@dynamic_odoo/core/utils/format";

const {Component, toRaw, useEffect} = owl;
const modifierRegistry = registry.category("modifier_views");


class ExtendNodeModifier extends NodeModifier {
}

const BUTTON_KEY = (node) => {
    return `btn_studio_${floorRandom()}`
}
const getContext = (node) => {
    return evaluateExpr(node.attrs.context || '{}');
}
const setContext = (node, callback = (_context) => {
}) => {
    const context = getContext(node);
    callback(context);
    node.attrs.context = JSON.stringify(context);
    return context;
}
const superString = NodeModifier.nodeProps.string;
const PROPS = {
    string: {
        ...superString, modifierProps: {
            ...superString.modifierProps,
            onChange: (node, prop, value, params) => {
                superString.modifierProps.onChange(node, prop, value);
                if (node.tag == "field") {
                    const {fields} = params.self.params.viewInfo, fieldName = node.attrs.name,
                        field = fields[fieldName];
                    if (field.isNew) {
                        dispatchEvent("STUDIO_FORM:NEW_FIELD", {
                            field: {name: fieldName, string: node.attrs.string}, type: "update"
                        }, node.el[0]);
                    }
                }
            }
        }
    },
    nolabel: {
        type: Boolean, optional: true, modifierProps: {
            widget: "toggle_switch",
            onChange: (node, prop, value, params = {}) => {
                value ? (node.attrs.nolabel = '1') : (delete node.attrs.nolabel)
            }
        }
    },
    use_label: {
        type: Boolean, optional: true, modifierProps: {
            widget: "toggle_switch", label: "Use label", widgetProps: (self, node) => {
                const props = {}, fieldName = node.attrs.name, children = node.parentNode.children;
                const index = children.findIndex((_node) => _node.tag && _node.nodeId == node.nodeId);
                let label = children[index - 1] || children[index - 1], studio_label_for = label?.nodeId;
                if (label) {
                    if (label.attrs.class?.includes("o_td_label")) {
                        const foundNode = label.children.filter((_node) => _node.tag == "label" && _node.attrs.for == fieldName);
                        if (foundNode.length) {
                            label = foundNode[0];
                        }
                    }
                    if (label.tag == "label" && label.attrs.for == fieldName) {
                        props.value = true;
                        node.attrs.studio_label_for = studio_label_for;
                    }
                }
                return props;
            }, onChange: (node, prop, value, params = {}) => {
                if (value) {
                    const tdLabel = {
                        attrs: {class: "o_td_label"},
                        children: [{attrs: {for: node.attrs.name}, children: [], tag: "label"}],
                        parentId: node.parentNode.nodeId,
                        tag: "td"
                    };
                    node.attrs.nolabel = '1';
                    node.params.setNodeId(tdLabel);
                    node.params.xpathNode(node, [tdLabel], "before", false, false)
                } else {
                    const nodeId = node.attrs.studio_label_for;
                    if (nodeId) {
                        node.params.removeNode(nodeId);
                        delete node.attrs.nolabel;
                        delete node.attrs.studio_label_for;
                    }
                }
            }
        }
    },
    use_chatter_widget: {
        type: Boolean, optional: true, modifierProps: {
            widget: "toggle_switch", label: "Use Chatter Widget", widgetProps: (self, node) => {
                const chatter = node.params.findNode(false, (node) => (node.attrs || {}).class == "oe_chatter");
                return {value: chatter.hasOwnProperty("tag")};
            }, onChange: (node, prop, value, params = {}) => {
                if (value) {
                    const {app} = params.self.params, parser = new DOMParser();
                    const chatter = xmlToJson(parser.parseFromString(app.rawTemplates['dynamic_odoo.Form.Chatter'].innerHTML, "text/xml"));
                    chatter.parentId = node.nodeId;
                    node.children.push(chatter);
                } else {
                    const nodeRemove = node.params.findNode(false, (node) => (node.attrs || {}).class == "oe_chatter");
                    if (nodeRemove) node.params.removeNode(nodeRemove);
                }
                node.attrs.chatter = value;
            }
        }
    },
    use_button_box: {
        type: Boolean, optional: true, modifierProps: {
            widget: "toggle_switch", label: "Use Button Box", widgetProps: (self, node) => {
                const buttonBox = node.params.findNode(false, (node) => (node.attrs || {}).name == "button_box");
                return {value: buttonBox.hasOwnProperty("tag")};
            }, onChange: (node, prop, value) => {
                if (value) {
                    const sheet = node.params.findNode(false, (node) => node.tag == "sheet");
                    if (sheet) {
                        const buttonBox = {
                            attrs: {class: "oe_button_box", name: "button_box"}, children: [], tag: "div"
                        }
                        sheet.children.splice(0, 0, buttonBox);
                    }
                } else {
                    const nodeRemove = node.params.findNode(false, (node) => (node.attrs || {}).name == "button_box");
                    if (nodeRemove) node.params.removeNode(nodeRemove);
                }
            }
        }
    }, can_create: {
        type: Boolean, optional: true, modifierProps: {
            widget: "radio", label: "Can Create", widgetProps: (self, node) => {
                const {can_create, options} = node.attrs, _options = evaluateExpr(options || '{}');
                return {value: _options.no_create ? !_options.no_create : can_create ? evaluateBooleanExpr(can_create) : true};
            }, onChange: (node, prop, value) => {
                const options = evaluateExpr(node.attrs.options || "{}");
                options.no_create = !value;
                node.attrs.options = JSON.stringify(options);
            }
        },
    },
    currency_field: {
        type: String, optional: true, modifierProps: {
            widget: "many2one", widgetProps: (self, node) => {
                const {fields, model} = self.params.viewInfo, field = fields[node.attrs.name];
                const model_id = odoo.studio.models.filter((dataModel) => dataModel.model == model)[0].id;
                const props = {
                    relation: "ir.model.fields",
                    domain: [['model', '=', model], ['ttype', '=', 'many2one'], ['relation', '=', 'res.currency']],
                    value_name: "name",
                    context: {
                        default_model_id: model_id,
                        default_field_description: "Currency Field",
                        default_ttype: "many2one",
                        default_relation: "res.currency"
                    },
                };
                if (field.currency_field) {
                    props.value = node.attrs.currency_field || field.currency_field;
                }
                return props;
            }, onChange: (node, prop, value) => {
                node.attrs.currency_field = value;
                dispatchEvent("STUDIO_FORM:UPDATE_FIELD", {
                    fieldName: node.attrs.name, data: {currency_field: value}
                }, node.el[0]);
            }
        }
    },
    clickable: {
        type: Boolean, optional: true, modifierProps: {
            widget: "toggle_switch",
            widgetProps: (self, node) => {
                const options = evaluateExpr(node.attrs.options || '{}');
                return {value: ['1'].includes(options.clickable)}
            }, onChange: (node, prop, value) => {
                const options = evaluateExpr(node.attrs.options || "{}");
                value ? (options.clickable = '1') : (delete options.clickable);
                Object.keys(options).length ? (node.attrs.options = JSON.stringify(options)) : (delete node.attrs.options);
            }
        }
    },
    default_value: {
        type: Boolean, optional: true, modifierProps: {
            component: DefaultFieldValue, widgetProps: (self, node) => {
                const {fields, model} = self.params.viewInfo, field = fields[node.attrs.name];
                return {field: field, model: model, value: node.attrs.studio_default, name: node.attrs.name}
            }, onChange: (node, props, value) => {
                node.attrs.studio_default = value;
                dispatchEvent("STUDIO_FORM:DEFAULT_VALUE", {
                    fieldName: node.attrs.name, defaultValue: value
                }, node.el[0]);
            }
        }
    },
    can_write: {
        type: Boolean, optional: true, modifierProps: {
            widget: "radio", label: "Can Write",
        },
    }, no_open: {
        type: Boolean, optional: true, modifierProps: {
            widget: "radio", label: "Can Open", widgetProps: (self, node) => {
                const options = evaluateExpr(node.attrs.options || '{}');
                return {value: !options.no_open};
            }, onChange: (node, prop, value) => {
                const options = evaluateExpr(node.attrs.options || "{}");
                options.no_open = !value;
                node.attrs.options = JSON.stringify(options);
            }
        },
    }, field_name: {
        type: String, optional: true, modifierProps: {
            widgetProps: (self, node) => {
                return {value: node.attrs.name}
            }, onChange: (node, prop, value, params = {}) => {
                const {fields} = params.self.params.viewInfo, oldName = node.attrs.name, field = fields[oldName];
                if (fields[value]) {
                    alert("This name already exist !");
                } else if (field.isNew && value.substring(0, 2) == "x_") {
                    node.attrs.name = value;
                    dispatchEvent("STUDIO_FORM:UPDATE_FIELD_NAME", {
                        oldName: oldName, newName: value
                    }, node.el[0]);
                }
            }
        }
    },
    no_quick_create: {
        type: Boolean, optional: true, modifierProps: {
            widget: "radio", label: "Quick Create", widgetProps: (self, node) => {
                const options = evaluateExpr(node.attrs.options || '{}');
                return {value: !options.no_quick_create};
            }, onChange: (node, prop, value) => {
                const options = evaluateExpr(node.attrs.options || '{}');
                options.no_quick_create = !value;
                node.attrs.options = JSON.stringify(options);
            }
        },
    }, btn_set_approval: {
        type: Boolean, optional: true, modifierProps: {
            widget: "toggle_switch", label: "Set Approval", widgetProps: (self, node) => {
                return {value: node.attrs.use_approval || false};
            }, onChange: (node, prop, value) => {
                setContext(node, (context) => {
                    context.btn_key = context.btn_key || BUTTON_KEY();
                });
                value ? (node.attrs.use_approval = true) : (delete node.attrs.use_approval);
            }
        },
    }, btn_active_confirm: {
        type: Boolean, optional: true, modifierProps: {
            widget: "toggle_switch", label: "Active confirm", widgetProps: (self, node) => {
                return {value: node.attrs.hasOwnProperty("confirm")};
            }, onChange: (node, prop, value) => {
                value ? (node.attrs.confirm = "") : (delete node.attrs.confirm);
            }
        },
    }, confirm: {
        type: String, optional: true, noLabel: true, modifierProps: {
            widget: "html",
        }
    }, btn_object_name: {
        type: String, optional: true, modifierProps: {
            label: "Method to run",
            widgetProps: (self, node) => ({value: node.attrs.name}),
            onChange: (node, prop, value) => {
                node.attrs.name = value;
            }
        }
    }, btn_action_name: {
        type: String, optional: true, modifierProps: {
            label: "Action to run", widget: "many2one", widgetProps: (self, node) => {
                let name = node.attrs.name;
                if (name && name.indexOf("(") >= 0) {
                    name = name.split("(")[1].split(")")[0]
                }
                return {relation: "ir.actions.act_window", value_name: "xml_id", value: name};
            }, onChange: (node, prop, value) => {
                node.attrs.name = `%(${value})d`;
            }
        }
    }, btn_fnc_custom: {
        type: String, optional: true, modifierProps: {
            label: "Custom action to run", widget: "many2one", widgetProps: (self, node) => {
                const {models} = odoo.studio || {},
                    model = node.attrs.model || (odoo.studio && odoo.studio.getState().model),
                    model_id = odoo.studio.models.filter((dataModel) => dataModel.model == model)[0].id;
                const props = {
                    relation: "base.automation",
                    value_name: "id",
                    canOpen: true,
                    openTarget: "new",
                    string: "Custom Action",
                    context: {default_model_id: model_id, default_trigger: "button_action"},
                    value: getContext(node).automation_id,
                }

                if (models) {
                    const _model = models.filter((record) => record.model == model);
                    if (_model.length) props.domain = [['model_id', '=', _model[0].id]];
                }
                return props;
            }, onChange: (node, prop, value) => {
                setContext(node, (context) => {
                    context.automation_id = value;
                    context.btn_key = context.btn_key || BUTTON_KEY();
                    context.btn_type = "automation";
                });
            }
        }
    }, btn_type: {
        type: String, optional: true, modifierProps: {
            widget: "selection", label: "Action Type", widgetProps: (self, node) => {
                return {
                    value: node.attrs.studio_type || node.attrs.type || "custom",
                    options: [['custom', 'Custom a action'], ['object', 'Call a method'], ['action', 'Run a server action'], ['python', 'Use a Python code']]
                };
            }, onChange: (node, prop, value = {}) => {
                const CUSTOM_FNC_NAME = "studio_action_button";
                const {name, type, original_type, original_name} = node.attrs;
                if (!original_type && type) {
                    node.attrs.original_type = type;
                }
                if (!original_name && name) {
                    node.attrs.original_name = name;
                }
                node.attrs.studio_type = value;
                node.attrs.type = ["custom", "python"].includes(value) ? "object" : value;
                ["custom", "python"].includes(value) ? (node.attrs.name = CUSTOM_FNC_NAME) : (delete node.attrs.name);
            }
        }
    },
    btn_code_editor: {
        type: String, optional: true, modifierProps: {
            label: "Action Code Editor",
            component: ButtonCodeEditor,
            widgetProps: (self, node) => {
                return {btn_key: getContext(node).btn_key};
            },
            onChange: (node, prop, value) => {
                const context = setContext(node, (_context) => {
                    _context.btn_key = _context.btn_key || BUTTON_KEY();
                    _context.btn_type = "python";
                });
                dispatchEvent("STUDIO_FORM:UPDATE_BUTTON", {...value, btn_key: context.btn_key}, node.el[0]);
            }
        }
    },
    btn_approval: {
        type: String, optional: true, modifierProps: {
            component: Approval, widgetProps: (self, node) => {
                return {
                    model: self.params.viewInfo.model,
                    key: getContext(node).btn_key,
                    btn_string: node.attrs.string || node.children.filter((child) => typeof child == "string").join(" ")
                }
            }, onChange: (node, prop, value) => {
                node.attrs.rules_size = value;
            }
        }
    }, icon: {
        ...NodeModifier.nodeProps?.icon, modifierProps: {
            widget: "choose_icon", onChange: (node, prop, value) => {
                node.attrs.icon = "fa-" + value;
            }
        }
    }, relation: {
        ...NodeModifier.nodeProps.relation, modifierProps: {
            ...NodeModifier.nodeProps.relation.modifierProps, onChange: (node, prop, value) => {
                node.attrs.relation = value;
                dispatchEvent("STUDIO_FORM:NEW_FIELD", {
                    field: {name: node.attrs.name, relation: value}, type: "update"
                }, node.el[0]);
            }
        }
    }, selection: {
        type: String, optional: true, modifierProps: {
            component: SelectionOptions, widgetProps: (self, node) => {
                const {fields} = self.params.viewInfo, field = fields[node.attrs.name];
                const options = field.selection || node.attrs.selection || [];
                const statusbarVisible = (node.attrs.statusbar_visible || "").trim().split(",");
                const props = {canCreate: field.isNew || false};
                // only use for statusbar widget
                if (node.attrs.widget == "statusbar") {
                    props.usePicked = true;
                }
                props.options = options.map((option) => {
                    const newOption = {name: option[0], string: option[1]};
                    if (statusbarVisible.includes(newOption.name)) {
                        newOption.picked = true;
                    }
                    return newOption;
                });
                return props;
            },
            onChange: (node, prop, value, params) => {
                const options = [], statusbarVisible = [];
                const {fields} = params.self.params.viewInfo, field = fields[node.attrs.name];
                value.map((option) => {
                    options.push([option.name, option.string]);
                    if (option.picked) statusbarVisible.push(option.name);
                });
                if (field.isNew) {
                    node.attrs.selection = options;
                    dispatchEvent("STUDIO_FORM:NEW_FIELD", {
                        field: {name: node.attrs.name, selection: options}, type: "update"
                    }, node.el[0]);
                }
                if (statusbarVisible.length) {
                    node.attrs.statusbar_visible = statusbarVisible.join(",");
                }
            },
        }
    }, relation_field: {
        type: String, optional: true, modifierProps: {
            widget: "many2one", widgetProps: (self, node) => {
                const {fields, model} = self.params.viewInfo, field = fields[node.attrs.name];
                const model_id = odoo.studio.models.filter((dataModel) => dataModel.model == field.relation)[0].id;
                const props = {
                    relation: "ir.model.fields",
                    domain: [['model', '=', field.relation], ['ttype', '=', 'many2one'], ['relation', '=', model]],
                    value_name: "name",
                    context: {
                        default_model_id: model_id,
                        default_field_description: "Field Relation",
                        default_ttype: "many2one",
                        default_relation: model
                    },
                };

                if (field.relation_field) {
                    props.value = field.relation_field;
                }
                return props;
            }, onChange: (node, prop, value, params) => {
                const {fields} = params.self.params.viewInfo, fieldName = node.attrs.name;
                const field = fields[fieldName];
                field.relation_field = value;
            }
        }
    }, choose_stat_field: {
        type: String, optional: true, modifierProps: {
            widget: "many2one", widgetProps: (self, node) => {
                const {model} = self.params.viewInfo;
                const props = {
                    relation: "ir.model.fields",
                    domain: [['relation', '=', model], ['store', '=', true]],
                    specific_list: ["model", "name"],
                    value_name: "name"
                };
                (node.children || []).map((child) => {
                    if (child.tag == "field") {
                        const fieldName = child.attrs.name;
                        if (fieldName.includes("x_field_")) {
                            props.value = fieldName.substring(8, fieldName.indexOf("_count_"));
                        }
                    }
                });
                return props;
            }, onChange: (node, prop, value, params) => {
                const fieldName = `x_field_${value.name}_count_${floorRandom()}`,
                    actionName = `act_${fieldName}`
                const stat_field = {
                    name: fieldName,
                    action_name: actionName,
                    compute: true,
                    model: value.model,
                    relation_field: value.name,
                    type: "integer",
                    string: node.attrs.string,
                    widget: "statinfo"
                }
                const stat_node_field = {
                    tag: "field",
                    attrs: {name: stat_field.name, string: stat_field.string, widget: stat_field.widget},
                    children: []
                };
                if (node.children) node.children = [];
                node.attrs.name = actionName;
                node.children.push(stat_node_field);
                dispatchEvent("STUDIO_FORM:NEW_FIELD", {
                    field: stat_field
                }, node.el[0]);
            }
        }
    }, group_columns: {
        ...NodeModifier.nodeProps.columns,
        modifierProps: {...NodeModifier.nodeProps.columns.modifierProps, label: "Columns"}
    }, col_space: {
        type: String, optional: true, modifierProps: {
            onChange: (node, prop, value) => {
                node.attrs.col = value;
            }, widgetProps: (self, node) => {
                return {value: node.attrs.col || node.children.length}
            }
        }
    }, colspan: {
        type: String, optional: true, modifierProps: {
            onChange: (node, prop, value) => {
                node.attrs.colspan = value;
            }, widgetProps: (self, node) => {
                return {value: node.attrs.colspan}
            }
        }
    },
    select_avatar: {
        type: String, optional: true, modifierProps: {
            widget: "many2one", label: "Use Exist Field", widgetProps: (self, node) => {
                const {model} = self.params.viewInfo;
                const props = {
                    relation: "ir.model.fields",
                    domain: [['model', '=', model], ['ttype', '=', 'binary']],
                    value_name: "name"
                };
                return props;
            }, onChange: (node, prop, value) => {
                const sheetNode = node.params.findNode(false, (_node) => _node.tag == "sheet");
                if (sheetNode) {
                    const firstNode = sheetNode.children[0];
                    const fieldNode = {
                        attrs: {name: value, class: "oe_avatar", widget: "image"},
                        parentId: firstNode.nodeId,
                        tag: "field"
                    }
                    node.params.xpathNode(firstNode, [fieldNode], "before", false, true);
                }
            }
        }
    },
    use_new_field: {
        type: Boolean, optional: true, modifierProps: {
            widget: "toggle_switch",
            onChange: (node, prop, value, params) => {
                const {model} = params.self.params.viewInfo;
                const sheetNode = node.params.findNode(false, (_node) => _node.tag == "sheet");
                if (value) {
                    const firstNode = sheetNode.children[0];
                    const field = {
                        name: `x_field_${floorRandom()}`,
                        model: model,
                        type: "binary",
                        string: "New Avatar",
                    }
                    const fieldNode = {
                        attrs: {name: field.name, class: "oe_avatar", widget: "image"},
                        parentId: firstNode.nodeId,
                        tag: "field",
                    };
                    node.params.xpathNode(firstNode, [fieldNode], "before", false, true);
                    dispatchEvent("STUDIO_FORM:NEW_FIELD", {
                        field: field
                    }, sheetNode.el[0]);
                }
            }
        }
    }
}

ExtendNodeModifier.nodeProps = {
    ...NodeModifier.nodeProps, ...PROPS
}

ExtendNodeModifier.nodeViewStore = [...NodeModifier.nodeViewStore, ["[button]", (node) => {
    const isStatButton = (node.attrs.class || "").includes("oe_stat_button");
    let view = ["invisible", "string", "choose_stat_field", "groups", "icon", "css", "more"];
    if (isStatButton) {
        return view;
    }
    let _view_action = "btn_fnc_custom", offset = 0;
    view = ["invisible", "btn_set_approval", "btn_active_confirm", "btn_type", "string", "groups", "icon", "css", "more"];
    const btnType = node.attrs.studio_type || node.attrs.type;
    switch (btnType) {
        case "object":
            _view_action = "btn_object_name";
            break;
        case "action":
            _view_action = "btn_action_name";
            break;
        case "python":
            _view_action = "btn_code_editor";
            break;
    }
    view.splice(4, 0, _view_action);
    if (node.attrs.use_approval) {
        view.splice(2, 0, "btn_approval");
        offset += 1;
    }
    if (node.attrs.hasOwnProperty("confirm")) {
        view.splice(3 + offset, 0, "confirm")
    }
    return view;
}], ["[field]", (node, viewInfo) => {
    const superViewField = NodeModifier.nodeViewStore.filter((view) => view[0] == "[field]")[0];
    const fieldView = [...superViewField[1]];
    const field = viewInfo.fields[node.attrs.name];
    if (!field) {
        return [];
    }
    fieldView.splice(3, 0, ...["use_label"]);
    if (field.isNew) {
        fieldView.splice(5, 0, "field_name");
    } else {
        fieldView.splice(5, 0, "default_value");
    }
    if (field.related) {
        fieldView.splice(5, 0, "related");
        return fieldView;
    }
    if (["many2one", "many2many", "one2many"].includes(field.type)) {
        fieldView.splice(5, 0, "relation");
    }
    if (["many2one"].includes(field.type)) {
        fieldView.splice(fieldView.length - 1, 0, ...["can_create", "can_write", "no_open", "no_quick_create"])
    } else if (field.type == "one2many" && field.relation) {
        fieldView.splice(6, 0, "relation_field");
    } else if (field.type == "selection") {
        fieldView.splice(5, 0, "selection");
        if (node.attrs.widget == "statusbar") {
            fieldView.splice(3, 0, "clickable");
        }
    } else if (field.type == "monetary") {
        fieldView.splice(6, 0, "currency_field");
    }

    return fieldView;
}], ["[picture]", ["use_new_field", "select_avatar"]], ["[group]", (node, viewInfo) => {
    const groupView = ["col_space", "colspan", "group_columns", "string", "groups", "more"];
    if (node?.parentNode?.tag == "group") {
        groupView.splice(4, 1);
    }
    return groupView;
}], ["[header], [sheet]", ["more", "css"]], ["[page]", ["invisible", "string", "groups", "more"]], ["[notebook]", ["invisible", "groups", "more"]], ["[form]", ["create", "edit", "delete", "show_all_invisible", "use_button_box", "use_chatter_widget"]],]

ExtendNodeModifier.ShowNodeRoot = false;

class TabComponents extends Component {

    get fieldsSupported() {
        const fieldsSupported = {
            datetime: {title: "Datetime"},
            date: {title: "Date"},
            char: {title: "Char"},
            text: {title: "Text"},
            many2one: {
                title: "Many2one", props: {relation: (odoo.studio && odoo.studio.getState().model)}
            },
            one2many: {title: "One2many"},
            many2many: {title: "Many2many"},
            many2many_tags: {
                type: "many2many", title: "Many2many Tags", props: {widget: "form.many2many_tags"}
            },
            integer: {title: "Integer"},
            monetary: {title: "Monetary", props: {store: true}},
            float: {title: "Float"},
            binary: {title: "File"},
            signature: {type: 'binary', title: "Signature", props: {widget: "signature"}},
            image: {type: 'binary', title: "Image", props: {widget: "image"}},
            related: {title: "Related", props: {related: "create_uid.id", type: "integer"}},
            selection: {title: "Selection", props: {selection: [['option_1', 'Option 1']]}},
            statusbar: {
                type: "selection", title: "Statusbar", props: {widget: "statusbar", selection: [['draft', 'Draft']]}
            },
            boolean: {title: "Boolean"},
            html: {title: "HTML"},
        }
        Object.keys(fieldsSupported).map((fieldType) => {
            if (fieldType in FIELD_ICONS) {
                fieldsSupported[fieldType].icon = FIELD_ICONS[fieldType];
            }
        })
        return fieldsSupported;
    }
}

TabComponents.template = "dynamic_odoo.form.TabComponents";
TabComponents.components = {...DRAG_COMPONENTS};

class ExtendTabsModifier extends ComponentTabsModifier {
    get tabComponent() {
        return {name: "components", data: {label: "Components", content: [{component: TabComponents}]}}
    }

    get tabs() {
        const tabField = this.tabField, tabView = this.tabView, tabComponents = this.tabComponent;
        return {
            [tabView.name]: tabView.data, [tabField.name]: tabField.data, [tabComponents.name]: tabComponents.data,
        }
    }
}


export class FormModifier extends ViewComponentModifier {
    setup() {
        super.setup();
        this.new_fields = {};
        this.update_fields = {};
        this.button_store = {};
        this.approval_store = {};
        this.default_store = {};
        useEffect(() => {
            this.removeEvents();
            this.loadEvents();
            return () => this.removeEvents.bind(this)()
        });
    }

    removeEvents() {
        (this.prevEvents || []).map((event) => {
            event[0].removeEventListener(event[1], event[2]);
        });
    }

    loadEvents() {
        const el = this.__owl__.bdom.el, events = [];
        events.push(["STUDIO_FORM:UPDATE_BUTTON", (params) => {
            const {btn_key} = (params.detail || {});
            this.button_store[btn_key] = {...(this.button_store[btn_key] || {}), ...(params.detail || {})};
        }]);
        events.push(["MODIFIER:NOTEBOOK:ADD_PAGE", (params) => {
            const xpath = (params.detail || {}).xpath;
            this.addNewPage(xpath);
        }]);
        events.push(["STUDIO_FORM:APPROVAL_UPDATE", (params) => {
            const approval = (params.detail || {}).approval || false;
            if (approval) this.approval_store[approval.key] = {btn_string: approval.btn_string, rules: approval.rules};
        }]);
        events.push(["STUDIO_FORM:DEFAULT_VALUE", (params) => {
            const {fieldName, defaultValue} = (params.detail || {});
            this.default_store[fieldName] = defaultValue;
        }]);
        events.push(["STUDIO_FORM:NEW_FIELD", (params) => {
            const {field, type} = (params.detail || {});
            if (field) this.doNewField(field, type);
        }]);
        events.push(["STUDIO_FORM:UPDATE_FIELD", (params) => {
            const {fieldName, data} = (params.detail || {});
            this.updateField(fieldName, data);
        }])
        events.push(["STUDIO_FORM:UPDATE_FIELD_NAME", (params) => {
            const {oldName, newName} = (params.detail || {});
            this.updateFieldName(oldName, newName);
        }])
        events.push(["MODIFIER:BIND_SORT", () => {
            this.bindSort();
        }]);
        events.push(["MODIFIER:BUTTON_BOX:ADD_BUTTON", () => {
            this.onNewButtonBox();
        }]);
        events.push(["STUDIO_FORM:LOAD_SUBVIEW", (params) => {
            const {viewInfo, nodeId} = params.detail;
            this.prepareSubView(nodeId, viewInfo);
            dispatchEvent("VIEW_CENTER:SUBVIEW_TO_STACK", {...params.detail});
        }]);
        this.prevEvents = [];
        events.map((event) => {
            el.addEventListener([event[0]], event[1]);
            this.prevEvents.push([el, ...event]);
        });
    }

    prepareSubView(nodeId, subViewInfo) {
        const {viewType} = subViewInfo;
        const realNode = this.findNode(false, (node) => node.nodeId == nodeId);
        const viewIndex = realNode.children.findIndex((child) => child.tag == (viewType == "list" ? "tree" : viewType))
        const foundView = realNode.children[viewIndex];
        subViewInfo.store = true;
        subViewInfo.isSubView = true;
        if (foundView) {
            subViewInfo.store = false;
            // use for subView on parentView.
            subViewInfo.patchNode = () => {
                toRaw(realNode).children.splice(viewIndex, 1, subViewInfo.archJson);
            }
        }
        subViewInfo.loadViewRef = (key) => {
            let context = (realNode.attrs.context || '{}').trim();
            const viewKey = 'odoo_studio.' + key, exactType = viewType == "list" ? "tree" : viewType;
            if (!context.includes(viewKey)) {
                let viewRef = `${exactType}_view_ref`, inContext = false;
                const newContext = context.substring(1, context.length - 1).split(",").map((option) => {
                    option = option.split(":");
                    if (option[0].includes(viewRef)) {
                        inContext = true;
                        option[1] = `'${viewKey}'`;
                    }
                    return option.join(":");
                });
                if (!inContext) {
                    newContext.splice(1, 0, `'${viewRef}': '${viewKey}'`)
                }
                realNode.attrs.context = ["{", newContext.filter((op) => op).join(","), "}"].join("");
            }
        }
    }

    get attrsRemove() {
        const attrsRemove = super.attrsRemove;
        return [...attrsRemove, "default_value", "currency_field"];
    }

    prepareDataToSave(clear = true) {
        const data = super.prepareDataToSave();
        data.new_fields = Object.values(this.new_fields);
        data.button_store = Object.values(this.button_store);
        data.approvals = this.approval_store;
        data.default_store = this.default_store;
        data.update_fields = this.update_fields;
        if (clear) {
            this.new_fields = {};
            this.button_store = {};
            this.default_store = {};
            this.update_fields = {};
            this.env.bus.trigger("APPROVAL:CLEAR");
        }
        return data;
    }

    addNewPage(xpath) {
        const page = {
            attrs: {string: "New Page"}, children: [{
                attrs: {},
                children: [{attrs: {}, children: [], tag: "group"}, {attrs: {}, children: [], tag: "group"},],
                tag: "group"
            },], parentId: this.nodes[xpath.nodeId].parentId, tag: "page"
        };
        this.setNodeId(page);
        this.onXpathNode(this.nodes[xpath.nodeId], [page], xpath.position, false);
        this.render(true);
    }

    // only use for new field
    updateFieldName(oldName, newName) {
        const field = this.new_fields[oldName];
        if (field) {
            this.doNewField({name: oldName}, "delete");
            this.doNewField({...field, name: newName})
        }
    }

    updateField(fieldName, data = {}) {
        const update = this.update_fields[fieldName];
        this.update_fields[fieldName] = {...(update || {}), ...data};
    }

    doNewField(params, type = "new") {
        const {relatedModels, fields, model} = this.props.viewInfo, {name} = params;
        if (type == "delete") {
            delete this.new_fields[name];
            delete fields[name];
            delete relatedModels[model][name];
            return true;
        }
        const field = this.new_fields[name] || {string: "New Field", isNew: true, ...params};
        if (type == "update") {
            return Object.keys(params).map((attr) => {
                field[attr] = params[attr];
                fields[name][attr] = params[attr];
                relatedModels[model][name][attr] = params[attr];
            });
        }
        this.new_fields[name] = field;
        fields[name] = field;
        relatedModels[model][name] = field;
    }

    onNewButtonBox() {
        const buttonBox = this.findNode(false, (node) => (node.attrs || {}).name == "button_box");
        if (buttonBox) {
            const statButton = {
                tag: "button", children: [], attrs: {type: "action", string: "New Button", class: "oe_stat_button"}
            }
            this.setNodeId(statButton);
            buttonBox.children.push(statButton);
            this.state.node = statButton;
        }
    }

    onRemoveNode(node, showParent = true) {
        node = this.getNode(node);
        const removeNewField = (nodes) => {
            const fields = this.props.viewInfo.fields;
            nodes.map((_node) => {
                if (_node.tag == "field" && fields[_node.attrs.name]?.isNew) {
                    this.doNewField(_node.attrs.name, "delete");
                }
                removeNewField(_node?.children || []);
            });
        }
        removeNewField([node])
        super.onRemoveNode(node, showParent);
    }

    bindAction() {
        super.bindAction();
        this.$el.find(".studio_create_avatar").click((e) => {
            e.stopPropagation();
            const avatarNode = {attrs: {}, children: [], tag: "picture"};
            this.setNodeId(avatarNode);
            avatarNode.el = e.currentTarget;
            this.state.node = avatarNode;
        });
    }
}

const resetOffset = (event, ui) => {
    const parent = ui.helper.offsetParent().offset();
    const offset = {
        top: event.pageY - parent.top, left: event.pageX - parent.left,
    }
    const margins = {
        left: (parseInt(ui.helper.css("marginLeft"), 10) || 0), top: (parseInt(ui.helper.css("marginTop"), 10) || 0)
    };
    const width = ui.helper.outerWidth(), height = ui.helper.outerHeight();
    ui.helper.css({
        left: (offset.left - width / 2 - margins.left) + "px", top: (offset.top - height / 2 - margins.top) + "px"
    });
}

FormModifier.useStructure = true;
FormModifier.NodeModifier = ExtendNodeModifier;
FormModifier.showNodeRoot = false;
FormModifier.components = {...ViewComponentModifier.components, Tab: ExtendTabsModifier};
FormModifier.ArchTemplate = "dynamic_odoo.Form.View.default";
FormModifier.classes = "studio_form_view";
FormModifier.sortParams = {
    selector: [".o_form_sheet, .o_notebook_content .tab-pane", ".container, .o_inner_group, .helper-ok, .col", ".o_notebook_headers > .nav-tabs"],
    params: {},
    lifecycle: {
        start(event, ui) {
            ui.placeholder.empty().append(ui.item.clone().children());
        }, sort(event, ui) {
            resetOffset(event, ui);
        }, change(event, ui) {
            resetOffset(event, ui);
        }, stop(event, ui, superFnc, params) {
            const item = ui.item, nodeId = item.attr('node-id');
            if (item.hasClass("o_wrap_field") && !nodeId) {
                params.nodeMoves = item.children().toArray().map((child) => $(child).find("> *[node-id]").attr("node-id"));
                const nextItem = item.next();
                if (nextItem.length) {
                    params.params = {
                        nodeXpath: nextItem.find("[node-id]:eq(0)").attr("node-id"), position: "before",
                    }
                }
            }
            superFnc(event, ui, params);
        }
    }
}


modifierRegistry.add("form", FormModifier);
