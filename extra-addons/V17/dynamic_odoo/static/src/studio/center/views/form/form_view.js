/** @odoo-module **/

import {registry} from "@web/core/registry";
import {InnerGroup} from "@web/views/form/form_group/form_group";
import {Notebook} from "@web/core/notebook/notebook";
import {FormController} from "@web/views/form/form_controller";
import {FormRenderer} from "@web/views/form/form_renderer";
import {RelationalModel} from "@web/model/relational_model/relational_model";
import {FormCompiler} from "@web/views/form/form_compiler";
import {FormArchParser} from "@web/views/form/form_arch_parser";
import {FormLabel} from "@web/views/form/form_label";
import {useViewCompiler, resetViewCompilerCache} from "@web/views/view_compiler";
import {visitXML} from "@web/core/utils/xml";
import {formView} from "@web/views/form/form_view";
import {dispatchEvent} from "@dynamic_odoo/core/studio_core";
import {Approval} from "@dynamic_odoo/base/views/form/form_view";
import {approvalCache} from "./button_approval/button_approval";
import {ViewButton} from "@web/views/view_button/view_button";
import {ButtonBox} from "@web/views/form/button_box/button_box";
import {CallbackRecorder} from "@web/webclient/actions/action_hook";
import {extractFieldsFromArchInfo} from "@web/model/relational_model/utils";
import {xmlToJson, stringToJson} from "@dynamic_odoo/core/utils/view";
import {Field} from "@web/views/fields/field";
import {isX2Many, archParseBoolean} from "@web/views/utils";
import {append, createTextNode, createElement, getTag} from "@web/core/utils/xml";
import {setNodeId, makeWrapper, WrapComponent} from "../wrap_node_compiled";
import {makeContext} from "@web/core/context";

const studioViewRegistry = registry.category("studio_views");
const {onWillUpdateProps, onWillStart, useSubEnv, Component, useEffect, onPatched} = owl;


function iconFromString(iconString) {
    const icon = {};
    if (iconString.startsWith("fa-")) {
        icon.tag = "i";
        icon.class = `o_button_icon fa fa-fw ${iconString}`;
    } else if (iconString.startsWith("oi-")) {
        icon.tag = "i";
        icon.class = `o_button_icon oi oi-fw ${iconString}`;
    } else {
        icon.tag = "img";
        icon.src = iconString;
    }
    return icon;
}

class ButtonBoxExtend extends ButtonBox {
    onAddButton(e) {
        e.stopPropagation();
        dispatchEvent("MODIFIER:BUTTON_BOX:ADD_BUTTON", {}, this.__owl__.bdom.firstNode());
    }
}

ButtonBoxExtend.template = "dynamic_odoo.Form.ButtonBox";

class NotebookExtend extends Notebook {
    setup() {
        super.setup();
        onPatched(() => {
            dispatchEvent("MODIFIER:BIND_SORT");
        });

    }

    onAddPage() {
        const {slots} = this.props, nodeId = Object.values(slots)[Object.keys(slots).length - 1]['node-id'];
        dispatchEvent("MODIFIER:NOTEBOOK:ADD_PAGE", {
            xpath: {
                nodeId: nodeId, position: "after"
            }
        }, this.__owl__.bdom.firstNode());
    }
}

NotebookExtend.template = "dynamic_odoo.Form.Notebook";

class InnerGroupExtend extends InnerGroup {
    getNodeId(row) {
        const cellComponent = (row || []).filter((cell) => cell.subType === 'item_component');
        if (cellComponent.length) {
            return ((cellComponent[0].props.fieldInfo || {}).attrs || {})['node-id'];
        }
        return false;
    }
}

InnerGroupExtend.template = "dynamic_odoo.Form.InnerGroup";

class ApprovalExtend extends Approval {
    get approvals() {
        const {btn_key} = this.props, cache = approvalCache.get(btn_key);
        if (cache) {
            // if (cache.length != super.approvals.length) {
            return cache.filter((rule) => rule.type != 'delete').map((rule) => {
                const ruleId = rule.data_exist?.id;
                return ruleId ? super.approvals.filter((ap) => ap['rule_id'] == ruleId)[0] : {state: "wait"};
            });
            // }
        }
        return super.approvals;
    }

    showDetails() {
    }
}

class ViewButtonExtend extends ViewButton {
    setup() {
        super.setup();
        onWillUpdateProps((nextProps) => {
            if (nextProps.icon && nextProps.icon !== this.props.icon) {
                this.icon = iconFromString(nextProps.icon);
            }
        });
    }

