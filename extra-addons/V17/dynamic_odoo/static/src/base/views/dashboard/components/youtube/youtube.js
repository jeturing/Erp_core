/** @odoo-module **/

import {jsonNodeToXml} from "@dynamic_odoo/core/utils/view";

const {Component, useEffect, onWillUnmount, onMounted, useState, onWillUpdateProps, onWillStart, xml} = owl;

export class Youtube extends Component {

    setup() {
        super.setup();
        this.state = useState({link: "https://www.youtube.com/embed/OBZMGgGjpLs"});
        this.setTemplate();
        onWillUpdateProps(async (nextProps) => {
            this.setTemplate();
        });
    }

    setTemplate() {
        const {viewInfo} = this.props, {archJson} = viewInfo;
        if (archJson.attrs.link) {
            this.state.link = archJson.attrs.link;
        }
        this.template = xml`${jsonNodeToXml(archJson.children[0])}`;
    }
}

Youtube.template = xml`<t t-call="{{template}}" />`;
