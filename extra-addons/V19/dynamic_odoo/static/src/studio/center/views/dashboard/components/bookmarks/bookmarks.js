/** @odoo-module **/

import {CharField} from "@dynamic_odoo/core/fields/char_field/char_field";
import {NodeModifier, ComponentModifier} from "@dynamic_odoo/studio/center/modifier";
import {DashboardWidgets} from "@dynamic_odoo/base/views/dashboard/components/components";

const {useEffect} = owl;

class StudioBookmarks extends DashboardWidgets.bookmarks.component {
    onCreate(val) {
        this.env.bus.trigger("BOOKMARKS:UPDATE", {fncName: "newBookmark", params: [val]});
    }
}

StudioBookmarks.template = "dynamic_odoo.StudioBookmarks";
StudioBookmarks.components = {InputAdd: CharField};


const PROPS = {
    link: {
        type: String, optional: true
    }
}

class ExtendNodeModifier extends NodeModifier {
}

ExtendNodeModifier.nodeProps = {
    ...NodeModifier.nodeProps, ...PROPS
}

ExtendNodeModifier.nodeViewStore = [...NodeModifier.nodeViewStore, ["[bookmark]", ["link", "more"]], ["[bookmarks]", []]]

export class BookmarksModifier extends ComponentModifier {
    setup() {
        super.setup();
        const doSomething = (payload) => {
            const {fncName, params} = payload.detail;
            this[fncName](...params);
        }
        useEffect(() => {
            this.env.bus.addEventListener("BOOKMARKS:UPDATE", doSomething);
            return () => {
                this.env.bus.removeEventListener("BOOKMARKS:UPDATE", doSomething);
            }
        });
    }

    newBookmark(link) {
        const {archJson} = this.props.viewInfo;
        const bookmark = {attrs: {link: link}, tag: "bookmark", children: [], parentId: archJson.nodeId};
        this.setNodeId(bookmark);
        archJson.children.push(bookmark);
        this.state.node = bookmark;
    }
}

BookmarksModifier.showNodeRoot = true;
BookmarksModifier.NodeModifier = ExtendNodeModifier;
BookmarksModifier.ArchTemplate = "dynamic_odoo.Bookmarks.Layout_1";
BookmarksModifier.components = {
    ...ComponentModifier.components, ViewComponent: StudioBookmarks,
};
