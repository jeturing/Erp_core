import { h as sanitize_props, i as spread_props, j as slot } from "./index2.js";
import { I as Icon } from "./Icon.js";
function Percent($$renderer, $$props) {
  const $$sanitized_props = sanitize_props($$props);
  const iconNode = [
    ["line", { "x1": "19", "x2": "5", "y1": "5", "y2": "19" }],
    ["circle", { "cx": "6.5", "cy": "6.5", "r": "2.5" }],
    ["circle", { "cx": "17.5", "cy": "17.5", "r": "2.5" }]
  ];
  Icon($$renderer, spread_props([
    { name: "percent" },
    $$sanitized_props,
    {
      /**
       * @component @name Percent
       * @description Lucide SVG icon component, renders SVG Element with children.
       *
       * @preview ![img](data:image/svg+xml;base64,PHN2ZyAgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIgogIHdpZHRoPSIyNCIKICBoZWlnaHQ9IjI0IgogIHZpZXdCb3g9IjAgMCAyNCAyNCIKICBmaWxsPSJub25lIgogIHN0cm9rZT0iIzAwMCIgc3R5bGU9ImJhY2tncm91bmQtY29sb3I6ICNmZmY7IGJvcmRlci1yYWRpdXM6IDJweCIKICBzdHJva2Utd2lkdGg9IjIiCiAgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIgogIHN0cm9rZS1saW5lam9pbj0icm91bmQiCj4KICA8bGluZSB4MT0iMTkiIHgyPSI1IiB5MT0iNSIgeTI9IjE5IiAvPgogIDxjaXJjbGUgY3g9IjYuNSIgY3k9IjYuNSIgcj0iMi41IiAvPgogIDxjaXJjbGUgY3g9IjE3LjUiIGN5PSIxNy41IiByPSIyLjUiIC8+Cjwvc3ZnPgo=) - https://lucide.dev/icons/percent
       * @see https://lucide.dev/guide/packages/lucide-svelte - Documentation
       *
       * @param {Object} props - Lucide icons props and any valid SVG attribute
       * @returns {FunctionalComponent} Svelte component
       *
       */
      iconNode,
      children: ($$renderer2) => {
        $$renderer2.push(`<!--[-->`);
        slot($$renderer2, $$props, "default", {});
        $$renderer2.push(`<!--]-->`);
      },
      $$slots: { default: true }
    }
  ]));
}
export {
  Percent as P
};
