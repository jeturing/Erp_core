/** @odoo-module **/

const {Component, useState} = owl;

export class GraphType extends Component {
    setup() {
        super.setup();
        this.prepareGraphType();
        const {value} = this.props;
        this.state = useState({value: value});
    }

    prepareGraphType() {
        this.modes = {};
        this.modes.bar = {title: "Bar", icon: "bar_icon.svg", value: {type: "bar"}};
        this.modes.stacked_bar = {
            title: "Stacked Bar",
            icon: "stacked_bar_icon.svg",
            value: {type: "bar", stacked: true}
        };
        this.modes.stacked_bar_100 = {
            title: "100% Stacked Bar",
            icon: "stacked_bar_100_icon.svg",
            value: {type: "bar", stacked: true}
        };
        this.modes.pie = {title: "Pie", icon: "pie_icon.svg", value: {type: "pie"}};
        this.modes.doughnut = {title: "Doughnut", icon: "donut_icon.svg", value: {type: "doughnut"}};
        this.modes.polar_area = {title: "Polar Area", icon: "polar_area_icon.svg", value: {type: "polar_area"}};
        this.modes.line = {title: "Line", icon: "line_icon.svg", value: {type: "line"}};
        this.modes.smooth_line = {
            title: "Smooth Line",
            icon: "smooth_line_icon.svg",
            value: {type: "line", smooth: true}
        };
        this.modes.stacked_line = {
            title: "Stacked Line",
            icon: "stacked_line_icon.svg",
            value: {type: "line", stacked: true}
        };
        this.modes.stacked_line_100 = {
            title: "100% Stacked Line",
            icon: "stacked_line_100_icon.svg",
            value: {type: "line", stacked: true}
        };
        this.modes.column = {title: "Column", icon: "column_icon.svg", value: {type: "column"}};
        this.modes.stacked_column = {
            title: "Stacked Column",
            icon: "stacked_column_icon.svg",
            value: {type: "column", stacked: true}
        };
        this.modes.stacked_column_100 = {
            title: "100% Stacked Column",
            icon: "stacked_column_100_icon.svg",
            value: {type: "column", stacked: true}
        };
        this.modes.area = {title: "Area", icon: "area_icon.svg", value: {type: "line", area: true}};
        this.modes.stacked_area = {
            title: "Stacked Area",
            icon: "stacked_area_icon.svg",
            value: {type: "line", area: true, smooth: true, stacked: true}
        };
        this.modes.stacked_area_100 = {
            title: "100% Stacked Area",
            icon: "stacked_area_100_icon.svg",
            value: {type: "line", area: true, stacked: true}
        };

        this.groups = {
            most_popular: {title: "Chart Type", modes: ["pie", "bar", "line", "stacked_bar"]},
            pie: {title: "Pie", modes: ["pie", "polar_area", "doughnut"]},
            line: {title: "Line", modes: ["line", "smooth_line", "stacked_line"]},
            bar: {title: "Bar", modes: ["bar", "stacked_bar", "column"]},
            column: {title: "Column", modes: ["column", "stacked_column"]},
            area: {title: "Area", modes: ["area", "stacked_area"]},
        };
    }

    isActive(info) {
        const {value} = this.state;
        if (Object.keys(info).length == Object.keys(value).length) {
            return (Object.keys(info).map((key) => {
                return info[key] == value[key]
            })).every(Boolean);
        }
        return false;
    }

    onClickType(typeInfo) {
        this.state.value = typeInfo;
        this.props.update(typeInfo);
    }
}

GraphType.noFieldLabel = true;
GraphType.template = "dynamic_odoo.Widget.GraphType";
