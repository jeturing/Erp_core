/** @odoo-module **/

import {append, createElement} from "@web/core/utils/xml";

const {Component, onMounted, onPatched, xml} = owl;

export const setNodeId = (self, nodeId = () => {
}) => {
    const _setNodeId = (_nodeId) => {
        let firstNode = self.__owl__.bdom.firstNode();
        if (!firstNode.hasOwnProperty("setAttribute")) {
            const child = Object.values(self.__owl__.children);
            if (child.length) {
                firstNode = child[0].firstNode();
            }
        }
        if (firstNode) {
            firstNode.setAttribute("node-id", _nodeId);
        }
    }
    onMounted(() => {
        _setNodeId(nodeId());
    });
    onPatched(() => {
        _setNodeId(nodeId());
    });
}

export const makeWrapper = (node, compileNode, nodeId) => {
    const mainSlot = createElement("t", {
        "t-set-slot": "compile_component",
    }), wrapProps = {nodeId: `'${nodeId}'`};
    // set attr for wrap from compileNode
    for (let i = 0; i < compileNode.attributes.length; i++) {
        const attr = compileNode.attributes[i]
        wrapProps[attr.name] = attr.value;
    }
    const wrapCom = createElement("WrapComponent", wrapProps);
    append(mainSlot, compileNode);
    append(wrapCom, mainSlot);
    // when set attr for wrap, it will dispatch to compileNode
    wrapCom.setAttribute = (name, value) => {
        compileNode.setAttribute(name, value);
    }
    return wrapCom;
}

export class WrapComponent extends Component {
    setup() {
        super.setup();
        setNodeId(this, () => this.props.nodeId);
    }
}

WrapComponent.template = xml`<t t-ref="component" t-slot="compile_component" />`;
