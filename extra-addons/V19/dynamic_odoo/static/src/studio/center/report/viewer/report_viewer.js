/** @odoo-module **/
import {TemplateViewer} from "@dynamic_odoo/studio/center/template/template_viewer";
import {jsonNodeToString} from "@dynamic_odoo/core/utils/view";

const {useState} = owl;

export class ReportViewer extends TemplateViewer {
    setup() {
        super.setup();
        this.state = useState({show_area: odoo.studio.show_area || false});
    }

    get predicate() {
        return (node) => node?.tag == "main";
    }

    onShowArea() {
        this.state.show_area = !this.state.show_area;
        odoo.studio.show_area = this.state.show_area;
    }

    get archXml() {
        const {archJson} = this.props.viewInfo;
        const mainView = archJson.params.findNode(false, this.predicate);
        const copyMainView = []
        const copyNode = (node, wrap) => {
            if (!node.tag) {
                wrap.push(node);
            } else if (!["link", "meta", "script"].includes(node.tag)) {
                const _node = {...node, children: []}
                wrap.push(_node);
                (node.children || []).map((n) => {
                    copyNode(n, _node.children);
                });
            }
        }
        copyNode(mainView, copyMainView);
        return jsonNodeToString(copyMainView[0] || {tag: "div"});
        // return jsonNodeToString(mainView || {tag: "div"});
    }

    async onHistory(type) {
        const {model, reloadReport, templateKey} = this.props;
        if (this.props[`can_${type}`]) {
            await model.undoRedoTemplate(templateKey, type);
            await reloadReport();
        }
    }

    //
    // onIframeLoaded(ev) {
    //     const iframeDocument = ev.target.contentWindow.document;
    //     iframeDocument.body.classList.add("o_in_iframe", "container-fluid");
    //     iframeDocument.body.classList.remove("container");
    //
    //     $(iframeDocument).find("*").click(() => {
    //         alert("ok")
    //     });
    // }
}

ReportViewer.template = "dynamic_odoo.ReportViewer";
