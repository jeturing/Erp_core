/** @odoo-module **/

const {onWillUnmount, useEffect, useComponent} = owl;

export const studioListener = (name, callback = () => {
}, element = document) => {
    element.addEventListener(name, callback);
    onWillUnmount(() => {
        element.removeEventListener(name, callback);
    });
}

export const dispatchEvent = (name, params = {}, element = document.body) => {
    element.dispatchEvent(new CustomEvent(name, {bubbles: true, detail: params}));
}

export const addEvent = (name, callback = () => {
}, element = document) => {
    element.addEventListener(name, callback);
}
export const destroyEvent = (name, callback = () => {
}, element = document) => {
    element.removeEventListener(name, callback);
}