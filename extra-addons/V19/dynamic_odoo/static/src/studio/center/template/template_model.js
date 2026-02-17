/** @odoo-module **/

import {Model} from "@web/model/model";


export class TemplateModel extends Model {
    static TEMPLATE_MODEL = "studio.template.center";
    static IR_QWEB = "ir.qweb";

    async saveTemplate(templateKey, templateId, archString, options = {}) {
        await this.orm.call(this.constructor.TEMPLATE_MODEL, "store_template", [templateKey, parseInt(templateId), archString], options);
    }

    async loadTemplate(templateId, params = {}) {
        return await this.orm.call(this.constructor.IR_QWEB, "load_template", [parseInt(templateId)], params);
    }

    async undoRedoTemplate(templateKey, type = "undo") {
        return await this.orm.call(this.constructor.TEMPLATE_MODEL, "undo_redo_template", [templateKey, type]);
    }

    async canUndoRedo(templateKey) {
        return await this.orm.call(this.constructor.TEMPLATE_MODEL, "can_undo_redo", [templateKey]);
    }

     async resetTemplate(templateKey) {
        return await this.orm.call(this.constructor.TEMPLATE_MODEL, "reset_view", [templateKey]);
    }

}
