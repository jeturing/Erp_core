/** @odoo-module **/
import {jsonNodeToXml} from "@dynamic_odoo/core/utils/view";

const {Component, useState, onWillUpdateProps, onWillStart, xml} = owl;


export class Battery extends Component {
    setup() {
        super.setup();
        this.setTemplate();
        this.state = useState({active: false});
        onWillStart(async () => {
            await this.loadData();
        });
        onWillUpdateProps(async (nextProps) => {
            await this.loadData();
            this.setTemplate();
        });
    }

    setTemplate() {
        const {viewInfo} = this.props, archJson = viewInfo.archJson;
        this.template = xml`${archJson.children[0] ? jsonNodeToXml(archJson.children[0]) : '<div></div>'}`;
    }

    async loadData() {
        const {viewInfo} = this.props, {model, domain} = viewInfo;
        const {measure, colors, group_by} = viewInfo.archJson.attrs;
        if (model) {
            this.state.active = false;
            this.raw_groups = await this.env.services.orm.readGroup(model, domain || [], measure ? [measure] : [], group_by ? [group_by] : []);
            this.prepareGroups(this.raw_groups);
            this.modelName = model;
            this.groupBy = group_by;
            this.measure = measure;
            this.colors = colors;
        } else if (((measure != this.measure) || (this.colors != colors)) && this.raw_groups) {
            this.measure = measure;
            this.prepareGroups(this.raw_groups);
        }
    }

    prepareGroups(groups) {
        const {archJson, fields} = this.props.viewInfo;
        const {group_by, colors, measure} = archJson.attrs, data = {};
        if (group_by) {
            const field = fields[group_by], colorByGroup = {},
                measure_key = measure || (group_by + "_count"),
                total = groups.reduce((total, group) => total + group[measure_key], 0),
                randomColor = () => `#${Math.floor(Math.random() * 16777215).toString(16).padStart(6, '0')}`;
            const getLabel = (op) => field.selection.filter((option) => option[0] == op);
            if (colors) {
                colors.split(",").map((color) => {
                    color = color.split(":");
                    colorByGroup[color[0]] = color[1];
                });
            }
            groups.map((group) => {
                const groupBy = group[group_by];
                if (!colorByGroup[groupBy]) {
                    colorByGroup[groupBy] = randomColor();
                }
                const label = getLabel(groupBy);
                data[groupBy] = {
                    data: group[measure_key],
                    color: colorByGroup[groupBy],
                    percen: total != 0 ? group[measure_key] / total * 100 : 0,
                    label: label.length ? label[0][1] : "No Label",
                    groupBy: groupBy,
                };
                if (!this.state.active) {
                    this.state.active = groupBy;
                }
            });
            this.props.viewInfo.archJson.attrs.colors = Object.entries(colorByGroup).map((color) => color[0] + ":" + color[1]).join(",");
        }
        this.groups = data;
    }

    onShowInfo(group) {
        this.state.active = group.groupBy;
    }

    get info() {
        const {active} = this.state, group = this.groups[active];
        return `${Math.round(group?.percen || 0)}% ${group?.label || "Undefined"}`;
    }
}

Battery.template = xml`<div class="dbWidgetBattery"><t t-call="{{template}}" /></div>`;
