/** @odoo-module **/


const {Component, onWillStart, useState, onWillUpdateProps} = owl;

export class Bookmarks extends Component {

    setup() {
        super.setup();
        this.state = useState({bookmarks: []});
        onWillStart(() => {
            this.prepareState();
        })
        onWillUpdateProps(async (nextProps) => {
            this.prepareState(nextProps);
        });
    }

    prepareState(props = this.props) {
        const {viewInfo} = props, {archJson} = viewInfo, bookmarks = [];
        archJson.children.map((bookmark) => {
            if (bookmark.tag == "bookmark") {
                const link = document.createElement("a");
                link.href = bookmark.attrs.link;
                bookmarks.push({
                    link: bookmark.attrs.link,
                    host: `www.${link.hostname}`,
                    nodeId: bookmark.nodeId,
                    icon: `https://t0.gstatic.com/faviconV2?client=SOCIAL&type=FAVICON&fallback_opts=TYPE,SIZE,URL&url=https://${link.hostname}&size=50`
                });
            }
        });
        this.state.bookmarks = bookmarks;
    }
}

Bookmarks.template = "dynamic_odoo.Bookmarks";

