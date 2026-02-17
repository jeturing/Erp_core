/** @odoo-module **/

import {jsonNodeToString} from "@dynamic_odoo/core/utils/view";

const {Component, useEffect, xml} = owl;


export class TemplateViewer extends Component {
    setup() {
        useEffect(() => {
            $(this.__owl__.refs.preview).empty().append(this.archXml);
            const {bindAction} = this.props;
            if (bindAction) bindAction();
        });
    }

    get predicate() {
        return (node) => node?.tag == "div" && node.attrs.id == 'wrapwrap';
    }

    get archXml() {
        const {archJson} = this.props.viewInfo;
        const mainView = archJson.params.findNode(false, this.predicate);
        return jsonNodeToString(mainView || {tag: "div"});
    }
}

TemplateViewer.template = xml`<div class="template_viewer"><div class="preview" ref="preview"></div></div>`