    onClick(ev) {
        if (!odoo.studio) {
            super.onClick(ev);
        }
    }
}

ViewButtonExtend.components = {...ViewButtonExtend.components, Approval: ApprovalExtend}

class FormLabelExtend extends FormLabel {
    setup() {
        super.setup();
        setNodeId(this, () => {
            const {attrs} = this.props.fieldInfo || {};
            return (attrs || {})['node-id'];
        });
    }
}

class One2ManyModifier extends Component {
    getViewRef(fieldInfo, context = {}) {
        const fieldContext = {}, regex = /'([a-z]*_view_ref)' *: *'(.*?)'/g;
        let matched;
        while ((matched = regex.exec(fieldInfo.context)) !== null) {
            fieldContext[matched[1]] = matched[2];
        }
        // filter out *_view_ref keys from general context
        const refinedContext = {};
        for (const key in context) {
            if (key.indexOf("_view_ref") === -1) {
                refinedContext[key] = context[key];
            }
        }
        return makeContext([fieldContext, this.env.services.user.context, refinedContext]);
    }

    async loadView(viewType) {
        const {fieldInfo, record} = this.props;
        const field = record._config.fields[fieldInfo.name];
        const viewService = this.env.services.view;
        const {
            fields: formFields,
            views,
        } = await viewService.loadViews({
            context: this.getViewRef(fieldInfo, field.context),
            resModel: field.relation,
            views: [[false, viewType]],
        });
        return {
            fields: formFields,
            arch: views[viewType].arch,
            archJson: stringToJson(views[viewType].arch)
        };
    }

    prepareViewInfo(viewType, archInfo) {
        const {fieldInfo, record} = this.props, field = record._config.fields[fieldInfo.name];
        const {fields, arch, xmlDoc, archJson} = archInfo;
        return {
            viewType: viewType,
            model: field.relation,
            string: field.string,
            fields: fields,
            arch: arch || xmlDoc.outerHTML,
            archJson: archJson || xmlToJson(xmlDoc)
        };
    }

    async onEditView(viewType) {
        let {fieldInfo, record} = this.props, archInfo = fieldInfo.views[viewType];
        if (!archInfo) {
            archInfo = await this.loadView(viewType);
        }
        const viewInfo = this.prepareViewInfo(viewType, archInfo);
        dispatchEvent("STUDIO_FORM:LOAD_SUBVIEW", {
            viewInfo: viewInfo, parent: record, canLoad: true, nodeId: fieldInfo.attrs['node-id']
        }, this.__owl__.bdom.el);
    }
}

One2ManyModifier.template = "dynamic_odoo.One2manyEdit";

class ExtendWrapComponent extends WrapComponent {
    get isXMany() {
        const fieldInfo = this.props.fieldInfo || {};
        return ['one2many', 'many2many'].includes(fieldInfo?.type) && fieldInfo?.views && !fieldInfo.views.default;
    }
}

ExtendWrapComponent.template = "dynamic_odoo.WrapComponent";
ExtendWrapComponent.components = {One2ManyModifier};

export class FormCompilerExtend extends FormCompiler {
    createLabelFromField(fieldId, fieldName, fieldString, label, params) {
        const formLabel = super.createLabelFromField(fieldId, fieldName, fieldString, label, params);
        const nodeId = label.getAttribute("node-id");
        if (nodeId) {
            return makeWrapper(label, formLabel, nodeId)
        }
        return formLabel;
    }

    compileNode(node, params = {}, evalInvisible = true) {
        if (!params.componentsName) {
            params.componentsName = Object.keys(FormRenderer.components);
        }
        const compileNode = super.compileNode(node, params, evalInvisible);
        const nodeId = node['getAttribute'] ? node['getAttribute']("node-id") : false;
        if (compileNode && nodeId) {
            if (params.componentsName.includes(compileNode.tagName)) {
                return makeWrapper(node, compileNode, nodeId);
            } else {
                compileNode.setAttribute("node-id", nodeId);
            }
        }
        return compileNode;
    }

    compileButtonBox(el, params) {
        const compiled = super.compileButtonBox(el, params);
        if (!compiled || compiled.tagName == "div") {
            const buttonBox = createElement("ButtonBox"), mainSlot = createElement("t", {
                "t-set-slot": `slot_1`, isVisible: true,
            });
            append(buttonBox, mainSlot);
            return buttonBox;
        }
        return compiled;
    }

