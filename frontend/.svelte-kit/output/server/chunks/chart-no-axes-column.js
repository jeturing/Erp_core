import { h as sanitize_props, i as spread_props, j as slot } from "./index2.js";
import { I as Icon } from "./Icon.js";
function Chart_no_axes_column($$renderer, $$props) {
  const $$sanitized_props = sanitize_props($$props);
  const iconNode = [
    ["path", { "d": "M5 21v-6" }],
    ["path", { "d": "M12 21V3" }],
    ["path", { "d": "M19 21V9" }]
  ];
  Icon($$renderer, spread_props([
    { name: "chart-no-axes-column" },
    $$sanitized_props,
    {
      /**
       * @component @name ChartNoAxesColumn
       * @description Lucide SVG icon component, renders SVG Element with children.
       *
       * @preview ![img](data:image/svg+xml;base64,PHN2ZyAgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIgogIHdpZHRoPSIyNCIKICBoZWlnaHQ9IjI0IgogIHZpZXdCb3g9IjAgMCAyNCAyNCIKICBmaWxsPSJub25lIgogIHN0cm9rZT0iIzAwMCIgc3R5bGU9ImJhY2tncm91bmQtY29sb3I6ICNmZmY7IGJvcmRlci1yYWRpdXM6IDJweCIKICBzdHJva2Utd2lkdGg9IjIiCiAgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIgogIHN0cm9rZS1saW5lam9pbj0icm91bmQiCj4KICA8cGF0aCBkPSJNNSAyMXYtNiIgLz4KICA8cGF0aCBkPSJNMTIgMjFWMyIgLz4KICA8cGF0aCBkPSJNMTkgMjFWOSIgLz4KPC9zdmc+Cg==) - https://lucide.dev/icons/chart-no-axes-column
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
  Chart_no_axes_column as C
};
