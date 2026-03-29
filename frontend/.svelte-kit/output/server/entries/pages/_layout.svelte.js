import "clsx";
import { e as ensure_array_like, s as store_get, a as attr_style, b as stringify, c as attr, d as escape_html, u as unsubscribe_stores } from "../../chunks/index2.js";
import { t as toasts } from "../../chunks/toast.js";
import { S as Spinner } from "../../chunks/Spinner.js";
import { o as onDestroy } from "../../chunks/index-server.js";
import { W as Wifi_off, a as Wifi } from "../../chunks/wifi.js";
import "../../chunks/darkMode.js";
function Toast($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    var $$store_subs;
    const ICONS = {
      success: ["M20 6 9 17l-5-5"],
      error: ["M18 6 6 18", "M6 6 12 12"],
      warning: ["M12 9v4", "M12 17h.01"],
      info: ["M12 16v-4", "M12 8h.01"]
    };
    const ICON_CIRCLE = { success: false, error: false, warning: true, info: true };
    const STATE_COLORS = {
      success: "oklch(0.723 0.219 142.136)",
      error: "oklch(0.637 0.237 25.331)",
      warning: "oklch(0.795 0.184 86.047)",
      info: "oklch(0.685 0.169 237.323)"
    };
    const FILLS = {
      success: "#152b1e",
      error: "#2b1519",
      warning: "#2b2615",
      info: "#151d2b"
    };
    const LABELS = {
      success: "Éxito",
      error: "Error",
      warning: "Aviso",
      info: "Info"
    };
    const W = 350;
    const H = 40;
    const R = 18;
    let swipeY = {};
    $$renderer2.push(`<div class="sileo-viewport svelte-1cpok13"><!--[-->`);
    const each_array = ensure_array_like(store_get($$store_subs ??= {}, "$toasts", toasts));
    for (let $$index_1 = 0, $$length = each_array.length; $$index_1 < $$length; $$index_1++) {
      let toast = each_array[$$index_1];
      const c = STATE_COLORS[toast.variant];
      const fill = FILLS[toast.variant];
      const paths = ICONS[toast.variant];
      const circle = ICON_CIRCLE[toast.variant];
      $$renderer2.push(`<div class="sileo-toast svelte-1cpok13" role="alert"${attr_style(`--_tone:${stringify(c)}; --_tone-bg:color-mix(in oklch,${stringify(c)} 20%,transparent); transform:translateY(${stringify(swipeY[toast.id] ?? 0)}px)`)}><svg class="sileo-svg svelte-1cpok13"${attr("width", W)}${attr("height", H)}${attr("viewBox", `0 0 ${stringify(W)} ${stringify(H)}`)}><defs><filter${attr("id", `goo-${stringify(toast.id)}`)} x="-20%" y="-20%" width="140%" height="140%" color-interpolation-filters="sRGB"><feGaussianBlur in="SourceGraphic" stdDeviation="9" result="b"></feGaussianBlur><feColorMatrix in="b" type="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 20 -10" result="g"></feColorMatrix><feComposite in="SourceGraphic" in2="g" operator="atop"></feComposite></filter></defs><g${attr("filter", `url(#goo-${stringify(toast.id)})`)}><rect x="0" y="0"${attr("width", W)}${attr("height", H)}${attr("rx", R)}${attr("ry", R)}${attr("fill", fill)}></rect></g></svg> <div class="sileo-header svelte-1cpok13"><div class="sileo-badge svelte-1cpok13"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">`);
      if (circle) {
        $$renderer2.push("<!--[-->");
        $$renderer2.push(`<circle cx="12" cy="12" r="10"></circle>`);
      } else {
        $$renderer2.push("<!--[!-->");
      }
      $$renderer2.push(`<!--]--><!--[-->`);
      const each_array_1 = ensure_array_like(paths);
      for (let $$index = 0, $$length2 = each_array_1.length; $$index < $$length2; $$index++) {
        let d = each_array_1[$$index];
        $$renderer2.push(`<path${attr("d", d)}></path>`);
      }
      $$renderer2.push(`<!--]--></svg></div> <span class="sileo-label svelte-1cpok13">${escape_html(LABELS[toast.variant])}</span> <span class="sileo-msg svelte-1cpok13">${escape_html(toast.message)}</span> <button type="button" class="sileo-x svelte-1cpok13" aria-label="Cerrar"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"></path><path d="M6 6 12 12"></path></svg></button></div></div>`);
    }
    $$renderer2.push(`<!--]--></div>`);
    if ($$store_subs) unsubscribe_stores($$store_subs);
  });
}
function OfflineBanner($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let isOnline = true;
    let showReconnected = false;
    let reconnectedTimer;
    function update() {
      const wasOffline = !isOnline;
      isOnline = navigator.onLine;
      if (wasOffline && isOnline) {
        showReconnected = true;
        reconnectedTimer = setTimeout(
          () => {
            showReconnected = false;
          },
          3e3
        );
      }
    }
    onDestroy(() => {
      window.removeEventListener("online", update);
      window.removeEventListener("offline", update);
      clearTimeout(reconnectedTimer);
    });
    if (!isOnline) {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="fixed top-0 left-0 right-0 z-[9999] flex items-center justify-center gap-2 bg-amber-600 text-white px-4 py-2 text-sm font-medium shadow-lg" role="alert" aria-live="polite">`);
      Wifi_off($$renderer2, { class: "w-4 h-4 shrink-0" });
      $$renderer2.push(`<!----> <span>Sin conexión — mostrando datos en caché (solo lectura)</span></div> <div class="h-9" aria-hidden="true"></div>`);
    } else if (showReconnected) {
      $$renderer2.push("<!--[1-->");
      $$renderer2.push(`<div class="fixed top-4 right-4 z-[9999] flex items-center gap-2 bg-emerald-700 text-white px-4 py-2.5 rounded-lg shadow-lg text-sm font-medium animate-[fadeIn_0.2s_ease-out]" role="status">`);
      Wifi($$renderer2, { class: "w-4 h-4 shrink-0 text-emerald-300" });
      $$renderer2.push(`<!----> Conexión restaurada</div>`);
    } else {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]-->`);
  });
}
function _layout($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let { children } = $$props;
    Toast($$renderer2);
    $$renderer2.push(`<!----> `);
    OfflineBanner($$renderer2);
    $$renderer2.push(`<!----> `);
    {
      $$renderer2.push("<!--[-->");
      $$renderer2.push(`<div class="min-h-screen bg-bg-page flex items-center justify-center"><div class="text-center">`);
      Spinner($$renderer2, { size: "lg" });
      $$renderer2.push(`<!----> <p class="mt-4 text-gray-500">Cargando...</p></div></div>`);
    }
    $$renderer2.push(`<!--]-->`);
  });
}
export {
  _layout as default
};
