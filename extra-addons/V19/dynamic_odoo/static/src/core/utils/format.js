/** @odoo-module **/

export const formatNumber = (num) => Math.abs(num) > 999 ? Math.sign(num) * ((Math.abs(num) / 1000).toFixed(1)) + 'k' : Math.sign(num) * Math.abs(num);
export const roundNumber = (monetary) => Math.round((monetary + Number.EPSILON) * 100) / 100;
export const floorRandom = () => Math.floor(Math.random() * 1000000000).toString();
export const hexToRGB = (hex, opacity) => {
    const _hex = hex.replace('#', '');
    const r = parseInt(_hex.substring(0, 2), 16), g = parseInt(_hex.substring(2, 4), 16),
        b = parseInt(_hex.substring(4, 6), 16), result = 'rgba(' + r + ',' + g + ',' + b + ',' + opacity / 100 + ')';
    return result;
}


export const rgbToHex = (color) => {
    const _rgba = color.replace(/^rgba?\(|\s+|\)$/g, '').split(',');
    return `#${((1 << 24) + (parseInt(_rgba[0]) << 16) + (parseInt(_rgba[1]) << 8) + parseInt(_rgba[2])).toString(16).slice(1)}`;
}