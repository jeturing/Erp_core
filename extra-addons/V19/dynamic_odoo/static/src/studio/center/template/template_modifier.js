/** @odoo-module **/

import {Cache} from "@web/core/utils/cache";
import {patch} from "@web/core/utils/patch";
import {ComponentModifier, NodeModifier, ComponentTabsModifier} from "../modifier";
import {evaluateExpr} from "@web/core/py_js/py";
import {stringToXml, jsonNodeToXml, stringToJson, jsonNodeToString} from "@dynamic_odoo/core/utils/view";
import {TemplateViewer} from "./template_viewer";

const DATA_OE_CONTEXT = "data-oe-context";
const DATA_OE_XPATH = "data-oe-xpath";
const DATA_OE_ID = "data-oe-id";
const DATA_OE_MODEL = "data-oe-model";
const DATA_OE_OPTIONS = "data-oe-options";

const {useEffect} = owl;

export const QWEB_SYNTAX = {
    tField: "t-field",
    tIf: "t-if",
    tOptions: "t-options",
    tForeach: "t-foreach",
    tAttSrc: "t-att-src"
};

export const DYNAMIC_MODEL = {}

patch(Cache.prototype, {
    read(...path) {
        if (path[0] in DYNAMIC_MODEL) {
            return DYNAMIC_MODEL[path[0]];
        }
        return super.read(...path)
    }
});

export const prepareDataOeContext = (self, node) => {
    const dataXpath = node.attrs[DATA_OE_XPATH], dataId = node.attrs[DATA_OE_ID];
    let dataContext = {}, context = node.attrs[DATA_OE_CONTEXT];
    if (!context) {
        const elNodes = document.querySelectorAll(`[${DATA_OE_XPATH}='${dataXpath}']`);
        context = elNodes.length ? elNodes[0].getAttribute(DATA_OE_CONTEXT) : false;
    }
    if (!context) {
        const archXml = stringToXml(jsonNodeToXml(self.params.viewInfo.archJson));
        const elNodes = archXml.querySelector(`[${DATA_OE_XPATH}='${dataXpath}'][${DATA_OE_ID}='${dataId}']`);
        context = elNodes ? elNodes.getAttribute(DATA_OE_CONTEXT) : false;
    }
    context = JSON.parse(context || '{}');
    Object.keys(context).map((name) => {
        const value = context[name];
        if (odoo.studio.models.filter((model) => model.model == value).length) {
            dataContext[name] = {relation: value, type: "many2one", name: name, string: name, searchable: true}
        }
    });
    return dataContext;
}

export const getOptions = (node) => {
    return evaluateExpr(node.attrs[QWEB_SYNTAX.tOptions] || "{}");
}

export class ComponentTabsModifierTemplate extends ComponentTabsModifier {

}

export class NodeModifierTemplate extends NodeModifier {

}

export class ComponentModifierTemplate extends ComponentModifier {
    setup() {
        super.setup();
        this.templates = {};
        const reload = () => this.reload.bind(this)(true);
        useEffect(() => {
            this.env.bus.addEventListener("TEMPLATE:UNDO-REDO", reload);
            return () => {
                this.env.bus.removeEventListener("TEMPLATE:UNDO-REDO", reload);
            };
        });
    }

    get structureNode() {
        const {node} = this.state;
        if (node) {
            const templateId = node.attrs[DATA_OE_ID];
            if (templateId in this.templates) {
                return this.templates[templateId].arch;
            }
        }
        return super.structureNode;
    }

    get nodeParams() {
        const props = super.nodeParams;
        props.modifier = this;
        return props;
    }

    get structureNodeProps() {
        const props = super.structureNodeProps;
        props.useCodeEditor = true;
        props.onSaveCode = async (code) => {
            await this.saveTemplate(this.currentTemplateId, code);
        };
        return props;
    }

    get currentEl() {
        const {node} = this.state;
        return this.$el.find(`[${DATA_OE_XPATH}='${node.attrs[DATA_OE_XPATH]}']`);
    }

    get currentTemplateId() {
        return this.state.node.attrs[DATA_OE_ID];
    }

    getNode(nodeId) {
        const node = super.getNode(nodeId);
        const realNode = this.findNodeReport(node.attrs[DATA_OE_XPATH], node.attrs[DATA_OE_ID]);
        if (!realNode && !this.nodes[node.nodeId]) {
            // this node has been removed.
            return false;
        }
        return realNode || node;
    }

    setElToNode() {
        const {node} = this.state;
        const selector = `[${DATA_OE_XPATH}='${node.attrs[DATA_OE_XPATH]}'][${DATA_OE_ID}='${node.attrs[DATA_OE_ID]}']`;
        node.el = $(this.__owl__.bdom.el).find(selector);
    }

