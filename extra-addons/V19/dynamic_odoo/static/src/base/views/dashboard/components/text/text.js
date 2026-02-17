/** @odoo-module **/

import {StudioHtmlField} from "@dynamic_odoo/core/fields/html_field/html_field";
import {jsonNodeToXml} from "@dynamic_odoo/core/utils/view";

const {Component, useEffect, useState, onWillUpdateProps, xml} = owl;

export class Text extends Component {

    setup() {
        super.setup();
        this.setTemplate();
        onWillUpdateProps(async (nextProps) => {
            this.setTemplate();
        });
        useEffect(() => {
            $(this.__owl__.refs.text).html(this.richText);
        })
    }

    setTemplate() {
        const {viewInfo} = this.props, {archJson} = viewInfo;
        if (archJson.attrs.text) {
            this.richText = archJson.attrs.text;
        }
        this.template = xml`${jsonNodeToXml(archJson.children[0])}`;
    }
}

Text.template = xml`<t t-call="{{template}}" />`;