    compileNotebook(el, params) {
        const compiled = super.compileNotebook(el, params);
        compiled.setAttribute("defaultPage", `__comp__.props.activeNotebookPages[${this.noteBookId - 1}]`);
        for (let i = 0; i < el.children.length; i++) {
            const child = el.children[i];
            if (getTag(child, true) !== "page") {
                continue;
            }
            const compileChild = compiled.children[i], nodeId = "'" + child.getAttribute("node-id") + "'";
            if (compileChild) compileChild.setAttribute("node-id", nodeId);
        }
        return compiled;
    }

    compileForm(el, params) {
        // check exist Header
        const elHeader = el.querySelector("header")
        if (!elHeader) {
            el.prepend(createElement("header", {}));
        }
        // move ButtonBox to outer
        const elButtonBox = el.querySelector("div[name='button_box']"),
            wrapButtonBox = createElement("div", {class: "d-flex justify-content-end my-2"});
        if (elButtonBox) {
            append(wrapButtonBox, elButtonBox.cloneNode(true));
            elButtonBox.remove();
            el.insertBefore(wrapButtonBox, el.firstChild);
        }
        const compiled = super.compileForm(el, params);
        return compiled;
    }

    compileSheet(el, params) {
        const compiled = super.compileSheet(el, params);
        if (!el.getElementsByClassName("oe_avatar").length) {
            const buttonAvatar = createElement("button", {class: "studio_create_avatar btn btn-secondary d-flex align-items-center"});
            append(buttonAvatar, createTextNode("Add Picture"));
            const sheetFG = compiled.getElementsByClassName("o_form_sheet")[0];
            sheetFG.insertBefore(buttonAvatar, sheetFG.firstChild);
        }
        return compiled;
    }

    compileField(el, params) {
        const compiled = super.compileField(el, params);
        compiled.setAttribute("readonly", "true");
        if (el.getAttribute("is_title") && !params.record?.resId) {
            const wrap = createElement("div", {});
            const _compiled = createElement("div", {class: "is_title", name: el.getAttribute("name")});
            compiled.setAttribute("t-if", "__comp__.props.record.resId");
            _compiled.setAttribute("t-if", "!__comp__.props.record.resId");
            const span = createElement("span", {});
            append(wrap, compiled);
            append(wrap, _compiled);
            append(span, createTextNode("Description..."));
            append(_compiled, span);
            return wrap;
        }
        return compiled;
    }

}

class FieldExtend extends Field {
    setup() {
        super.setup();
        onWillUpdateProps((nextProps) => {
            const {FieldComponent} = nextProps.fieldInfo;
            if (FieldComponent && (FieldComponent != this.FieldComponent)) {
                this.FieldComponent = FieldComponent;
            }
        });
    }
}

class FormControllerExtend extends FormController {
    setup() {
        const {__beforeLeave__, __getGlobalState__, __getLocalState__} = this.env;
        if (!__getLocalState__) {
            useSubEnv({
                __beforeLeave__: __beforeLeave__ || new CallbackRecorder(),
                __getGlobalState__: __getGlobalState__ || new CallbackRecorder(),
                __getLocalState__: __getLocalState__ || new CallbackRecorder(),
            });
        }
        super.setup();
        onWillUpdateProps((nextProps) => {
            this.prepareNextProps(nextProps);
            this.archInfo = nextProps.archInfo;
            const callBack = this.env.__getLocalState__._callbacks.filter((item) => item['owner'].__owl__.bdom.el == this.__owl__.bdom.el);
            callBack.map((item) => {
                const originalModel = this.model;
                this.model = {
                    exportState: originalModel.exportState.bind(originalModel),
                    root: {isNew: false, resId: originalModel.root.resId}
                };
                nextProps.state = item.callback();
                this.model = originalModel;
            });
        });
    }

    // use for case subview
    prepareNextProps(nextProps) {
        // load subview for field ( load from prev render)
        const nextArchInfo = nextProps.archInfo;
        Object.keys(nextArchInfo.fieldNodes).map((fieldKey) => {
            const fieldNode = nextArchInfo.fieldNodes[fieldKey];
            if (isX2Many(fieldNode)) {
                const oldFieldNode = this.archInfo.fieldNodes[fieldKey], views = oldFieldNode?.views || {};
                if (Object.keys(views).length && !fieldNode.views) {
                    Object.assign(fieldNode, oldFieldNode);
                }
            }
        });
        // set data for model
        const {activeFields, fields} = extractFieldsFromArchInfo(nextArchInfo, nextProps.fields);
        this.model.nextFields = fields;
        this.model.nextActiveFields = activeFields;
        // this.model.config.activeFields = activeFields;
        // this.model.config.fields = fields;
    }

