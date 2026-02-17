/** @odoo-module **/

import {GraphArchParser} from "@web/views/graph/graph_arch_parser";
import {GraphRenderer} from "@web/views/graph/graph_renderer";
import {graphView} from "@web/views/graph/graph_view";
import {archParseBoolean} from "@web/views/utils";
import {patch} from "@web/core/utils/patch";
import {visitXML} from "@web/core/utils/xml";
import {getColor, hexToRGBA} from "@web/core/colors/colors";

patch(GraphArchParser.prototype, {
    parse(arch, fields = {}) {
        const archInfo = super.parse(...arguments);
        visitXML(arch, (node) => {
            switch (node.tagName) {
                case "graph": {
                    if (node.hasAttribute("area")) {
                        archInfo.area = archParseBoolean(node.getAttribute("area"));
                    }
                    if (node.hasAttribute("smooth")) {
                        archInfo.smooth = archParseBoolean(node.getAttribute("smooth"));
                    }
                    const mode = node.getAttribute("type");
                    if (mode && ['polar_area', 'doughnut', 'column'].includes(mode)) {
                        archInfo.mode = mode;
                    }
                }
            }
        });
        return archInfo;
    }
});

patch(GraphRenderer.prototype, {
    // setup() {
    //     super.setup();
    //     this.__owl__.parent.parent.rendererInst = this;
    // },

    formatValue(value, allIntegers = true) {
        if (value) {
            return super.formatValue(value, allIntegers);
        }
    },

    prepareOptions() {
        const options = super.prepareOptions();
        const {mode} = this.model.metaData;
        if (mode == "column") {
            options.indexAxis = "y"
        }
        return options;
    },

    getChartConfig() {
        let data = null, metaData = this.model.metaData, {mode} = metaData,
            replaceType = {column: "bar", polar_area: "polarArea"};
        if (["doughnut", "polar_area", "column"].includes(mode)) {
            data = this.getPieChartData();
            const options = this.prepareOptions();
            mode = replaceType[mode] || mode;
            return {data, options, type: mode};
        } else {
            return super.getChartConfig();
        }
    },

    getScaleOptions() {
        const {mode} = this.model.metaData;
        const stacked = this.props.model.metaData.stacked;
        if (["doughnut", "polar_area"].includes(mode)) {
            return {};
        }
        if ("column" == mode) {
            return {
                x: {
                    stacked: stacked,
                },
                y: {
                    stacked: stacked,
                },

            }
        }
        return super.getScaleOptions();
    },

    getLineChartData() {
        const data = super.getLineChartData();
        const {area, smooth} = this.model.metaData;
        for (let index = 0; index < data.datasets.length; ++index) {
            const dataSet = data.datasets[index];
            if (area) {
                const color = getColor(index);
                dataSet.backgroundColor = hexToRGBA(getColor(0), 0.2);
                dataSet.fill = 'origin';
                dataSet.borderColor = color;
            } else {
                delete dataSet.backgroundColor;
                delete dataSet.fill;
            }
            if (smooth) {
                dataSet.lineTension = 0.4;
            }
        }
        return data;
    },
});


const superGrapProps = graphView.props;

graphView.props = (genericProps, view) => {
    const props = superGrapProps(genericProps, view);
    if (!genericProps.state) {
        const {arch, fields} = genericProps;
        const parser = new view.ArchParser();
        const archInfo = parser.parse(arch, fields);
        props.modelParams.stacked = "stacked" in archInfo ? archInfo.stacked : false;
        props.modelParams.area = Boolean(archInfo.area);
        props.modelParams.smooth = Boolean(archInfo.smooth);
    }
    return props;
}
