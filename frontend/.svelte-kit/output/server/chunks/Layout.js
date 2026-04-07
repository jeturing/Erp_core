import { h as sanitize_props, i as spread_props, j as slot, k as attr_class, e as ensure_array_like, b as stringify, c as attr, d as escape_html, l as clsx, s as store_get, u as unsubscribe_stores } from "./index2.js";
import { a as auth, h as darkMode } from "./darkMode.js";
import "./toast.js";
import "@sveltejs/kit/internal";
import "./exports.js";
import "./utils.js";
import "@sveltejs/kit/internal/server";
import "./root.js";
import "./state.svelte.js";
import { I as Icon } from "./Icon.js";
import { U as Users } from "./users.js";
import { G as Globe } from "./globe.js";
import { S as Server } from "./server.js";
import { A as Arrow_right_left } from "./arrow-right-left.js";
import { H as Handshake } from "./handshake.js";
import { T as Target } from "./target.js";
import { F as File_spreadsheet } from "./file-spreadsheet.js";
import { S as Shopping_bag } from "./shopping-bag.js";
import { C as Credit_card } from "./credit-card.js";
import { P as Package } from "./package.js";
import { R as Receipt } from "./receipt.js";
import { S as Scale } from "./scale.js";
import { G as Git_compare_arrows, C as Clipboard_list } from "./git-compare-arrows.js";
import { G as Gauge } from "./gauge.js";
import { S as Shield_check } from "./shield-check.js";
import { B as Boxes } from "./boxes.js";
import { P as Percent } from "./percent.js";
import { P as Palette } from "./palette.js";
import { C as Chart_no_axes_column } from "./chart-no-axes-column.js";
import { M as Mail } from "./mail.js";
import { M as Message_circle } from "./message-circle.js";
import { L as Languages } from "./languages.js";
import { A as Activity } from "./activity.js";
import { S as Shield } from "./shield.js";
import { S as Settings } from "./settings.js";
import { Z as Zap } from "./zap.js";
import { F as File_text } from "./file-text.js";
import { K as Key } from "./key.js";
import { E as External_link } from "./external-link.js";
import { C as Chevron_down } from "./chevron-down.js";
import { L as Log_out } from "./log-out.js";
import { M as Menu } from "./menu.js";
function File_type($$renderer, $$props) {
  const $$sanitized_props = sanitize_props($$props);
  const iconNode = [
    [
      "path",
      {
        "d": "M6 22a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h8a2.4 2.4 0 0 1 1.704.706l3.588 3.588A2.4 2.4 0 0 1 20 8v12a2 2 0 0 1-2 2z"
      }
    ],
    ["path", { "d": "M14 2v5a1 1 0 0 0 1 1h5" }],
    ["path", { "d": "M11 18h2" }],
    ["path", { "d": "M12 12v6" }],
    [
      "path",
      { "d": "M9 13v-.5a.5.5 0 0 1 .5-.5h5a.5.5 0 0 1 .5.5v.5" }
    ]
  ];
  Icon($$renderer, spread_props([
    { name: "file-type" },
    $$sanitized_props,
    {
      /**
       * @component @name FileType
       * @description Lucide SVG icon component, renders SVG Element with children.
       *
       * @preview ![img](data:image/svg+xml;base64,PHN2ZyAgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIgogIHdpZHRoPSIyNCIKICBoZWlnaHQ9IjI0IgogIHZpZXdCb3g9IjAgMCAyNCAyNCIKICBmaWxsPSJub25lIgogIHN0cm9rZT0iIzAwMCIgc3R5bGU9ImJhY2tncm91bmQtY29sb3I6ICNmZmY7IGJvcmRlci1yYWRpdXM6IDJweCIKICBzdHJva2Utd2lkdGg9IjIiCiAgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIgogIHN0cm9rZS1saW5lam9pbj0icm91bmQiCj4KICA8cGF0aCBkPSJNNiAyMmEyIDIgMCAwIDEtMi0yVjRhMiAyIDAgMCAxIDItMmg4YTIuNCAyLjQgMCAwIDEgMS43MDQuNzA2bDMuNTg4IDMuNTg4QTIuNCAyLjQgMCAwIDEgMjAgOHYxMmEyIDIgMCAwIDEtMiAyeiIgLz4KICA8cGF0aCBkPSJNMTQgMnY1YTEgMSAwIDAgMCAxIDFoNSIgLz4KICA8cGF0aCBkPSJNMTEgMThoMiIgLz4KICA8cGF0aCBkPSJNMTIgMTJ2NiIgLz4KICA8cGF0aCBkPSJNOSAxM3YtLjVhLjUuNSAwIDAgMSAuNS0uNWg1YS41LjUgMCAwIDEgLjUuNXYuNSIgLz4KPC9zdmc+Cg==) - https://lucide.dev/icons/file-type
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
function Layout_dashboard($$renderer, $$props) {
  const $$sanitized_props = sanitize_props($$props);
  const iconNode = [
    [
      "rect",
      { "width": "7", "height": "9", "x": "3", "y": "3", "rx": "1" }
    ],
    [
      "rect",
      { "width": "7", "height": "5", "x": "14", "y": "3", "rx": "1" }
    ],
    [
      "rect",
      { "width": "7", "height": "9", "x": "14", "y": "12", "rx": "1" }
    ],
    [
      "rect",
      { "width": "7", "height": "5", "x": "3", "y": "16", "rx": "1" }
    ]
  ];
  Icon($$renderer, spread_props([
    { name: "layout-dashboard" },
    $$sanitized_props,
    {
      /**
       * @component @name LayoutDashboard
       * @description Lucide SVG icon component, renders SVG Element with children.
       *
       * @preview ![img](data:image/svg+xml;base64,PHN2ZyAgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIgogIHdpZHRoPSIyNCIKICBoZWlnaHQ9IjI0IgogIHZpZXdCb3g9IjAgMCAyNCAyNCIKICBmaWxsPSJub25lIgogIHN0cm9rZT0iIzAwMCIgc3R5bGU9ImJhY2tncm91bmQtY29sb3I6ICNmZmY7IGJvcmRlci1yYWRpdXM6IDJweCIKICBzdHJva2Utd2lkdGg9IjIiCiAgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIgogIHN0cm9rZS1saW5lam9pbj0icm91bmQiCj4KICA8cmVjdCB3aWR0aD0iNyIgaGVpZ2h0PSI5IiB4PSIzIiB5PSIzIiByeD0iMSIgLz4KICA8cmVjdCB3aWR0aD0iNyIgaGVpZ2h0PSI1IiB4PSIxNCIgeT0iMyIgcng9IjEiIC8+CiAgPHJlY3Qgd2lkdGg9IjciIGhlaWdodD0iOSIgeD0iMTQiIHk9IjEyIiByeD0iMSIgLz4KICA8cmVjdCB3aWR0aD0iNyIgaGVpZ2h0PSI1IiB4PSIzIiB5PSIxNiIgcng9IjEiIC8+Cjwvc3ZnPgo=) - https://lucide.dev/icons/layout-dashboard
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
function Moon($$renderer, $$props) {
  const $$sanitized_props = sanitize_props($$props);
  const iconNode = [
    [
      "path",
      {
        "d": "M20.985 12.486a9 9 0 1 1-9.473-9.472c.405-.022.617.46.402.803a6 6 0 0 0 8.268 8.268c.344-.215.825-.004.803.401"
      }
    ]
  ];
  Icon($$renderer, spread_props([
    { name: "moon" },
    $$sanitized_props,
    {
      /**
       * @component @name Moon
       * @description Lucide SVG icon component, renders SVG Element with children.
       *
       * @preview ![img](data:image/svg+xml;base64,PHN2ZyAgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIgogIHdpZHRoPSIyNCIKICBoZWlnaHQ9IjI0IgogIHZpZXdCb3g9IjAgMCAyNCAyNCIKICBmaWxsPSJub25lIgogIHN0cm9rZT0iIzAwMCIgc3R5bGU9ImJhY2tncm91bmQtY29sb3I6ICNmZmY7IGJvcmRlci1yYWRpdXM6IDJweCIKICBzdHJva2Utd2lkdGg9IjIiCiAgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIgogIHN0cm9rZS1saW5lam9pbj0icm91bmQiCj4KICA8cGF0aCBkPSJNMjAuOTg1IDEyLjQ4NmE5IDkgMCAxIDEtOS40NzMtOS40NzJjLjQwNS0uMDIyLjYxNy40Ni40MDIuODAzYTYgNiAwIDAgMCA4LjI2OCA4LjI2OGMuMzQ0LS4yMTUuODI1LS4wMDQuODAzLjQwMSIgLz4KPC9zdmc+Cg==) - https://lucide.dev/icons/moon
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
function Rocket($$renderer, $$props) {
  const $$sanitized_props = sanitize_props($$props);
  const iconNode = [
    [
      "path",
      {
        "d": "M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"
      }
    ],
    [
      "path",
      {
        "d": "m12 15-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"
      }
    ],
    ["path", { "d": "M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0" }],
    ["path", { "d": "M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5" }]
  ];
  Icon($$renderer, spread_props([
    { name: "rocket" },
    $$sanitized_props,
    {
      /**
       * @component @name Rocket
       * @description Lucide SVG icon component, renders SVG Element with children.
       *
       * @preview ![img](data:image/svg+xml;base64,PHN2ZyAgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIgogIHdpZHRoPSIyNCIKICBoZWlnaHQ9IjI0IgogIHZpZXdCb3g9IjAgMCAyNCAyNCIKICBmaWxsPSJub25lIgogIHN0cm9rZT0iIzAwMCIgc3R5bGU9ImJhY2tncm91bmQtY29sb3I6ICNmZmY7IGJvcmRlci1yYWRpdXM6IDJweCIKICBzdHJva2Utd2lkdGg9IjIiCiAgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIgogIHN0cm9rZS1saW5lam9pbj0icm91bmQiCj4KICA8cGF0aCBkPSJNNC41IDE2LjVjLTEuNSAxLjI2LTIgNS0yIDVzMy43NC0uNSA1LTJjLjcxLS44NC43LTIuMTMtLjA5LTIuOTFhMi4xOCAyLjE4IDAgMCAwLTIuOTEtLjA5eiIgLz4KICA8cGF0aCBkPSJtMTIgMTUtMy0zYTIyIDIyIDAgMCAxIDItMy45NUExMi44OCAxMi44OCAwIDAgMSAyMiAyYzAgMi43Mi0uNzggNy41LTYgMTFhMjIuMzUgMjIuMzUgMCAwIDEtNCAyeiIgLz4KICA8cGF0aCBkPSJNOSAxMkg0cy41NS0zLjAzIDItNGMxLjYyLTEuMDggNSAwIDUgMCIgLz4KICA8cGF0aCBkPSJNMTIgMTV2NXMzLjAzLS41NSA0LTJjMS4wOC0xLjYyIDAtNSAwLTUiIC8+Cjwvc3ZnPgo=) - https://lucide.dev/icons/rocket
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
function Route($$renderer, $$props) {
  const $$sanitized_props = sanitize_props($$props);
  const iconNode = [
    ["circle", { "cx": "6", "cy": "19", "r": "3" }],
    [
      "path",
      { "d": "M9 19h8.5a3.5 3.5 0 0 0 0-7h-11a3.5 3.5 0 0 1 0-7H15" }
    ],
    ["circle", { "cx": "18", "cy": "5", "r": "3" }]
  ];
  Icon($$renderer, spread_props([
    { name: "route" },
    $$sanitized_props,
    {
      /**
       * @component @name Route
       * @description Lucide SVG icon component, renders SVG Element with children.
       *
       * @preview ![img](data:image/svg+xml;base64,PHN2ZyAgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIgogIHdpZHRoPSIyNCIKICBoZWlnaHQ9IjI0IgogIHZpZXdCb3g9IjAgMCAyNCAyNCIKICBmaWxsPSJub25lIgogIHN0cm9rZT0iIzAwMCIgc3R5bGU9ImJhY2tncm91bmQtY29sb3I6ICNmZmY7IGJvcmRlci1yYWRpdXM6IDJweCIKICBzdHJva2Utd2lkdGg9IjIiCiAgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIgogIHN0cm9rZS1saW5lam9pbj0icm91bmQiCj4KICA8Y2lyY2xlIGN4PSI2IiBjeT0iMTkiIHI9IjMiIC8+CiAgPHBhdGggZD0iTTkgMTloOC41YTMuNSAzLjUgMCAwIDAgMC03aC0xMWEzLjUgMy41IDAgMCAxIDAtN0gxNSIgLz4KICA8Y2lyY2xlIGN4PSIxOCIgY3k9IjUiIHI9IjMiIC8+Cjwvc3ZnPgo=) - https://lucide.dev/icons/route
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
function Sliders_vertical($$renderer, $$props) {
  const $$sanitized_props = sanitize_props($$props);
  const iconNode = [
    ["path", { "d": "M10 8h4" }],
    ["path", { "d": "M12 21v-9" }],
    ["path", { "d": "M12 8V3" }],
    ["path", { "d": "M17 16h4" }],
    ["path", { "d": "M19 12V3" }],
    ["path", { "d": "M19 21v-5" }],
    ["path", { "d": "M3 14h4" }],
    ["path", { "d": "M5 10V3" }],
    ["path", { "d": "M5 21v-7" }]
  ];
  Icon($$renderer, spread_props([
    { name: "sliders-vertical" },
    $$sanitized_props,
    {
      /**
       * @component @name SlidersVertical
       * @description Lucide SVG icon component, renders SVG Element with children.
       *
       * @preview ![img](data:image/svg+xml;base64,PHN2ZyAgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIgogIHdpZHRoPSIyNCIKICBoZWlnaHQ9IjI0IgogIHZpZXdCb3g9IjAgMCAyNCAyNCIKICBmaWxsPSJub25lIgogIHN0cm9rZT0iIzAwMCIgc3R5bGU9ImJhY2tncm91bmQtY29sb3I6ICNmZmY7IGJvcmRlci1yYWRpdXM6IDJweCIKICBzdHJva2Utd2lkdGg9IjIiCiAgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIgogIHN0cm9rZS1saW5lam9pbj0icm91bmQiCj4KICA8cGF0aCBkPSJNMTAgOGg0IiAvPgogIDxwYXRoIGQ9Ik0xMiAyMXYtOSIgLz4KICA8cGF0aCBkPSJNMTIgOFYzIiAvPgogIDxwYXRoIGQ9Ik0xNyAxNmg0IiAvPgogIDxwYXRoIGQ9Ik0xOSAxMlYzIiAvPgogIDxwYXRoIGQ9Ik0xOSAyMXYtNSIgLz4KICA8cGF0aCBkPSJNMyAxNGg0IiAvPgogIDxwYXRoIGQ9Ik01IDEwVjMiIC8+CiAgPHBhdGggZD0iTTUgMjF2LTciIC8+Cjwvc3ZnPgo=) - https://lucide.dev/icons/sliders-vertical
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
function Sun($$renderer, $$props) {
  const $$sanitized_props = sanitize_props($$props);
  const iconNode = [
    ["circle", { "cx": "12", "cy": "12", "r": "4" }],
    ["path", { "d": "M12 2v2" }],
    ["path", { "d": "M12 20v2" }],
    ["path", { "d": "m4.93 4.93 1.41 1.41" }],
    ["path", { "d": "m17.66 17.66 1.41 1.41" }],
    ["path", { "d": "M2 12h2" }],
    ["path", { "d": "M20 12h2" }],
    ["path", { "d": "m6.34 17.66-1.41 1.41" }],
    ["path", { "d": "m19.07 4.93-1.41 1.41" }]
  ];
  Icon($$renderer, spread_props([
    { name: "sun" },
    $$sanitized_props,
    {
      /**
       * @component @name Sun
       * @description Lucide SVG icon component, renders SVG Element with children.
       *
       * @preview ![img](data:image/svg+xml;base64,PHN2ZyAgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIgogIHdpZHRoPSIyNCIKICBoZWlnaHQ9IjI0IgogIHZpZXdCb3g9IjAgMCAyNCAyNCIKICBmaWxsPSJub25lIgogIHN0cm9rZT0iIzAwMCIgc3R5bGU9ImJhY2tncm91bmQtY29sb3I6ICNmZmY7IGJvcmRlci1yYWRpdXM6IDJweCIKICBzdHJva2Utd2lkdGg9IjIiCiAgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIgogIHN0cm9rZS1saW5lam9pbj0icm91bmQiCj4KICA8Y2lyY2xlIGN4PSIxMiIgY3k9IjEyIiByPSI0IiAvPgogIDxwYXRoIGQ9Ik0xMiAydjIiIC8+CiAgPHBhdGggZD0iTTEyIDIwdjIiIC8+CiAgPHBhdGggZD0ibTQuOTMgNC45MyAxLjQxIDEuNDEiIC8+CiAgPHBhdGggZD0ibTE3LjY2IDE3LjY2IDEuNDEgMS40MSIgLz4KICA8cGF0aCBkPSJNMiAxMmgyIiAvPgogIDxwYXRoIGQ9Ik0yMCAxMmgyIiAvPgogIDxwYXRoIGQ9Im02LjM0IDE3LjY2LTEuNDEgMS40MSIgLz4KICA8cGF0aCBkPSJtMTkuMDcgNC45My0xLjQxIDEuNDEiIC8+Cjwvc3ZnPgo=) - https://lucide.dev/icons/sun
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
function User_check($$renderer, $$props) {
  const $$sanitized_props = sanitize_props($$props);
  const iconNode = [
    ["path", { "d": "m16 11 2 2 4-4" }],
    ["path", { "d": "M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" }],
    ["circle", { "cx": "9", "cy": "7", "r": "4" }]
  ];
  Icon($$renderer, spread_props([
    { name: "user-check" },
    $$sanitized_props,
    {
      /**
       * @component @name UserCheck
       * @description Lucide SVG icon component, renders SVG Element with children.
       *
       * @preview ![img](data:image/svg+xml;base64,PHN2ZyAgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIgogIHdpZHRoPSIyNCIKICBoZWlnaHQ9IjI0IgogIHZpZXdCb3g9IjAgMCAyNCAyNCIKICBmaWxsPSJub25lIgogIHN0cm9rZT0iIzAwMCIgc3R5bGU9ImJhY2tncm91bmQtY29sb3I6ICNmZmY7IGJvcmRlci1yYWRpdXM6IDJweCIKICBzdHJva2Utd2lkdGg9IjIiCiAgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIgogIHN0cm9rZS1saW5lam9pbj0icm91bmQiCj4KICA8cGF0aCBkPSJtMTYgMTEgMiAyIDQtNCIgLz4KICA8cGF0aCBkPSJNMTYgMjF2LTJhNCA0IDAgMCAwLTQtNEg2YTQgNCAwIDAgMC00IDR2MiIgLz4KICA8Y2lyY2xlIGN4PSI5IiBjeT0iNyIgcj0iNCIgLz4KPC9zdmc+Cg==) - https://lucide.dev/icons/user-check
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
function Users_round($$renderer, $$props) {
  const $$sanitized_props = sanitize_props($$props);
  const iconNode = [
    ["path", { "d": "M18 21a8 8 0 0 0-16 0" }],
    ["circle", { "cx": "10", "cy": "8", "r": "5" }],
    ["path", { "d": "M22 20c0-3.37-2-6.5-4-8a5 5 0 0 0-.45-8.3" }]
  ];
  Icon($$renderer, spread_props([
    { name: "users-round" },
    $$sanitized_props,
    {
      /**
       * @component @name UsersRound
       * @description Lucide SVG icon component, renders SVG Element with children.
       *
       * @preview ![img](data:image/svg+xml;base64,PHN2ZyAgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIgogIHdpZHRoPSIyNCIKICBoZWlnaHQ9IjI0IgogIHZpZXdCb3g9IjAgMCAyNCAyNCIKICBmaWxsPSJub25lIgogIHN0cm9rZT0iIzAwMCIgc3R5bGU9ImJhY2tncm91bmQtY29sb3I6ICNmZmY7IGJvcmRlci1yYWRpdXM6IDJweCIKICBzdHJva2Utd2lkdGg9IjIiCiAgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIgogIHN0cm9rZS1saW5lam9pbj0icm91bmQiCj4KICA8cGF0aCBkPSJNMTggMjFhOCA4IDAgMCAwLTE2IDAiIC8+CiAgPGNpcmNsZSBjeD0iMTAiIGN5PSI4IiByPSI1IiAvPgogIDxwYXRoIGQ9Ik0yMiAyMGMwLTMuMzctMi02LjUtNC04YTUgNSAwIDAgMC0uNDUtOC4zIiAvPgo8L3N2Zz4K) - https://lucide.dev/icons/users-round
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
function Layout($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    const { currentRoute = "dashboard", children } = $$props;
    function isGroup(entry) {
      return "children" in entry;
    }
    const navStructure = [
      {
        id: "dashboard",
        label: "Dashboard",
        icon: Layout_dashboard,
        href: "/dashboard"
      },
      {
        id: "grp-infra",
        label: "Infraestructura",
        icon: Server,
        children: [
          {
            id: "tenants",
            label: "Tenants",
            icon: Users,
            href: "/tenants"
          },
          {
            id: "domains",
            label: "Dominios",
            icon: Globe,
            href: "/domains"
          },
          {
            id: "infrastructure",
            label: "Servidores",
            icon: Server,
            href: "/infrastructure"
          },
          {
            id: "tunnels",
            label: "Tunnels",
            icon: Route,
            href: "/tunnels"
          },
          {
            id: "migrations",
            label: "Migraciones",
            icon: Arrow_right_left,
            href: "/migrations"
          }
        ]
      },
      {
        id: "grp-comercial",
        label: "Comercial",
        icon: Handshake,
        children: [
          {
            id: "partners",
            label: "Partners",
            icon: Handshake,
            href: "/partners"
          },
          { id: "leads", label: "Leads", icon: Target, href: "/leads" },
          {
            id: "clients",
            label: "Clientes",
            icon: User_check,
            href: "/clients"
          },
          {
            id: "quotations",
            label: "Cotizaciones",
            icon: File_spreadsheet,
            href: "/quotations"
          },
          {
            id: "catalog",
            label: "Catálogo",
            icon: Shopping_bag,
            href: "/catalog"
          }
        ]
      },
      {
        id: "grp-billing",
        label: "Facturación",
        icon: Credit_card,
        children: [
          {
            id: "billing",
            label: "Billing",
            icon: Credit_card,
            href: "/billing"
          },
          { id: "plans", label: "Planes", icon: Package, href: "/plans" },
          {
            id: "invoices",
            label: "Facturas",
            icon: Receipt,
            href: "/invoices"
          },
          {
            id: "seats",
            label: "Seats",
            icon: Users_round,
            href: "/seats"
          },
          {
            id: "settlements",
            label: "Liquidaciones",
            icon: Scale,
            href: "/settlements"
          },
          {
            id: "reconciliation",
            label: "Conciliación",
            icon: Git_compare_arrows,
            href: "/reconciliation"
          },
          {
            id: "dispersion",
            label: "Dispersión",
            icon: Arrow_right_left,
            href: "/dispersion"
          },
          { id: "quotas", label: "Quotas", icon: Gauge, href: "/quotas" },
          {
            id: "plan-governance",
            label: "Gobernanza",
            icon: Shield_check,
            href: "/plan-governance"
          }
        ]
      },
      {
        id: "grp-ops",
        label: "Operaciones",
        icon: Clipboard_list,
        children: [
          {
            id: "workorders",
            label: "Work Orders",
            icon: Clipboard_list,
            href: "/workorders"
          },
          {
            id: "blueprints",
            label: "Blueprints",
            icon: Boxes,
            href: "/blueprints"
          },
          {
            id: "commissions",
            label: "Comisiones",
            icon: Percent,
            href: "/commissions"
          },
          {
            id: "branding",
            label: "Branding",
            icon: Palette,
            href: "/branding"
          }
        ]
      },
      {
        id: "grp-analytics",
        label: "Análisis",
        icon: Chart_no_axes_column,
        children: [
          {
            id: "reports",
            label: "Reportes",
            icon: Chart_no_axes_column,
            href: "/reports"
          },
          {
            id: "communications",
            label: "Comunicaciones",
            icon: Mail,
            href: "/communications"
          }
        ]
      },
      {
        id: "grp-landing",
        label: "Landing / i18n",
        icon: Languages,
        children: [
          {
            id: "testimonials",
            label: "Testimonios",
            icon: Message_circle,
            href: "/testimonials"
          },
          {
            id: "landing-sections",
            label: "Secciones Landing",
            icon: File_type,
            href: "/landing-sections"
          },
          {
            id: "translations",
            label: "Traducciones",
            icon: Languages,
            href: "/translations"
          }
        ]
      },
      {
        id: "grp-security",
        label: "Seguridad",
        icon: Shield,
        children: [
          {
            id: "session-monitoring",
            label: "DSAM Monitor",
            icon: Activity,
            href: "/session-monitoring"
          }
        ]
      },
      {
        id: "grp-admin",
        label: "Administración",
        icon: Settings,
        children: [
          {
            id: "settings",
            label: "Settings",
            icon: Settings,
            href: "/settings"
          },
          {
            id: "onboarding-config",
            label: "Config. Onboarding",
            icon: Sliders_vertical,
            href: "/onboarding-config"
          },
          {
            id: "neural-users",
            label: "Neural Users ✨",
            icon: Zap,
            href: "/neural-users"
          },
          { id: "roles", label: "Roles", icon: Shield, href: "/roles" },
          {
            id: "admin-users",
            label: "Usuarios Admin",
            icon: Users_round,
            href: "/admin-users"
          },
          {
            id: "agreements",
            label: "Acuerdos",
            icon: File_text,
            href: "/agreements"
          },
          {
            id: "developer-portal",
            label: "Developer Portal",
            icon: Rocket,
            href: "/developer-portal"
          },
          {
            id: "api-keys",
            label: "API Keys",
            icon: Key,
            href: "/api-keys"
          },
          {
            id: "stripe-connect",
            label: "Stripe Connect",
            icon: Credit_card,
            href: "/stripe-connect"
          },
          {
            id: "audit",
            label: "Auditoría",
            icon: Shield_check,
            href: "/audit"
          },
          { id: "logs", label: "Logs", icon: File_text, href: "/logs" },
          {
            id: "portal",
            label: "Portal Tenant",
            icon: External_link,
            href: "/portal"
          }
        ]
      }
    ];
    const allNavItems = navStructure.flatMap((e) => isGroup(e) ? e.children : [e]);
    function findGroupForRoute(route) {
      for (const entry of navStructure) {
        if (isGroup(entry) && entry.children.some((c) => c.id === route)) return entry.id;
      }
      return null;
    }
    let expandedGroups = /* @__PURE__ */ new Set();
    function initExpandedGroups() {
      try {
        const saved = localStorage.getItem("sidebar_expanded");
        if (saved) expandedGroups = new Set(JSON.parse(saved));
      } catch {
      }
      const activeGroup = findGroupForRoute(currentRoute);
      if (activeGroup) expandedGroups.add(activeGroup);
      expandedGroups = new Set(expandedGroups);
    }
    initExpandedGroups();
    function groupHasActive(group) {
      return group.children.some((c) => c.id === currentRoute);
    }
    $$renderer2.push(`<div class="min-h-screen flex bg-bg-page">`);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> <aside${attr_class(
      `fixed lg:static inset-y-0 left-0 z-50 w-64 bg-charcoal flex flex-col transition-transform duration-300 ${"-translate-x-full lg:translate-x-0"}`,
      "svelte-qgpshq"
    )}><div class="flex items-center gap-3 px-6 py-6 border-b border-border-dark"><div class="w-8 h-8 bg-terracotta flex items-center justify-center flex-shrink-0"><span class="text-text-light font-bold font-sans text-sm">S</span></div> <span class="font-sans font-bold text-text-light tracking-wide text-sm uppercase">Sajet ERP</span></div> <nav class="flex-1 px-3 pt-2 overflow-y-auto sidebar-nav svelte-qgpshq"><!--[-->`);
    const each_array = ensure_array_like(navStructure);
    for (let $$index_1 = 0, $$length = each_array.length; $$index_1 < $$length; $$index_1++) {
      let entry = each_array[$$index_1];
      if (isGroup(entry)) {
        $$renderer2.push("<!--[-->");
        const GroupIcon = entry.icon;
        $$renderer2.push(`<button type="button"${attr_class(`sidebar-group-toggle ${stringify(groupHasActive(entry) ? "sidebar-group-active" : "")}`, "svelte-qgpshq")}${attr("aria-expanded", expandedGroups.has(entry.id))}><div class="flex items-center gap-2.5 min-w-0">`);
        if (GroupIcon) {
          $$renderer2.push("<!--[-->");
          GroupIcon($$renderer2, { size: 16, class: "shrink-0 opacity-60" });
          $$renderer2.push("<!--]-->");
        } else {
          $$renderer2.push("<!--[!-->");
          $$renderer2.push("<!--]-->");
        }
        $$renderer2.push(` <span class="truncate">${escape_html(entry.label)}</span></div> <div class="flex items-center gap-1.5">`);
        if (!expandedGroups.has(entry.id)) {
          $$renderer2.push("<!--[-->");
          $$renderer2.push(`<span class="sidebar-group-badge svelte-qgpshq">${escape_html(entry.children.length)}</span>`);
        } else {
          $$renderer2.push("<!--[!-->");
        }
        $$renderer2.push(`<!--]--> `);
        Chevron_down($$renderer2, {
          size: 14,
          class: `shrink-0 transition-transform duration-200 ${stringify(expandedGroups.has(entry.id) ? "rotate-180" : "")}`
        });
        $$renderer2.push(`<!----></div></button> `);
        if (expandedGroups.has(entry.id)) {
          $$renderer2.push("<!--[-->");
          $$renderer2.push(`<div class="sidebar-group-children svelte-qgpshq"><!--[-->`);
          const each_array_1 = ensure_array_like(entry.children);
          for (let $$index = 0, $$length2 = each_array_1.length; $$index < $$length2; $$index++) {
            let item = each_array_1[$$index];
            const ItemIcon = item.icon;
            $$renderer2.push(`<a${attr("href", item.href)}${attr_class(clsx(currentRoute === item.id ? "sidebar-child-active" : "sidebar-child"), "svelte-qgpshq")}>`);
            if (ItemIcon) {
              $$renderer2.push("<!--[-->");
              ItemIcon($$renderer2, { size: 15 });
              $$renderer2.push("<!--]-->");
            } else {
              $$renderer2.push("<!--[!-->");
              $$renderer2.push("<!--]-->");
            }
            $$renderer2.push(` <span>${escape_html(item.label)}</span></a>`);
          }
          $$renderer2.push(`<!--]--></div>`);
        } else {
          $$renderer2.push("<!--[!-->");
        }
        $$renderer2.push(`<!--]-->`);
      } else {
        $$renderer2.push("<!--[!-->");
        const DirectIcon = entry.icon;
        $$renderer2.push(`<a${attr("href", entry.href)}${attr_class(`sidebar-direct-link ${stringify(currentRoute === entry.id ? "sidebar-direct-active" : "")}`, "svelte-qgpshq")}>`);
        if (DirectIcon) {
          $$renderer2.push("<!--[-->");
          DirectIcon($$renderer2, { size: 18 });
          $$renderer2.push("<!--]-->");
        } else {
          $$renderer2.push("<!--[!-->");
          $$renderer2.push("<!--]-->");
        }
        $$renderer2.push(` <span>${escape_html(entry.label)}</span></a>`);
      }
      $$renderer2.push(`<!--]-->`);
    }
    $$renderer2.push(`<!--]--></nav> <div class="px-4 py-4 border-t border-border-dark"><div class="flex items-center justify-between gap-3"><div class="flex items-center gap-3 min-w-0"><div class="w-8 h-8 rounded-full bg-dark-subtle flex items-center justify-center flex-shrink-0"><span class="text-gray-400 font-sans font-semibold text-xs">${escape_html(store_get($$store_subs ??= {}, "$auth", auth).user?.username?.charAt(0).toUpperCase() || "U")}</span></div> <div class="min-w-0"><p class="text-sm font-semibold font-sans text-text-light truncate">${escape_html(store_get($$store_subs ??= {}, "$auth", auth).user?.username || "Admin")}</p> <p class="text-[11px] text-gray-500 truncate font-body">${escape_html(store_get($$store_subs ??= {}, "$auth", auth).user?.email || "")}</p></div></div> <button type="button" class="p-1.5 text-gray-500 hover:text-error transition-colors flex-shrink-0" title="Cerrar sesión" aria-label="Cerrar sesión">`);
    Log_out($$renderer2, { size: 16 });
    $$renderer2.push(`<!----></button></div></div></aside> <div class="flex-1 flex flex-col min-w-0"><header class="h-16 bg-charcoal border-b border-border-dark flex items-center px-6 gap-4"><button type="button" class="lg:hidden p-2 text-gray-400 hover:text-text-light" aria-label="Menú">`);
    {
      $$renderer2.push("<!--[!-->");
      Menu($$renderer2, { size: 22 });
    }
    $$renderer2.push(`<!--]--></button> <span class="hidden lg:block text-[11px] font-semibold uppercase tracking-widest text-gray-500 font-sans">${escape_html(allNavItems.find((n) => n.id === currentRoute)?.label ?? currentRoute)}</span> <div class="ml-auto flex items-center gap-4"><a href="/docs" target="_blank" rel="noreferrer" class="hidden sm:block text-[11px] uppercase tracking-widest text-gray-500 hover:text-text-light font-sans transition-colors">API Docs</a> <button type="button" class="p-2 rounded-md text-gray-400 hover:text-text-light hover:bg-white/10 transition-colors"${attr("title", store_get($$store_subs ??= {}, "$darkMode", darkMode) ? "Cambiar a modo claro" : "Cambiar a modo oscuro")} aria-label="Toggle dark mode">`);
    if (store_get($$store_subs ??= {}, "$darkMode", darkMode)) {
      $$renderer2.push("<!--[-->");
      Sun($$renderer2, { size: 16 });
    } else {
      $$renderer2.push("<!--[!-->");
      Moon($$renderer2, { size: 16 });
    }
    $$renderer2.push(`<!--]--></button> <a href="/portal" class="btn-accent btn-sm">Portal</a></div></header> <main class="flex-1 overflow-auto bg-bg-page">`);
    children?.($$renderer2);
    $$renderer2.push(`<!----></main></div></div>`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
export {
  Layout as L
};