    async stopSort(nodeMove, params = {}, isNew = false) {
        if (isNew) {
            this.setNodeId(nodeMove);
        }
        const {nodeXpath, position} = params;
        await this.onXpathNode(nodeXpath, Array.isArray(nodeMove) ? nodeMove : [nodeMove], position, !isNew);
    }

    get loadTemplateProps() {
        return {
            context: {
                TEMPLATE_KEY: this.key,
                Studio: true,
            }
        }
    }

    get key() {
        return this.props.viewInfo.key;
    }


    async loadTemplate(templateId, force = false) {
        if (templateId && (!(templateId in this.templates) || force)) {
            const template = await this.props.model.loadTemplate(templateId, this.loadTemplateProps)
            template.arch = stringToJson(template.arch, false);
            this.templates[templateId] = template;
            this.setNodeId(template.arch);
        }
    }

    async onClickNode(e) {
        e.preventDefault();
        e.stopPropagation();
        e.stopImmediatePropagation();
        const el = this.isAddress($(e.currentTarget)), xpath = el.attr(DATA_OE_XPATH), templateId = el.attr(DATA_OE_ID);

        if (!(templateId in this.templates)) await this.loadTemplate(templateId);
        const findNode = this.findNodeReport(xpath, templateId);
        if (findNode) this.state.node = findNode;
    }

    isAddress(el) {
        const address = el.parents("address");
        if (address.length) {
            return address.parent().addClass("is_address");
        }
        return el;
    }

    async _onXpathNode(node, nodeMoves, position = "after", deleteMove = false, resetNode = true) {
        if (typeof node == "string") node = this.nodes[node];
        const templateId = node.attrs[DATA_OE_ID];
        if (!(templateId in this.templates)) await this.loadTemplate(templateId);

        nodeMoves.map((nodeMove) => {
            if (typeof nodeMove == "string") nodeMove = this.getNode(nodeMove);
            nodeMove.attrs[DATA_OE_ID] = node.attrs[DATA_OE_ID];
        });
        super.onXpathNode(node, nodeMoves, position, deleteMove, resetNode);
    }

    async onXpathNode(node, nodeMoves, position = "after", deleteMove = false, resetNode = true) {
        if (typeof node == "string") node = this.getNode(node);
        const templateId = node.attrs[DATA_OE_ID];
        if (!(templateId in this.templates)) await this.loadTemplate(templateId);
        await this._onXpathNode(node, nodeMoves, position, deleteMove, false);
        await this._saveTemplate(node.attrs[DATA_OE_ID]);
        await this.props.reloadReport();
        await this.loadTemplate(templateId, true);
        this.state.node = this.getNode(nodeMoves[0].nodeId);
    }

    findNodeReport(xpath, templateId) {
        const {arch} = this.templates[templateId] || {};
        if (!xpath || !templateId || !arch) {
            return false;
        }
        const findNode = this.findNode(arch,
            (node) => node.tag && node.attrs[DATA_OE_ID] == templateId && node.attrs[DATA_OE_XPATH] == xpath);
        return findNode;
    }

    templateToString(templateId) {
        const {arch} = this.templates[templateId];
        const loopTemplate = (nodes) => {
            nodes.map((node) => {
                if (node?.tag) {
                    loopTemplate(node.children || []);
                }
            });
        }
        loopTemplate([arch]);
        return jsonNodeToString(arch)
    }

    async _saveTemplate(templateId, templateString) {
        await this.props.model.saveTemplate(this.key, templateId, templateString || this.templateToString(templateId), this.loadTemplateProps);
    }

    async saveTemplate(templateId = this.currentTemplateId, templateString = false) {
        if (!(templateId in this.templates)) await this.loadTemplate(templateId);
        await this._saveTemplate(templateId, templateString);
        await this.reload();
    }

    async reload(resetNode = true) {
        await this.props.reloadReport();
        await this.loadTemplate(this.currentTemplateId, true);
        if (resetNode)
            this.state.node = this.getNode(this.state.node) || this.props.viewInfo.archJson;
    }

    async onChangeProp(prop, value) {
        await this.saveTemplate();
    }

    bindStyle() {
        const clActive = "node-active";
        this.$el.find(`.${clActive}`).removeClass(clActive);
        this.currentEl.addClass(clActive);
    }

    bindAction() {
        this.$el = $(this.__owl__.bdom.el);
        this.$el.find(`[${DATA_OE_XPATH}]`).click(this.onClickNode.bind(this));
        this.bindSort();
    }
}

ComponentModifierTemplate.showNodeRoot = false;
ComponentModifierTemplate.useStructure = true;
ComponentModifierTemplate.classes = "studio_edit_template";
// ComponentModifierTemplate.components = {...ComponentModifier.components, Tab: ComponentTabsModifierTemplate};
ComponentModifierTemplate.NodeModifier = NodeModifierTemplate;
ComponentModifierTemplate.ViewComponent = TemplateViewer;