    async beforeExecuteActionButton(clickParams) {
        return false;
    }

    get className() {
        const className = super.className;
        const {xmlDoc} = this.archInfo;
        className['invisible_chatter'] = xmlDoc.getAttribute("chatter") == "false" ? true : false;
        return className;
    }

    get modelParams() {
        const modelParams = super.modelParams;
        const {parent} = this.props;
        if (parent) {
            modelParams.parent = parent;
        }
        return modelParams;
    }

    async beforeUnload(ev) {
    }

    async save(params) {

    }
}

class FormRendererExtend extends FormRenderer {
    get compilerParams() {
        return {
            record: this.props.record
        }
    }

    setup() {
        super.setup();
        resetViewCompilerCache();
        this.reCompiler();
        onWillUpdateProps((nextProps) => {
            this.reCompiler(nextProps);
        });
        useEffect(() => {
            //disable a link action
            const OFormURIs = this.__owl__.bdom.firstNode().getElementsByClassName("o_form_uri");
            for (let i = 0; i < OFormURIs.length; i++) {
                const oFormUri = OFormURIs[i];
                oFormUri.removeAttribute("href");
                oFormUri.replaceWith(oFormUri.cloneNode(true));
            }
        });
    }

    reCompiler(props = this.props) {
        const {archInfo, Compiler} = props;
        const templates = {FormRenderer: archInfo.xmlDoc};
        this.templates = useViewCompiler(Compiler || FormCompiler, templates, this.compilerParams);
    }

}

FormRendererExtend.components = {
    ...FormRendererExtend.components,
    WrapComponent: ExtendWrapComponent,
    InnerGroup: InnerGroupExtend,
    Field: FieldExtend,
    ViewButton: ViewButtonExtend,
    Notebook: NotebookExtend,
    ButtonBox: ButtonBoxExtend,
    FormLabel: FormLabelExtend,
}


class StudioFormModel extends RelationalModel {
    setup(params, state) {
        this.params = params;
        super.setup(params, state);
        onWillUpdateProps((nextProps) => {
            const {activeFields, fields} = extractFieldsFromArchInfo(nextProps.archInfo, nextProps.fields);
            this.nextFields = fields;
            this.nextActiveFields = activeFields;
        });
    }

    _createRoot(config, data) {
        const {parent} = this.params;
        if (this.nextActiveFields && this.nextFields) {
            config = {...config, fields: this.nextFields, activeFields: this.nextActiveFields};
        }
        const root = super._createRoot(config, data);
        if (parent) {
            root.evalContext.parent = parent.evalContext;
            root.evalContextWithVirtualIds.parent = parent.evalContextWithVirtualIds;
        }
        return root;
    }
}

class FormArchParserExtend extends FormArchParser {
    parse(xmlDoc, models, modelName) {
        this.showAllInvisible = archParseBoolean(xmlDoc.getAttribute("show_all_invisible"));
        const archInfo = super.parse(xmlDoc, models, modelName);
        visitXML(archInfo.xmlDoc, (node) => {
            if (this.showAllInvisible && node.tagName) {
                if (node.getAttribute("invisible")) {
                    node.setAttribute("invisible", "False");
                    node.classList.add("studio_is_invisible");
                }
            }
            if (node.tagName === "field") {
                const fieldId = node.getAttribute("field_id"), fieldNode = archInfo.fieldNodes[fieldId];
                if (fieldId && fieldNode) {
                    const newFieldId = `studio_${fieldId}`;
                    node.setAttribute("field_id", newFieldId);
                    archInfo.fieldNodes[newFieldId] = fieldNode;
                    delete archInfo.fieldNodes[fieldId];
                }
            }
        });
        return archInfo;
    }
}

export const studioFormView = {
    ...formView,
    Compiler: FormCompilerExtend,
    Controller: FormControllerExtend,
    Renderer: FormRendererExtend,
    Model: StudioFormModel,
    ArchParser: FormArchParserExtend,
    props: (genericProps, view) => {
        const props = formView.props(genericProps, view);
        props.archInfo.activeActions.edit = false;
        return props;
    },
};


studioViewRegistry.add("form_studio", studioFormView);


