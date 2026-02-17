/** @odoo-module **/

import {ViewController} from "../view_controller";
import {ReportModifier} from "./modifier/report_modifier";
import {xmlToJson, stringToXml, xmlToString} from "@dynamic_odoo/core/utils/view";
import {useService} from "@web/core/utils/hooks";
import {Dialog} from "@web/core/dialog/dialog";
import {getReportUrl} from "@web/webclient/actions/reports/utils";
import {useModel} from "@web/model/model";
import {TemplateModel} from "@dynamic_odoo/studio/center/template/template_model";

const {Component, onMounted, onWillUnmount, useState, onWillUpdateProps, onWillStart} = owl;

class ReportCenterModel extends TemplateModel {
    static REPORT_MODEL = "studio.report.center";
    static ACTIONS_REPORT = "ir.actions.report";
    static IR_QWEB = "ir.qweb";

    async loadRecord(resModel) {
        return await this.orm.searchRead(resModel, [], ["id"]);
    }

    async loadFieldWidgets() {
        return await this.orm.call(this.constructor.TEMPLATE_MODEL, "get_field_widget", []);
    }

    async createReport(values) {
        return await this.orm.call(this.constructor.TEMPLATE_MODEL, "create_new_report", [values])
    }

    async updateActionsReport(reportId, values = {}) {
        return await this.orm.write(this.constructor.ACTIONS_REPORT, [reportId], values);
    }
}

class ReportTemplates extends Component {
    setup() {
        this.state = useState({template: "external"});
    }

    get templates() {
        return {
            external: {
                title: "External",
                desc: "Business header/footer",
                template: "dynamic_odoo.ReportTemplates.External"
            },
            internal: {
                title: "Internal",
                desc: "Minimal header/footer",
                template: "dynamic_odoo.ReportTemplates.Internal"
            },
            blank: {title: "Blank", desc: "No header/footer", template: "dynamic_odoo.ReportTemplates.Blank"}
        }
    }

    get prepareNewReport() {
        const {template} = this.state, {resModel} = this.props;
        const archReportXml = stringToXml(this.__owl__.app.rawTemplates[this.templates[template].template].innerHTML).firstChild;
        const module = "report_studio", name = `studio_report_${template}_${Date.now()}`, xmlId = `${module}.${name}`;
        archReportXml.setAttribute("t-name", xmlId);

        return {
            xml: xmlToString(archReportXml),
            xml_id: xmlId,
            name: name,
            model: resModel,
            string: "New Report", module: module,
            report_file: xmlId,
            report_xml_id: `report_studio.action_${name}`,
            report_name: xmlId,
        }
    }

    async confirm() {
        const data = await this.props.model.createReport(this.prepareNewReport);
        await this.props.loadReport(data.id);
        this.props.close();
    }
}

ReportTemplates.template = "dynamic_odoo.Report.ReportTemplates";
ReportTemplates.components = {Dialog};

class ReportKanbanView extends ViewController {
    static viewType = "kanban";

    setup() {
        super.setup();
        this.dialogService = useService("dialog");
    }

    get domain() {
        return `[['model', '=', '${this.props.resModel}'], ['binding_model_id', '!=', False]]`
        // return `[['model', '=', '${this.props.resModel}']]`
    }

    get componentProps() {
        const props = super.componentProps, {resModel} = this.props;
        if (resModel) {
            props.irFilters = [
                {
                    context: "{}",
                    domain: `[['model', '=', '${resModel}']]`,
                    is_default: true,
                    name: resModel,
                },
            ]
        }
        return props;
    }

    async selectRecord(resId) {
        await this.props.onSelectRecord(resId)
    }

    async createRecord() {
        const {model, resModel} = this.props;
        this.dialogService.add(ReportTemplates, {
            model: model,
            resModel: resModel,
            loadReport: this.props.onSelectRecord
        });
    }
}

ReportKanbanView.actionXmlID = "base.ir_action_report";

const REPORT_STATE = {choose: "choose", modifier: "modifier"}

export default class ReportCenter extends Component {
    setup() {
        // type will have 2 options. choose | modifier
        this.http = useService("http");
        this.state = useState({type: REPORT_STATE.choose, reportId: false});
        this.actionService = useService("action");
        this.model = useModel(ReportCenterModel);
        onWillStart(async () => {
            this.fieldWidgets = await this.model.loadFieldWidgets();
        });
    }

    get uriState() {
        return odoo.studio.getState();
    }

    get breadcrumbs() {
        const {type} = this.state
        if (type == REPORT_STATE.modifier) {
            return [
                {title: "Reports", onClick: () => this.state.type = REPORT_STATE.choose},
                {
                    title: this.action.name, onClick: () => {
                    }
                }
            ];
        }
        return [];
    }

    get viewInfo() {
        const parser = new DOMParser();
        const {id, report_name} = this.action;
        const xml = parser.parseFromString(this.reportHtml, "text/html");
        const viewInfo = {
            archJson: xmlToJson(xml),
            fields: {},
            model: this.uriState.model,
            reportUrl: this.reportUrl,
            reportId: id,
            key: report_name,
            reportName: report_name,
            params: {
                binding_model_id: this.action.binding_model_id,
                fieldWidgets: this.fieldWidgets,
            }
        }
        return viewInfo;
    }

    async onLoadReport(reportId = this.state.reportId) {
        await this.loadAction(reportId);
        await this.loadReport();
    }

    get activeId() {
        return [this.uriState.id || (this.records.length ? this.records[0].id : false)];
    }

    async loadAction(reportId) {
        this.env.bus.trigger("CLEAR-CACHES");
        this.action = await this.actionService.loadAction(reportId, this.uriState);
        this.action.data = {studio: true, active_model: this.uriState.model};
        this.action.context.Studio = true;
        this.action.context.active_ids = this.activeId;
    }

    async loadReport() {
        this.reportUrl = getReportUrl(this.action, "html", {...this.env.services.user.context, Studio: true});
        this.reportUrl = this.reportUrl.replace("?options", `/${this.activeId[0]}?options`);
        this.reportHtml = await this.http.get(this.reportUrl, "text");
    }

    async reload() {
        await this.onLoadReport();
        this.render(true);
    }

    async printReport() {
        this.actionService.doAction(this.action, odoo.studio.getState());
    }

    async onSelectRecord(recordId) {
        if (!this.records) {
            this.records = await this.model.loadRecord(this.uriState.model);
        }
        await this.onLoadReport(recordId);
        this.state.reportId = recordId;
        this.state.type = REPORT_STATE.modifier;
    }
}

ReportCenter.template = "dynamic_odoo.ReportCenter";
ReportCenter.components = {Choose: ReportKanbanView, Modifier: ReportModifier}


