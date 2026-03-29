import { h as sanitize_props, i as spread_props, j as slot } from "./index2.js";
import { I as Icon } from "./Icon.js";
function Shopping_bag($$renderer, $$props) {
  const $$sanitized_props = sanitize_props($$props);
  const iconNode = [
    ["path", { "d": "M16 10a4 4 0 0 1-8 0" }],
    ["path", { "d": "M3.103 6.034h17.794" }],
    [
      "path",
      {
        "d": "M3.4 5.467a2 2 0 0 0-.4 1.2V20a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6.667a2 2 0 0 0-.4-1.2l-2-2.667A2 2 0 0 0 17 2H7a2 2 0 0 0-1.6.8z"
      }
    ]
  ];
  Icon($$renderer, spread_props([
    { name: "shopping-bag" },
    $$sanitized_props,
    {
      /**
       * @component @name ShoppingBag
       * @description Lucide SVG icon component, renders SVG Element with children.
       *
       * @preview ![img](data:image/svg+xml;base64,PHN2ZyAgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIgogIHdpZHRoPSIyNCIKICBoZWlnaHQ9IjI0IgogIHZpZXdCb3g9IjAgMCAyNCAyNCIKICBmaWxsPSJub25lIgogIHN0cm9rZT0iIzAwMCIgc3R5bGU9ImJhY2tncm91bmQtY29sb3I6ICNmZmY7IGJvcmRlci1yYWRpdXM6IDJweCIKICBzdHJva2Utd2lkdGg9IjIiCiAgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIgogIHN0cm9rZS1saW5lam9pbj0icm91bmQiCj4KICA8cGF0aCBkPSJNMTYgMTBhNCA0IDAgMCAxLTggMCIgLz4KICA8cGF0aCBkPSJNMy4xMDMgNi4wMzRoMTcuNzk0IiAvPgogIDxwYXRoIGQ9Ik0zLjQgNS40NjdhMiAyIDAgMCAwLS40IDEuMlYyMGEyIDIgMCAwIDAgMiAyaDE0YTIgMiAwIDAgMCAyLTJWNi42NjdhMiAyIDAgMCAwLS40LTEuMmwtMi0yLjY2N0EyIDIgMCAwIDAgMTcgMkg3YTIgMiAwIDAgMC0xLjYuOHoiIC8+Cjwvc3ZnPgo=) - https://lucide.dev/icons/shopping-bag
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
  Shopping_bag as S
};
