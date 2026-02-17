/** @odoo-module **/
import {xmlToJson, getTemplate} from "@dynamic_odoo/core/utils/view";

export const useSortService = (container, params = {}) => {
    const SORT_COM_CLASS = ".SORT_COMPONENT", HELPER_CLASS = ".helper-div", ITEM_SORT = "item_sort",
        D_NONE_CLASS = "d-none";
    const {stopSort} = params;
    const POSITION = {after: "after", before: "before", append: "append"}, NODE_ID = "node-id";

    const getNodeId = (el) => {
        return el.closest("[" + NODE_ID + "]").attr(NODE_ID);
    }
    const isDragCom = (el) => {
        return el.hasClass("drag_com");
    }
    const removeHelper = () => {
        container.find(HELPER_CLASS).remove();
    }
    const getComponent = (el) => el.data("component") || el.parents(SORT_COM_CLASS).data("component");
    const getSortParams = (component) => component ? (component.constructor['sortParams'] || {}) : {};

    const sortComponents = container.find(SORT_COM_CLASS).map((idx, el) => getComponent($(el))).toArray();
    const setReplaceTemplate = (ui, replaceTemplate, replaceClass) => {
        if (replaceTemplate) {
            ui.placeholder.addClass(replaceClass || "").html(getTemplate(replaceTemplate));
        } else {
            ui.placeholder.append(ui.item.children().clone());
        }
    }
    const prepareParams = () => {
        const onSort = (event, ui) => {
        };
        const onStart = (event, ui) => {
            if (isDragCom(ui.placeholder)) {
                ui.placeholder.addClass(D_NONE_CLASS);
            }
        };
        const onStop = (event, ui, stopParams = {}) => {
            const {item} = ui, parent = item.parent();
            if (parent.hasClass(SORT_COM_CLASS.substr(1))) {
                return removeHelper();
            }
            const component = getComponent(item), {
                replaceTemplate, nodeTemplate, isNew, useHelper
            } = getSortParams(component);
            const getParamsXpath = (currentEl) => {
                let params = currentEl.data("xpathParams") || {}, elXpath = currentEl.prev("[" + NODE_ID + "]");
                if (Object.keys(params).length) {
                    return params;
                }
                params.position = POSITION.after;
                if (!elXpath.length) {
                    elXpath = currentEl.next("[" + NODE_ID + "]");
                    params.position = POSITION.before;
                    if (!elXpath.length) {
                        // elXpath = currentEl.closest("[" + NODE_ID + "]["+NODE_ID+"!=]");
                        elXpath = currentEl.closest(`[${NODE_ID}][${NODE_ID}!=${currentEl.attr(NODE_ID)}]`);
                        params.position = POSITION.append;
                    }
                }
                params.nodeXpath = elXpath.attr(NODE_ID);
                return params;
            }
            const appendReplaceTemplate = (replaceTemplate, nodeTemplate) => {
                const getHTMLString = (_template) => {
                    return (typeof _template) == 'function' ? _template({el: ui.item[0], ...component.props}) : getTemplate(_template);
                }
                const xmlNodeTemplate = getHTMLString(nodeTemplate);
                const newNode = (typeof xmlNodeTemplate) == 'string' ? xmlToJson((new DOMParser()).parseFromString(xmlNodeTemplate.trim(), "text/xml")) : xmlNodeTemplate;

                let elCheck = item.closest(useHelper ? HELPER_CLASS : ".ui-sortable-handle");
                if (replaceTemplate) {
                    const _htmlString = getHTMLString(replaceTemplate);
                    useHelper ? elCheck.after(_htmlString) : ui.item.html(_htmlString);
                }
                newNode.parentId = elCheck.closest("[" + NODE_ID + "]").attr(NODE_ID)
                return {node: newNode, params: getParamsXpath(elCheck)}
            }
            const {
                node, params
            } = (component && isNew) ? appendReplaceTemplate(replaceTemplate, nodeTemplate) : {
                params: getParamsXpath(item), node: getNodeId(item)
            }
            removeHelper();
            if (stopSort) {
                stopSort(stopParams.nodeMoves || node, stopParams.params || params, isNew);
            }
        };
        const onChange = (event, ui) => {
            const {replaceTemplate, replaceClass} = getSortParams(getComponent(ui.item));
            const replaceHtml = replaceTemplate ? getTemplate(replaceTemplate) : ui.item.children().clone();
            ui.placeholder.removeClass(D_NONE_CLASS);
            ui.placeholder.addClass(replaceClass || "").html(replaceHtml);
        };
        const onBeforeStop = (event, ui) => {
        };
        const onActivate = (event, ui) => {
        };
        const runAction = (event, ui, baseFnc, kind) => {
            const lifecycle = getSortParams(getComponent(ui.item) || params.component).lifecycle || {};
            const extendFnc = (lifecycle || {})[kind];
            extendFnc ? extendFnc(event, ui, baseFnc, {...params, getComponent}) : baseFnc(event, ui);
        }
        return {
            tolerance: "pointer",
            delay: 30,
            sort: function (event, ui) {
                runAction(event, ui, onSort, "sort");
            }, start: function (event, ui) {
                ui.item.addClass(ITEM_SORT);
                runAction(event, ui, onStart, "start");
            }, stop: function (event, ui) {
                ui.item.removeClass(ITEM_SORT)
                runAction(event, ui, onStop, "stop");
            }, change: function (event, ui) {
                runAction(event, ui, onChange, "change");
            }, beforeStop: function (event, ui) {
                runAction(event, ui, onBeforeStop, "beforeStop");
            }, activate: function (event, ui) {
                runAction(event, ui, onActivate, "activate");
            }
        }
    }
    const sortParams = prepareParams(), bindSort = (components, sortParams, filter = (com) => com) => {
        components.filter(filter).map((component) => {
            const {selector, withoutSelector, params, useHelper} = getSortParams(component);
            (Array.isArray(selector) ? selector : [selector]).map((sl) => {
                container.find(SORT_COM_CLASS + "[key='" + component.key + "']," + (useHelper ? HELPER_CLASS : sl)).sortable({
                    connectWith: useHelper ? HELPER_CLASS : sl,
                    items: ` > *:not(.disable-sort-item${withoutSelector ? `, ${withoutSelector}` : ""})`, ...sortParams, ...params,
                }).disableSelection();
            });
        });
    }

    const bindHelper = (components) => {
        let hasActive = false;
        components.map((component) => {
            const {useHelper, helperClass, selector} = getSortParams(component);
            if (useHelper) {
                let isDrag = false;
                const mouseLeave = () => {
                    if (!isDrag && !hasActive) {
                        removeHelper();
                    }
                }
                const mouseEnter = () => {
                    if (!isDrag && !hasActive) {
                        removeHelper();
                        container.find(selector).map((i, e) => {
                            const $e = $(e), child = $e.children();
                            const helperDiv = (nodeId, position = POSITION.after) => $(`<div></div>`)
                                .addClass(helperClass ? `helper-div ${helperClass}` : "helper-div")
                                .data("xpathParams", {
                                    nodeXpath: nodeId, position: position
                                });

                            if (!child.length) {
                                $e.append(helperDiv(getNodeId($e), POSITION.append));
                            }
                            child.map((i, _e) => {
                                $(_e).after(helperDiv(getNodeId($(_e))));
                            });
                        });
                        bindSort([component], sortParams);
                    }
                }
                const mouseDown = () => {
                    isDrag = true;
                    hasActive = true;
                }
                const mouseUp = () => {
                    isDrag = false;
                    hasActive = false;
                }
                $(component.el).mouseleave(mouseLeave).mouseenter(mouseEnter).mousedown(mouseDown).mouseup(mouseUp);
            }
        });
    }
    bindSort(sortComponents, sortParams, (com) => !com.useHelper);
    bindHelper(sortComponents);
}
