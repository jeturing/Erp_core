/** @odoo-module **/

import {CharField} from "../char_field/char_field";
const {Component, useState} = owl;

export class ChooseIcon extends Component {
    setup() {
        super.setup();
        this.state = useState({value: null});
    }

    get IconsDefault() {
        return ["cubes", "diamond", "bell", "calendar", "circle", "cube",
            "flag", "folder-open", "home", "rocket", "sitemap", "area-chart", "balance-scale",
            "database", "globe", "institution", "random", "umbrella", "bed", "bolt", "commenting",
            "envelope", "flask", "magic", "pie-chart", "retweet", "shopping-basket", "star", "television", "tree",
            "thumbs-o-up", "file-o", "wheelchair", "code", "spinner", "ticket", "shield", "recycle", "phone",
            "microphone", "magnet", "info", "inbox", "heart", "bullseye", "cutlery", "credit-card", "briefcase"]
    }
}

ChooseIcon.template = "dynamic_odoo.ChooseIconWidget";
ChooseIcon.components = {CharField};
