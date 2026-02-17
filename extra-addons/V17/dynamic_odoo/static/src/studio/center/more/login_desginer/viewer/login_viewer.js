/** @odoo-module **/

import {TemplateViewer} from "@dynamic_odoo/studio/center/template/template_viewer";

const {useEffect} = owl;

export class LoginDesigner extends TemplateViewer {
    setup() {
        super.setup();
        useEffect(() => {
            const searchModal = $(this.__owl__.refs.preview).find("[data-bs-target='#o_search_modal']");
            searchModal.removeAttr("data-bs-toggle");
            searchModal.removeAttr("data-bs-target");
        });
    }

}

LoginDesigner.template = "dynamic_odoo.Login.Viewer";
