import "clsx";
import { k as attr_class, d as escape_html, e as ensure_array_like } from "../../../../chunks/index2.js";
import { o as onDestroy } from "../../../../chunks/index-server.js";
import "../../../../chunks/client.js";
import "../../../../chunks/toast.js";
import { S as Shield } from "../../../../chunks/shield.js";
import { R as Refresh_cw } from "../../../../chunks/refresh-cw.js";
import { P as Play } from "../../../../chunks/play.js";
import { A as Activity } from "../../../../chunks/activity.js";
import { Z as Zap } from "../../../../chunks/zap.js";
import { U as Users } from "../../../../chunks/users.js";
import { G as Globe } from "../../../../chunks/globe.js";
import { T as Triangle_alert } from "../../../../chunks/triangle-alert.js";
import { S as Search } from "../../../../chunks/search.js";
function SessionMonitoring($$renderer, $$props) {
  $$renderer.component(($$renderer2) => {
    let activeTab = "dashboard";
    let autoRefresh = false;
    onDestroy(() => {
    });
    $$renderer2.push(`<div class="dsam-container svelte-1ii1qns"><div class="dsam-header svelte-1ii1qns"><div><h1 class="page-title">`);
    Shield($$renderer2, { class: "inline w-7 h-7 mr-2", style: "color: #00FF9F" });
    $$renderer2.push(`<!----> DSAM — Session Monitor</h1> <p class="page-subtitle">Dynamic Session &amp; Anti-Theft Monitor</p></div> <div class="dsam-header-actions svelte-1ii1qns"><button class="btn-sm btn-accent" title="Sync Redis → BD">`);
    Refresh_cw($$renderer2, { class: "w-4 h-4" });
    $$renderer2.push(`<!----> Sync</button> <button class="btn-sm btn-secondary" title="Ejecutar scan completo">`);
    Play($$renderer2, { class: "w-4 h-4" });
    $$renderer2.push(`<!----> Scan</button> <button${attr_class("btn-sm", void 0, { "btn-accent": autoRefresh, "btn-secondary": !autoRefresh })}>`);
    Activity($$renderer2, { class: "w-4 h-4" });
    $$renderer2.push(`<!----> ${escape_html("Auto OFF")}</button></div></div> <div class="dsam-tabs svelte-1ii1qns"><!--[-->`);
    const each_array = ensure_array_like([
      { key: "dashboard", label: "Dashboard", icon: Zap },
      { key: "sessions", label: "Sesiones", icon: Users },
      { key: "geo", label: "Geo Mapa", icon: Globe },
      { key: "rules", label: "Reglas", icon: Shield },
      { key: "playbook", label: "Playbook", icon: Triangle_alert },
      { key: "audit", label: "Auditoría", icon: Search }
    ]);
    for (let $$index = 0, $$length = each_array.length; $$index < $$length; $$index++) {
      let tab = each_array[$$index];
      const IconComp = tab.icon;
      $$renderer2.push(`<button${attr_class("dsam-tab svelte-1ii1qns", void 0, { "active": activeTab === tab.key })}>`);
      if (IconComp) {
        $$renderer2.push("<!--[-->");
        IconComp($$renderer2, { class: "w-4 h-4" });
        $$renderer2.push("<!--]-->");
      } else {
        $$renderer2.push("<!--[!-->");
        $$renderer2.push("<!--]-->");
      }
      $$renderer2.push(` ${escape_html(tab.label)}</button>`);
    }
    $$renderer2.push(`<!--]--></div> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--> `);
    {
      $$renderer2.push("<!--[!-->");
    }
    $$renderer2.push(`<!--]--></div>`);
  });
}
function _page($$renderer) {
  SessionMonitoring($$renderer);
}
export {
  _page as default
};
