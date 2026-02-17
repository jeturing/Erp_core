/** @odoo-module **/
import {templates} from "@web/core/assets";

export const getTemplate = (template) => {
    if (template.includes("<")) {
        return template;
    }
    if (typeof template == "function") {
        return template();
    }
    return templates.firstChild.querySelector("[t-name='" + template + "']").innerHTML.trim();
}

export function jsonNodeToXml(node, human_readable, indent) {
    // For debugging purpose, this function will convert a json node back to xml
    indent = indent || 0;
    let sIndent = (human_readable ? (new Array(indent + 1).join('\t')) : ''),
        r = sIndent + '<' + node.tag,
        cr = human_readable ? '\n' : '';

    if (typeof (node) === 'string') {
        return sIndent + node.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    } else if (typeof (node.tag) !== 'string' || node.children && !(node.children instanceof Array) || node.attrs && !(node.attrs instanceof Object)) {
        throw new Error("Node " + JSON.stringify(node) + " is not a JSONified XML node");
    }
    for (let attr in node.attrs) {
        let vAttr = node.attrs[attr];
        if (typeof (vAttr) !== 'string') {
            // domains, ...
            vAttr = JSON.stringify(vAttr);
        }
        vAttr = vAttr.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
        if (human_readable) {
            vAttr = vAttr.replace(/&quot;/g, "'");
        }
        r += ' ' + attr + '="' + vAttr + '"';
    }
    if (node.children && node.children.length) {
        r += '>' + cr;
        let childS = [];
        for (let i = 0, ii = node.children.length; i < ii; i++) {
            childS.push(jsonNodeToXml(node.children[i], human_readable, indent + 1));
        }
        r += childS.join(cr);
        r += cr + sIndent + '</' + node.tag + '>';
        return r;
    } else {
        return r + '/>';
    }
}

export function xmlToJson(node, strip_whitespace = true) {
    const nodeType = node.nodeType;
    switch (nodeType) {
        case 9:
            return xmlToJson(node.documentElement, strip_whitespace);
        case 3:
        case 4:
            return (strip_whitespace && node.data.trim() === '') ? undefined : node.data;
        case 1:
            let attrs = $(node).getAttributes();
            return {
                tag: node.tagName.toLowerCase(),
                attrs: attrs,
                // children: _.compact(_.map(node.childNodes, function (node) {
                //     return xmlToJson(node, strip_whitespace);
                // })),
                children: [...node.childNodes].map((node) => xmlToJson(node, strip_whitespace)).filter((node) => node),
            };
    }
}

export function stringToXml(stringXMl) {
    const parser = new DOMParser();
    return parser.parseFromString(stringXMl, "text/xml");
}

export function stringToJson(stringXMl, strip_whitespace=true) {
    return xmlToJson(stringToXml(stringXMl), strip_whitespace)
}

export function xmlToString(node) {
    let str = "";
    if (window.XMLSerializer) {
        str = (new XMLSerializer()).serializeToString(node);
    } else if (window.ActiveXObject) {
        str = node.xml;
    } else {
        throw new Error(_t("Could not serialize XML"));
    }
    const void_elements = 'area base br col command embed hr img input keygen link meta param source track wbr'.split(' ');
    str = str.replace(/<([a-z]+)([^<>]*)\s*\/\s*>/g, function (match, tag, attrs) {
        if (void_elements.indexOf(tag) < 0) {
            return "<" + tag + attrs + "></" + tag + ">";
        } else {
            return match;
        }
    });
    return str;
}

export function jsonNodeToString(json) {
    const parser = new DOMParser();
    return xmlToString(parser.parseFromString(jsonNodeToXml(json), "text/xml"))
}