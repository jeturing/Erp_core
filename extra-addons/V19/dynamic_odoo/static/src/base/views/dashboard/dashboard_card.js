/** @odoo-module **/

import {Dropdown} from "@web/core/dropdown/dropdown";

import {download} from "@web/core/network/download";

const {Component, useState} = owl;
import {DashboardComponent} from "./components/components";
import {DASHBOARD_STORE_MODEL} from "./dashboard_model";

export class DashboardCard extends Component {
    get exportOptions() {
        return {
            csv: {
                label: "CSV", fn: () => {
                    this.exportToCSV();
                }
            },
            pdf: {
                label: "PDF", fn: () => {
                    this.exportToPdf();
                }
            },
            png: {
                label: "PNG", fn: () => {
                    this.exportToImage("png");
                }
            },
            jpg: {
                label: "JPG", fn: () => {
                    this.exportToImage("jpg");
                }
            },
        }
    }

    // setup() {
    //     super.setup();
        // this.state = useState({showTitle: this.shouldShowTitle()});
    // }

    // shouldShowTitle() {
    //     const withoutType = ["title"];
    //     return !withoutType.includes(this.props.viewInfo.viewType);
    // }

    onFullScreen() {
        const {elStackItem} = this.props;
        elStackItem.addClass("noTransition").toggleClass("full");
        elStackItem.removeClass("noTransition");
    }

    exportToExcel() {
        const {viewInfo, canExport} = this.props
        if (!canExport) return;
        const chart = Chart.getChart(this.__owl__.bdom.el.querySelector("canvas")), dataSets = chart.data.datasets;
        const data = {
            data: {
                labels: ["Measure", ...chart.data.labels.map((labels) => labels[0])],
                rows: dataSets.map((dataSet) => [dataSet.label || "Total", ...dataSet.data])
            },
            file_name: `${viewInfo.title}.xlsx`
        };
        download({
            url: "/web/dashboard/xlsx",
            data: {data: JSON.stringify(data)},
        });
    }

    exportToCSV() {
        const {viewInfo, canExport} = this.props
        if (!canExport) return;
        const chart = Chart.getChart(this.__owl__.bdom.el.querySelector("canvas"));
        let dataSets = chart.data.datasets,
            dataCSV = ["Measure", ...chart.data.labels].join(";").concat("\n");
        dataSets.map((dataSet) => {
            dataCSV += [dataSet.label, ...dataSet.data].join(";").concat("\n");
        });
        if (!dataCSV) {
            return false;
        }
        dataCSV = encodeURI('data:text/csv;charset=utf-8,' + dataCSV);
        const link = document.createElement('a');
        link.setAttribute('href', dataCSV);
        link.setAttribute('download', `${viewInfo.title || 'file'}.csv`);
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    //
    exportToImage(fileType) {
        const {viewInfo, canExport} = this.props, {title} = viewInfo;
        if (canExport) {
            const elCanvas = $(this.__owl__.bdom.el).find("canvas"),
                url_base64jp = elCanvas[0].toDataURL(`image/${fileType}`);
            const elDownload = document.createElement("a");
            elDownload.setAttribute('href', url_base64jp);
            elDownload.setAttribute('download', `${title || "download"}.${fileType}`);
            elDownload.click();
        }
    }

    exportToPdf() {
        // get size of report page
        const {viewInfo, canExport} = this.props, elCanvas = $(this.__owl__.bdom.el).find("canvas"),
            // elCanvas = $(`#${chartId}`),
            reportPageHeight = elCanvas.innerHeight(), reportPageWidth = elCanvas.innerWidth();
        // create a new canvas object that we will populate with all other canvas objects
        if (!canExport) return;
        let pdfCanvas = $('<canvas />').attr({
            id: "canvasPdf",
            width: reportPageWidth,
            height: reportPageHeight
        });

        // keep track canvas position
        const canvasOptions = {ctx2D: $(pdfCanvas)[0].getContext('2d'), x: 0, y: 0, buffer: 100};
        // for each chart.js chart
        elCanvas.each(function (index) {
            // get the chart height/width
            const el = $(this), canvasHeight = el.innerHeight(), canvasWidth = el.innerWidth();
            // draw the chart into the new canvas
            const {ctx2D, x, y, buffer} = canvasOptions;
            ctx2D.drawImage($(this)[0], x, y, canvasWidth, canvasHeight);
            canvasOptions.x += canvasWidth + buffer;
            // our report page is in a grid pattern so replicate that in the new canvas
            if (index % 2 === 1) {
                canvasOptions.x = 0;
                canvasOptions.y += canvasHeight + buffer;
            }
        });
        let pdf = new jsPDF('p', 'px', 'a4');
        const pageSize = pdf.internal.pageSize, pageWidth = pageSize.width - 100,
            pageHeight = ((reportPageHeight - 0) * pageWidth) / (reportPageWidth - 0);
        pdf.addImage($(pdfCanvas)[0], 'PNG', 50, 50, pageWidth, pageHeight);
        pdf.save(`${viewInfo.title}.pdf`);
    }
}


DashboardCard.template = "dynamic_odoo.DashboardCard";
DashboardCard.components = {Dropdown, DashboardComponent};
DashboardCard.props = {
    id: {type: Number},
    editable: {type: Boolean, optional: true},
    viewInfo: {type: Object, optional: true},
}
